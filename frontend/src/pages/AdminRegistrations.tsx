import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";
import { formatDeadline, statusLabel } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { useI18n } from "../i18n";
import { formatEuro } from "../money";
import { adminRegistrationPath } from "../routes";
import { CsvButton } from "./CsvButton";

type Row = {
  // null for someone who is only on a waitlist and has no booking
  id: number | null;
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
  hold_expires_at: string | null;
  waitlist_slots?: number;
};

const STATUSES = [
  "in_attesa_pagamento",
  "confermata",
  "scaduta",
  "disdetta_richiesta",
  "rimborsata",
  "in_lista",
];

function filterParams(status: string, query: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (query.trim()) params.set("q", query.trim());
  return params;
}

export function AdminRegistrations() {
  const { t, tn } = useI18n();
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
      <h1>{t("people.title")}</h1>
      {notice && (
        <p role="status" className="notice ok">
          {notice}
        </p>
      )}
      <div className="row filters">
        <label>
          {t("people.search")}
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <label>
          {t("people.status")}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{t("adm.all")}</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {failed && <p role="alert">{t("people.loadError")}</p>}
      {rows === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : rows.length === 0 ? (
        <p>{t("people.none")}</p>
      ) : (
        <>
          <p aria-live="polite">{tn("people.count", rows.length)}</p>
          <p>
            <CsvButton path="/api/admin/registrations" params={filterParams(status, query)} />
          </p>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">{t("people.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("people.colPerson")}</th>
                  <th scope="col">{t("people.colPhone")}</th>
                  <th scope="col">{t("people.colCode")}</th>
                  <th scope="col">{t("people.colDays")}</th>
                  <th scope="col">{t("people.colEvenings")}</th>
                  <th scope="col">{t("people.colStatus")}</th>
                  <th scope="col">{t("people.colDue")}</th>
                  <th scope="col">{t("people.colPaid")}</th>
                  <th scope="col">{t("people.colBalance")}</th>
                  <th scope="col">{t("people.colDeadline")}</th>
                  <th scope="col">{t("people.colWaitlist")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id ?? `w-${row.personal_code}`}>
                    <th scope="row">
                      {row.id === null ? (
                        `${row.first_name} ${row.last_name}`
                      ) : (
                        <Link to={adminRegistrationPath(row.id)}>
                          {row.first_name} {row.last_name}
                        </Link>
                      )}
                      <br />
                      <small>{row.email}</small>
                    </th>
                    <td>{row.phone ?? "-"}</td>
                    <td>{row.personal_code}</td>
                    <td>{row.days}</td>
                    <td>{row.evenings}</td>
                    <td>
                      <StatusBadge status={row.status} />
                    </td>
                    <td>{formatEuro(row.amount_due_cents)}</td>
                    <td>{formatEuro(row.paid_cents)}</td>
                    <td>{formatEuro(row.balance_cents)}</td>
                    <td>
                      {row.status === "in_attesa_pagamento" && row.hold_expires_at
                        ? formatDeadline(row.hold_expires_at)
                        : "-"}
                    </td>
                    <td>
                      {row.waitlist_slots ? tn("people.waitlistSlots", row.waitlist_slots) : "-"}
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
