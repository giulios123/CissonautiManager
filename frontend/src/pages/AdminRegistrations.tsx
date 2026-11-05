import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";
import { formatDeadline, statusLabel } from "../booking";
import { formatEuro } from "../money";
import { CsvButton } from "./CsvButton";

type Row = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  personal_code: string;
  days: number;
  evenings: number;
  status: string;
  amount_due_cents: number;
  paid_cents: number;
  balance_cents: number;
  hold_expires_at: string;
};

const STATUSES = [
  "in_attesa_pagamento",
  "confermata",
  "scaduta",
  "disdetta_richiesta",
  "rimborsata",
];

function filterParams(status: string, query: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (query.trim()) params.set("q", query.trim());
  return params;
}

export function AdminRegistrations() {
  const notice = (useLocation().state as { notice?: string } | null)?.notice;
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    api<Row[]>(`/api/admin/registrations?${filterParams(status, query)}`)
      .then((loaded) => {
        if (!cancelled) {
          setRows(loaded);
          setFailed(false);
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [status, query]);

  return (
    <main className="wide">
      <h1>Persone</h1>
      {notice && (
        <p role="status" className="notice ok">
          {notice}
        </p>
      )}
      <div className="row filters">
        <label>
          Cerca per nome, email o codice
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <label>
          Stato
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Tutti</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {failed && <p role="alert">Non riesco a caricare le iscrizioni.</p>}
      {rows === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : rows.length === 0 ? (
        <p>Nessuna iscrizione trovata.</p>
      ) : (
        <>
          <p aria-live="polite">{rows.length} iscrizioni</p>
          <p>
            <CsvButton path="/api/admin/registrations" params={filterParams(status, query)} />
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Telefono</th>
                  <th scope="col">Codice</th>
                  <th scope="col">Giorni</th>
                  <th scope="col">Sere</th>
                  <th scope="col">Stato</th>
                  <th scope="col">Dovuto</th>
                  <th scope="col">Versato</th>
                  <th scope="col">Saldo</th>
                  <th scope="col">Scadenza</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <th scope="row">
                      <Link to={`/admin/iscrizioni/${row.id}`}>
                        {row.first_name} {row.last_name}
                      </Link>
                      <br />
                      <small>{row.email}</small>
                    </th>
                    <td>{row.phone ?? "-"}</td>
                    <td>{row.personal_code}</td>
                    <td>{row.days}</td>
                    <td>{row.evenings}</td>
                    <td>{statusLabel(row.status)}</td>
                    <td>{formatEuro(row.amount_due_cents)}</td>
                    <td>{formatEuro(row.paid_cents)}</td>
                    <td>{formatEuro(row.balance_cents)}</td>
                    <td>
                      {row.status === "in_attesa_pagamento"
                        ? formatDeadline(row.hold_expires_at)
                        : "-"}
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
