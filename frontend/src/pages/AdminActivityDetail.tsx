import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { CsvButton } from "./CsvButton";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  status: string;
};
type Detail = Activity & { people: Person[] };

export function AdminActivityDetail() {
  const { id } = useParams();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Detail>(`/api/admin/activities/${id}`)
      .then(setDetail)
      .catch(() => setFailed(true));
  }, [id]);

  if (failed) return <main role="alert">Attività non trovata.</main>;
  if (!detail) return <main aria-busy="true">Caricamento…</main>;

  return (
    <main className="wide">
      <p>
        <Link to="/admin/activities">← Tutte le attività</Link>
      </p>
      <h1>{detail.title}</h1>
      <p>
        {formatDay(detail.date)}, {periodLabel(detail.period).toLowerCase()}
        {detail.time_label && ` (${detail.time_label})`} · {priceLabel(detail.price_cents)} ·{" "}
        {seatsLabel(detail)}
        {detail.free !== null && `, ${detail.free} posti liberi`}
      </p>
      {detail.description && <p>{detail.description}</p>}
      {detail.people.length === 0 ? (
        <p>Nessun iscritto per ora.</p>
      ) : (
        <>
          <p>
            <CsvButton path={`/api/admin/activities/${detail.id}`} />
          </p>
          <div className="table-wrap">
            <table>
              <caption>Iscritti</caption>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Telefono</th>
                  <th scope="col">Stato</th>
                </tr>
              </thead>
              <tbody>
                {detail.people.map((person) => (
                  <tr key={person.booking_id}>
                    <th scope="row">
                      <Link to={`/admin/registrations/${person.booking_id}`}>
                        {person.first_name} {person.last_name}
                      </Link>
                      <br />
                      <small>{person.email}</small>
                    </th>
                    <td>{person.phone ?? "-"}</td>
                    <td>
                      <StatusBadge status={person.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
