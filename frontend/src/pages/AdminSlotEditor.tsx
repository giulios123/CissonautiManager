import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import type { PickerDay } from "../daySelection";
import { formatEuro } from "../money";
import { DayPicker } from "./DayPicker";
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

  const pickerDays: PickerDay[] = days.map((day) => ({
    date: day.date,
    slots: day.slots.map((slot) => {
      const full = slot.free !== null && slot.free < 1;
      return {
        id: slot.id,
        period: slot.period,
        start_time: slot.start_time,
        end_time: slot.end_time,
        full,
        disabled: full && !mine.has(slot.id) && !selected.has(slot.id) && !force,
        hint:
          slot.capacity === null
            ? `${slot.present} presenti, senza limite`
            : `${slot.present}/${slot.capacity} presenti${full ? ", completo" : ""}`,
      };
    }),
  }));

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
      <DayPicker days={pickerDays} selected={selected} onChange={setSelected} />
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <button type="submit">Salva gli slot</button>
    </form>
  );
}
