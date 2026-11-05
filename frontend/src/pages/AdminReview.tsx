import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { statusLabel } from "../booking";
import { formatEuro } from "../money";
import { CsvButton } from "./CsvButton";

type Row = {
  booking_id: number;
  first_name: string;
  last_name: string;
  email: string;
  personal_code: string;
  status: string;
  amount_due_cents: number;
  paid_cents: number;
  balance_cents: number;
  reason: string;
  reason_label: string;
};

export function AdminReview() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Row[]>("/api/admin/views/payments-review")
      .then(setRows)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide">
      <h1>Pagamenti da verificare</h1>
      <p>
        Le iscrizioni che chiedono un&apos;occhiata sui soldi. Escono da qui da sole quando il
        problema è risolto.
      </p>
      {failed && <p role="alert">Non riesco a caricare la vista.</p>}
      {rows === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : rows.length === 0 ? (
        <p>Tutto in ordine: nessun pagamento da verificare.</p>
      ) : (
        <>
          <p aria-live="polite">{rows.length} da verificare</p>
          <p>
            <CsvButton path="/api/admin/views/payments-review" />
          </p>
          <div className="table-wrap">
            <table>
              <caption>Iscrizioni da verificare</caption>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Motivo</th>
                  <th scope="col">Stato</th>
                  <th scope="col">Dovuto</th>
                  <th scope="col">Versato</th>
                  <th scope="col">Saldo</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.booking_id}>
                    <th scope="row">
                      <Link to={`/admin/iscrizioni/${row.booking_id}`}>
                        {row.first_name} {row.last_name}
                      </Link>
                      <br />
                      <small>{row.personal_code}</small>
                    </th>
                    <td>{row.reason_label}</td>
                    <td>{statusLabel(row.status)}</td>
                    <td>{formatEuro(row.amount_due_cents)}</td>
                    <td>{formatEuro(row.paid_cents)}</td>
                    <td>{formatEuro(row.balance_cents)}</td>
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
