import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { formatDay, hhmm, periodLabel } from "../booking";
import { formatEuro } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

type SlotRow = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number | null;
  present: number;
  free: number | null;
};
type DayRow = { date: string; slots: SlotRow[] };

/** Admins can pick any slot, past days included. A full slot needs "Forza oltre la capienza". */
export function AdminSlotEditor({
  bookingId,
  booking,
  onDone,
}: {
  bookingId: number;
  booking: BookingView;
  onDone: (detail: Detail, text: string) => void;
}) {
  const mine = new Set(booking.slots.map((slot) => slot.id));
  const [days, setDays] = useState<DayRow[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set(mine));
  const [force, setForce] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<{ days: DayRow[] }>("/api/admin/views/slots")
      .then((data) => setDays(data.days))
      .catch(() => setLoadError(true));
  }, []);

  if (loadError) return <p role="alert">Non riesco a caricare gli slot.</p>;
  if (!days) return <p aria-busy="true">Caricamento…</p>;

  function toggle(id: number, checked: boolean) {
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
    try {
      const updated = await api<Detail>(`/api/admin/registrations/${bookingId}/slots`, {
        method: "PUT",
        json: { slot_ids: [...selected], force },
      });
      // Presences changed with this save: reload them so a slot just freed can be picked again.
      const fresh = await api<{ days: DayRow[] }>("/api/admin/views/slots").catch(() => null);
      if (fresh) setDays(fresh.days);
      onDone(
        updated,
        `Slot aggiornati. Nuova quota: ${formatEuro(updated.booking.amount_due_cents)}.`,
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    }
  }

  return (
    <form onSubmit={save} aria-label="Cambia gli slot">
      <label className="check">
        <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
        <span>Forza oltre la capienza (per aggiungere uno slot già pieno)</span>
      </label>
      {days.map((day) => (
        <fieldset key={day.date}>
          <legend>{formatDay(day.date)}</legend>
          {day.slots.map((slot) => {
            const full = slot.free !== null && slot.free < 1;
            const disabled = full && !mine.has(slot.id) && !selected.has(slot.id) && !force;
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
                  {slot.capacity === null
                    ? `${slot.present} presenti, senza limite`
                    : `${slot.present}/${slot.capacity} presenti${full ? ", completo" : ""}`}
                </span>
              </label>
            );
          })}
        </fieldset>
      ))}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <button type="submit">Salva gli slot</button>
    </form>
  );
}
