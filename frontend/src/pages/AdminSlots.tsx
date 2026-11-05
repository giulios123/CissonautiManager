import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDay, hhmm, periodLabel } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { CsvButton } from "./CsvButton";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  status: string;
  derived: boolean;
};
type Waiting = {
  entry_id: number;
  position: number;
  first_name: string;
  last_name: string;
  email: string;
};
type SlotRow = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number | null;
  present: number;
  free: number | null;
  people: Person[];
  waitlist?: Waiting[];
};
type DayRow = { date: string; slots: SlotRow[] };

export function AdminSlots() {
  const [days, setDays] = useState<DayRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(
    () =>
      api<{ days: DayRow[] }>("/api/admin/views/slots")
        .then((data) => setDays(data.days))
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  async function remove(person: Waiting) {
    setMessage(null);
    try {
      await api(`/api/admin/waitlist/${person.entry_id}`, { method: "DELETE" });
      setMessage({
        ok: true,
        text: `${person.first_name} ${person.last_name} è stato tolto dalla lista. Non parte nessuna email: avvisalo tu.`,
      });
      await load();
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : "Riprova tra poco.",
      });
    }
  }

  return (
    <main className="wide">
      <h1>Giorni e slot</h1>
      <p>
        Chi c&apos;è in ogni slot. La sera comprende anche chi ha prenotato mattina e pomeriggio
        dello stesso giorno (segnato come «sera dell&apos;intero giorno»).
      </p>
      {failed && <p role="alert">Non riesco a caricare la vista.</p>}
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`notice ${message.ok ? "ok" : "error"}`}
        >
          {message.text}
        </p>
      )}
      {days === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : days.length === 0 ? (
        <p>Nessun giorno: configura prima l&apos;edizione nelle Impostazioni.</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/slots" />
          </p>
          {days.map((day) => (
            <div className="table-wrap" key={day.date}>
              <table>
                <caption>{formatDay(day.date)}</caption>
                <thead>
                  <tr>
                    <th scope="col">Slot</th>
                    <th scope="col">Presenti</th>
                    <th scope="col">Posti liberi</th>
                    <th scope="col">Persone</th>
                    <th scope="col">Lista d&apos;attesa</th>
                  </tr>
                </thead>
                <tbody>
                  {day.slots.map((slot) => (
                    <tr key={slot.id}>
                      <th scope="row">
                        {periodLabel(slot.period)}
                        <br />
                        <small>
                          {hhmm(slot.start_time)}-{hhmm(slot.end_time)}
                        </small>
                      </th>
                      <td>
                        {slot.present}
                        {slot.capacity !== null && ` / ${slot.capacity}`}
                      </td>
                      <td>{slot.free === null ? "senza limite" : slot.free}</td>
                      <td>
                        {slot.people.length === 0 ? (
                          "-"
                        ) : (
                          <ul className="plain">
                            {slot.people.map((person) => (
                              <li key={person.booking_id}>
                                <Link to={`/admin/iscrizioni/${person.booking_id}`}>
                                  {person.first_name} {person.last_name}
                                </Link>{" "}
                                <small>
                                  <StatusBadge status={person.status} />
                                  {person.derived && ", sera dell'intero giorno"}
                                </small>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                      <td>
                        {(slot.waitlist ?? []).length === 0 ? (
                          "-"
                        ) : (
                          <ol className="plain">
                            {(slot.waitlist ?? []).map((person) => (
                              <li key={person.entry_id} className="item">
                                <span>
                                  {person.position}. {person.first_name} {person.last_name}
                                </span>
                                <button
                                  type="button"
                                  className="secondary"
                                  onClick={() => remove(person)}
                                  aria-label={`Togli ${person.first_name} ${person.last_name} dalla lista`}
                                >
                                  Togli
                                </button>
                              </li>
                            ))}
                          </ol>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </>
      )}
    </main>
  );
}
