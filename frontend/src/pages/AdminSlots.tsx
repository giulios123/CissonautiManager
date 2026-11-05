import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatDay, hhmm, periodLabel, statusLabel } from "../booking";
import { CsvButton } from "./CsvButton";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  status: string;
  derived: boolean;
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
};
type DayRow = { date: string; slots: SlotRow[] };

export function AdminSlots() {
  const [days, setDays] = useState<DayRow[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<{ days: DayRow[] }>("/api/admin/views/slots")
      .then((data) => setDays(data.days))
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide">
      <h1>Giorni e slot</h1>
      <p>
        Chi c&apos;è in ogni slot. La sera comprende anche chi ha prenotato mattina e pomeriggio
        dello stesso giorno (segnato come «sera dell&apos;intero giorno»).
      </p>
      {failed && <p role="alert">Non riesco a caricare la vista.</p>}
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
                                  {statusLabel(person.status)}
                                  {person.derived && ", sera dell'intero giorno"}
                                </small>
                              </li>
                            ))}
                          </ul>
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
