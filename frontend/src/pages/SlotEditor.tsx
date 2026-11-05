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

  if (loadError) return <p role="alert">Non riesco a caricare i giorni. Riprova tra poco.</p>;
  if (!edition) return <p aria-busy="true">Caricamento…</p>;

  const fee =
    feePreview(
      edition.days,
      selected,
      edition.base_fee_cents ?? 0,
      edition.per_day_fee_cents ?? 0,
    ) + (extras ? extrasPreview(edition.days, selected, extras) : 0);
  const delta = fee - booking.amount_due_cents;
  const changed = selected.size !== original.size || [...selected].some((id) => !original.has(id));

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    if (selected.size === 0) {
      setError("Scegli almeno uno slot. Per rinunciare usa la disdetta.");
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
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
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
          ? "giorno passato"
          : isFull(slot) && mine
            ? "il tuo posto"
            : canJoinWaitlist(slot)
              ? "completo, puoi metterti in lista d'attesa"
              : seatsLabel(slot),
      };
    }),
  }));

  return (
    <form onSubmit={save} aria-label="Modifica i tuoi slot">
      <DayPicker
        days={pickerDays}
        selected={selected}
        onChange={(next) => {
          setSaved(false);
          setSelected(next);
        }}
      />
      <p aria-live="polite" className="fee">
        Nuova quota: <strong>{formatEuro(fee)}</strong>
        {delta !== 0 && (
          <>
            {" "}
            ({formatEuro(Math.abs(delta))} {delta > 0 ? "in più" : "in meno"} di ora)
          </>
        )}
      </p>
      {booking.status === "in_attesa_pagamento" && (
        <p className="legal">La scadenza del blocco non cambia.</p>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          Slot aggiornati.
          {dropped.length > 0 &&
            ` Tolti anche pasti e attività dei momenti in cui non ci sei più: ${dropped.join(", ")}.`}
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        Salva gli slot
      </button>
    </form>
  );
}
