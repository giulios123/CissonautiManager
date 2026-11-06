import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { StatusBadge } from "../StatusBadge";
import { useT } from "../i18n";
import { formatEuro } from "../money";
import { adminRegistrationPath } from "../routes";
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
  const t = useT();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Row[]>("/api/admin/views/payments-review")
      .then(setRows)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide">
      <h1>{t("review.title")}</h1>
      <p>{t("review.intro")}</p>
      {failed && <p role="alert">{t("review.loadError")}</p>}
      {rows === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : rows.length === 0 ? (
        <p>{t("review.empty")}</p>
      ) : (
        <>
          <p aria-live="polite">{t("review.count", { n: rows.length })}</p>
          <p>
            <CsvButton path="/api/admin/views/payments-review" />
          </p>
          <div className="table-wrap">
            <table>
              <caption>{t("review.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("people.colPerson")}</th>
                  <th scope="col">{t("review.colReason")}</th>
                  <th scope="col">{t("people.colStatus")}</th>
                  <th scope="col">{t("people.colDue")}</th>
                  <th scope="col">{t("people.colPaid")}</th>
                  <th scope="col">{t("people.colBalance")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.booking_id}>
                    <th scope="row">
                      <Link to={adminRegistrationPath(row.booking_id)}>
                        {row.first_name} {row.last_name}
                      </Link>
                      <br />
                      <small>{row.personal_code}</small>
                    </th>
                    <td>{row.reason_label}</td>
                    <td>
                      <StatusBadge status={row.status} />
                    </td>
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
