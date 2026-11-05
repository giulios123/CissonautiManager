import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import {
  canJoinWaitlist,
  feePreview,
  formatDay,
  hhmm,
  isFull,
  periodLabel,
  seatsLabel,
  type Day,
} from "../booking";
import { formatEuro } from "../money";

type PublicEdition = {
  base_fee_cents: number | null;
  per_day_fee_cents: number | null;
  days: Day[];
};

const fetchEdition = () => api<PublicEdition>("/api/public/edition");

export function SlotEditor({
  booking,
  onSaved,
}: {
  booking: BookingView;
  onSaved: () => Promise<void> | void;
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

  const fee = feePreview(
    edition.days,
    selected,
    edition.base_fee_cents ?? 0,
    edition.per_day_fee_cents ?? 0,
  );
  const delta = fee - booking.amount_due_cents;
  const changed = selected.size !== original.size || [...selected].some((id) => !original.has(id));

  function toggle(id: number, checked: boolean) {
    setSaved(false);
    setSelected((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

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
      setDropped(result.dropped_meals ?? []);
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

  return (
    <form onSubmit={save} aria-label="Modifica i tuoi slot">
      {edition.days.map((day) => (
        <fieldset key={day.date}>
          <legend>{formatDay(day.date)}</legend>
          {day.slots.map((slot) => {
            const mine = original.has(slot.id);
            const disabled = Boolean(day.past) || (isFull(slot) && !mine && !selected.has(slot.id));
            const hint = day.past
              ? "giorno passato"
              : isFull(slot) && mine
                ? "il tuo posto"
                : canJoinWaitlist(slot)
                  ? "completo, puoi metterti in lista d'attesa"
                  : seatsLabel(slot);
            return (
              <label className="check" key={slot.id}>
                <input
                  type="checkbox"
                  checked={selected.has(slot.id)}
                  disabled={disabled}
                  onChange={(e) => toggle(slot.id, e.target.checked)}
                />
                <span>
                  {periodLabel(slot.period)} {hhmm(slot.start_time)}-{hhmm(slot.end_time)}
                  {" · "}
                  {hint}
                </span>
              </label>
            );
          })}
        </fieldset>
      ))}
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
            ` Tolti anche i pasti in cui non ci sei più: ${dropped.join(", ")}.`}
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        Salva gli slot
      </button>
    </form>
  );
}
