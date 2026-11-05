import { useEffect, useState } from "react";
import { api } from "../api";
import { formatDay } from "../booking";
import { CsvButton } from "./CsvButton";

type DayRow = {
  date: string;
  morning: number;
  afternoon: number;
  evening: number;
  evening_derived: number;
  people: number;
};
type Week = { days: DayRow[]; total_people: number };

export function AdminWeek() {
  const [week, setWeek] = useState<Week | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Week>("/api/admin/views/week")
      .then(setWeek)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide">
      <h1>Settimana</h1>
      <p>
        Quante persone ci sono ogni giorno. La sera include chi ha prenotato l&apos;intero giorno.
      </p>
      {failed && <p role="alert">Non riesco a caricare la vista.</p>}
      {week === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : week.days.length === 0 ? (
        <p>Nessun giorno: configura prima l&apos;edizione nelle Impostazioni.</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/week" />
          </p>
          <div className="table-wrap">
            <table>
              <caption>Presenze per giorno</caption>
              <thead>
                <tr>
                  <th scope="col">Giorno</th>
                  <th scope="col">Mattina</th>
                  <th scope="col">Pomeriggio</th>
                  <th scope="col">Sera</th>
                  <th scope="col">Persone</th>
                </tr>
              </thead>
              <tbody>
                {week.days.map((day) => (
                  <tr key={day.date}>
                    <th scope="row">{formatDay(day.date)}</th>
                    <td>{day.morning}</td>
                    <td>{day.afternoon}</td>
                    <td>
                      {day.evening}
                      {day.evening_derived > 0 && (
                        <small> (di cui {day.evening_derived} per l&apos;intero giorno)</small>
                      )}
                    </td>
                    <td>{day.people}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colSpan={4}>
                    Persone diverse in tutta la settimana
                  </th>
                  <td>{week.total_people}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
