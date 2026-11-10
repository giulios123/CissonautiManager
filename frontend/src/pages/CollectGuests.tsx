import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { GuestItem } from "../guests";
import { useI18n } from "../i18n";
import { formatEuro } from "../money";
import { adminGuestPath } from "../routes";
import { GuestMovementDialog } from "./GuestMovementDialog";

type Row = {
  guest_id: number;
  first_name: string;
  last_name: string;
  reference: string | null;
  items: GuestItem[];
  due_cents: number;
  paid_cents: number;
  balance_cents: number;
};

/**
 * External guests who still have to pay, apart from the bookings above: their money sits in its
 * own register and no email goes out, so there is nothing to wait for or to undo here.
 */
export function CollectGuests() {
  const { t, locale } = useI18n();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [query, setQuery] = useState("");
  const [failed, setFailed] = useState(false);
  const [paying, setPaying] = useState<Row | null>(null);
  const [message, setMessage] = useState("");

  // Only the answer to the latest request counts: an older, slower one (a previous search, or
  // the list before a payment) must not put old rows back.
  const latest = useRef(0);
  const load = useCallback((search: string) => {
    const request = ++latest.current;
    return api<Row[]>(`/api/admin/guests/to-collect?q=${encodeURIComponent(search)}`)
      .then((loaded) => {
        if (request !== latest.current) return;
        if (!Array.isArray(loaded)) throw new Error("unexpected answer");
        setRows(loaded);
        setFailed(false);
      })
      .catch(() => {
        if (request === latest.current) setFailed(true);
      });
  }, []);
  // The item labels come from the server in the language of the request: a new language means
  // asking again (this page is not remounted when the language changes).
  useEffect(() => {
    void load(query);
  }, [load, query, locale]);

  // Nothing to show and nothing searched: the section stays out of the way.
  // Not an alert: the bookings above stay usable when only this list fails.
  if (failed) return <p className="legal">{t("guestMoney.loadError")}</p>;
  if (rows === null || (rows.length === 0 && query === "" && !message)) return null;

  return (
    <section aria-labelledby="collect-guests">
      <h2 id="collect-guests">{t("guestMoney.collectTitle")}</h2>
      <p>{t("guestMoney.collectIntro")}</p>
      <label>
        {t("guestMoney.search")}
        <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} />
      </label>
      {message && (
        <p role="status" className="notice ok">
          {message}
        </p>
      )}
      {rows.length === 0 ? (
        <p>{t("guestMoney.collectNone")}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <caption>{t("guestMoney.collectTitle")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("guests.colName")}</th>
                <th scope="col">{t("guestMoney.colItems")}</th>
                <th scope="col">{t("people.colDue")}</th>
                <th scope="col">{t("people.colPaid")}</th>
                <th scope="col">{t("people.colBalance")}</th>
                <th scope="col">{t("collect.colAction")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const name = `${row.first_name} ${row.last_name}`;
                return (
                  <tr key={row.guest_id}>
                    <th scope="row">
                      <Link to={adminGuestPath(row.guest_id)}>{name}</Link>
                      {row.reference && (
                        <>
                          <br />
                          <small>{row.reference}</small>
                        </>
                      )}
                    </th>
                    <td>
                      <ul className="plain">
                        {row.items.map((item) => (
                          <li key={item.label}>
                            {item.label} · {formatEuro(item.collectable_cents)}
                          </li>
                        ))}
                      </ul>
                    </td>
                    <td>{formatEuro(row.due_cents)}</td>
                    <td>{formatEuro(row.paid_cents)}</td>
                    <td>{formatEuro(row.balance_cents)}</td>
                    <td>
                      <button
                        type="button"
                        aria-label={t("guestMoney.collectAria", { name })}
                        onClick={() => setPaying(row)}
                      >
                        {t("guestMoney.collect")}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {paying && (
        <GuestMovementDialog
          guest={{
            id: paying.guest_id,
            first_name: paying.first_name,
            last_name: paying.last_name,
          }}
          kind="payment"
          suggestedCents={paying.balance_cents}
          onCancel={() => setPaying(null)}
          onSaved={() => {
            setMessage(
              t("guestMoney.recorded", { name: `${paying.first_name} ${paying.last_name}` }),
            );
            setPaying(null);
            void load(query);
          }}
        />
      )}
    </section>
  );
}
