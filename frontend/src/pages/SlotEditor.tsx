import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import {
  canJoinWaitlist,
  extrasPreview,
  feePreview,
  isFull,
  seatsLabel,
  type Day,
  type PricedExtras,
} from "../booking";
import type { PickerDay } from "../daySelection";
import { useT } from "../i18n";
import { formatEuro } from "../money";
import { DayPicker } from "./DayPicker";

type PublicEdition = {
  base_fee_cents: number | null;
  per_day_fee_cents: number | null;
  days: Day[];
};

const fetchEdition = () => api<PublicEdition>("/api/public/edition");

export function SlotEditor({
  booking,
  onSaved,
  extras,
}: {
  booking: BookingView;
  onSaved: () => Promise<void> | void;
  // Meals and activities of the booking, so the preview includes the ones that stay.
  extras?: PricedExtras;
}) {
  const t = useT();
  const original = new Set(booking.slots.map((slot) => slot.id));
  const [edition, setEdition] = useState<PublicEdition | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set(original));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dropped, setDropped] = useState<string[]>([]);

  useEffect(() => {
    fetchEdition()
      .then(setEdition)
      .catch(() => setLoadError(true));
  }, []);

  if (loadError) return <p role="alert">{t("edit.slotsLoadError")}</p>;
  if (!edition) return <p aria-busy="true">{t("common.loading")}</p>;

  const registrationFee = feePreview(
    edition.days,
    selected,
    edition.base_fee_cents ?? 0,
    edition.per_day_fee_cents ?? 0,
  );
  const fee = registrationFee + (extras ? extrasPreview(edition.days, selected, extras) : 0);
  const feePolicy = booking.confirmation_policy === "registration_fee";
  const delta = fee - booking.amount_due_cents;
  const changed = selected.size !== original.size || [...selected].some((id) => !original.has(id));

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    if (selected.size === 0) {
      setError(t("edit.chooseOne"));
      return;
    }
    setSaving(true);
    try {
      const result = await api<BookingView>("/api/me/booking/slots", {
        method: "PUT",
        json: { slot_ids: [...selected] },
      });
      setDropped([...(result.dropped_meals ?? []), ...(result.dropped_activities ?? [])]);
      await onSaved();
      // The seat I just freed (or took) changes what is available: show the current numbers.
      setEdition(await fetchEdition().catch(() => edition));
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
      // Seats may have changed while the page was open: show the current ones.
      setEdition(await fetchEdition().catch(() => edition));
    } finally {
      setSaving(false);
    }
  }

  const pickerDays: PickerDay[] = edition.days.map((day) => ({
    date: day.date,
    slots: day.slots.map((slot) => {
      const mine = original.has(slot.id);
      return {
        id: slot.id,
        period: slot.period,
        start_time: slot.start_time,
        end_time: slot.end_time,
        full: isFull(slot),
        disabled: Boolean(day.past) || (isFull(slot) && !mine && !selected.has(slot.id)),
        hint: day.past
          ? t("edit.pastDay")
          : isFull(slot) && mine
            ? t("edit.yourPlace")
            : canJoinWaitlist(slot)
              ? t("edit.fullJoinWaitlist")
              : seatsLabel(slot),
      };
    }),
  }));

  return (
    <form onSubmit={save} aria-label={t("edit.aria")}>
      <DayPicker
        days={pickerDays}
        selected={selected}
        onChange={(next) => {
          setSaved(false);
          setSelected(next);
        }}
      />
      <p aria-live="polite" className="fee">
        {feePolicy && (
          <>
            {t("edit.newRegistrationFee")} <strong>{formatEuro(registrationFee)}</strong>
            <br />
          </>
        )}
        {feePolicy ? t("edit.newTotal") : t("edit.newFee")} <strong>{formatEuro(fee)}</strong>
        {delta !== 0 && (
          <>
            {" "}
            {t(delta > 0 ? "edit.delta.more" : "edit.delta.less", {
              amount: formatEuro(Math.abs(delta)),
            })}
          </>
        )}
      </p>
      {booking.status === "in_attesa_pagamento" && (
        <p className="legal">{t("edit.holdUnchanged")}</p>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          {t("edit.slotsUpdated")}
          {dropped.length > 0 && ` ${t("edit.droppedAlso", { list: dropped.join(", ") })}`}
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        {t("edit.saveSlots")}
      </button>
    </form>
  );
}
