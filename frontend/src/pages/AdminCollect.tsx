import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDeadline } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { formatEuro } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

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
  hold_expires_at: string;
};

type Done = { paymentId: number; amountCents: number };

const CHANNELS = [
  ["revolut", "Revolut"],
  ["satispay", "Satispay"],
  ["paypal", "PayPal"],
  ["iban", "Bonifico (IBAN)"],
] as const;

/** How long a row shows "Annulla" after it was marked as paid. */
export const UNDO_WINDOW_MS = 10_000;
const CHANNEL_KEY = "collect-channel";
const UNDO_REASON = "Annullato subito dalla vista Da incassare";

function savedChannel(): string {
  try {
    const stored = window.localStorage.getItem(CHANNEL_KEY);
    if (CHANNELS.some(([code]) => code === stored)) return stored as string;
  } catch {
    // Storage can be blocked: the page works without remembering the channel.
  }
  return CHANNELS[0][0];
}

function without<T>(record: Record<number, T>, id: number): Record<number, T> {
  const copy = { ...record };
  delete copy[id];
  return copy;
}

function matches(row: Row, needle: string): boolean {
  const text = [
    `${row.first_name} ${row.last_name}`,
    `${row.last_name} ${row.first_name}`,
    row.email,
    row.personal_code,
  ]
    .join("\n")
    .toLowerCase();
  return text.includes(needle);
}

export function AdminCollect() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [channel, setChannel] = useState(savedChannel);
  const [done, setDone] = useState<Record<number, Done>>({});
  const [busy, setBusy] = useState<Set<number>>(new Set());
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const load = useCallback(() => {
    api<Row[]>("/api/admin/views/to-collect")
      .then((loaded) => {
        setRows(loaded);
        setFailed(false);
      })
      .catch(() => setFailed(true));
  }, []);

  useEffect(load, [load]);
  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach((timer) => clearTimeout(timer));
  }, []);

  function chooseChannel(code: string) {
    setChannel(code);
    try {
      window.localStorage.setItem(CHANNEL_KEY, code);
    } catch {
      // Not remembered: fine.
    }
  }

  function setBusyFor(id: number, on: boolean) {
    setBusy((current) => {
      const next = new Set(current);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function finish(id: number) {
    timers.current.delete(id);
    setDone((current) => without(current, id));
    load();
  }

  async function markPaid(row: Row) {
    const name = `${row.first_name} ${row.last_name}`;
    setBusyFor(row.booking_id, true);
    setErrors((current) => without(current, row.booking_id));
    try {
      const detail = await api<Detail>(`/api/admin/registrations/${row.booking_id}/payments`, {
        method: "POST",
        json: {
          amount_cents: row.balance_cents,
          channel,
          defer_confirmation_email: true,
        },
      });
      const latest = detail.booking.payments
        .filter((payment) => !payment.voided)
        .reduce((a, b) => (b.id > a.id ? b : a));
      setDone((current) => ({
        ...current,
        [row.booking_id]: { paymentId: latest.id, amountCents: row.balance_cents },
      }));
      timers.current.set(
        row.booking_id,
        setTimeout(() => finish(row.booking_id), UNDO_WINDOW_MS),
      );
      setMessage(
        `Pagamento di ${formatEuro(row.balance_cents)} registrato per ${name}.` +
          (detail.warning ? ` ${detail.warning}` : ""),
      );
    } catch (error) {
      setErrors((current) => ({
        ...current,
        [row.booking_id]: error instanceof ApiError ? error.message : "Non riesco a registrarlo.",
      }));
    } finally {
      setBusyFor(row.booking_id, false);
    }
  }

  async function undo(row: Row, paymentId: number) {
    const name = `${row.first_name} ${row.last_name}`;
    setBusyFor(row.booking_id, true);
    try {
      await api<Detail>(`/api/admin/registrations/${row.booking_id}/payments/${paymentId}/void`, {
        method: "POST",
        json: { reason: UNDO_REASON },
      });
      const timer = timers.current.get(row.booking_id);
      if (timer) clearTimeout(timer);
      setMessage(`Pagamento annullato per ${name}.`);
      finish(row.booking_id);
    } catch (error) {
      setErrors((current) => ({
        ...current,
        [row.booking_id]: error instanceof ApiError ? error.message : "Non riesco ad annullarlo.",
      }));
    } finally {
      setBusyFor(row.booking_id, false);
    }
  }

  const needle = query.trim().toLowerCase();
  const shown = rows?.filter((row) => !needle || matches(row, needle)) ?? [];

  return (
    <main className="wide">
      <h1>Da incassare</h1>
      <p>
        Le iscrizioni che aspettano un pagamento. Controlla il conto, cerca la causale e segna il
        pagamento: dopo averlo segnato hai 10 secondi per annullare, e l&apos;email di conferma
        parte dopo 30 secondi.
      </p>
      <div className="row filters">
        <label>
          Canale dei pagamenti che segni
          <select value={channel} onChange={(e) => chooseChannel(e.target.value)}>
            {CHANNELS.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cerca per nome, email o causale
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
      </div>
      <p role="status" aria-live="polite" className="notice ok" hidden={!message}>
        {message}
      </p>
      {failed && <p role="alert">Non riesco a caricare l&apos;elenco.</p>}
      {rows === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : rows.length === 0 ? (
        <p>Nessun pagamento da incassare.</p>
      ) : shown.length === 0 ? (
        <p>Nessun risultato.</p>
      ) : (
        <>
          <p>{shown.length} da incassare</p>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">Iscrizioni da incassare</caption>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Causale</th>
                  <th scope="col">Stato</th>
                  <th scope="col">Dovuto</th>
                  <th scope="col">Versato</th>
                  <th scope="col">Saldo</th>
                  <th scope="col">Scadenza</th>
                  <th scope="col">Azione</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((row) => {
                  const name = `${row.first_name} ${row.last_name}`;
                  const paid = done[row.booking_id];
                  return (
                    <tr key={row.booking_id}>
                      <th scope="row">
                        <Link to={`/admin/iscrizioni/${row.booking_id}`}>{name}</Link>
                        <br />
                        <small>{row.email}</small>
                      </th>
                      <td>{row.personal_code}</td>
                      <td>
                        <StatusBadge status={row.status} />
                      </td>
                      <td>{formatEuro(row.amount_due_cents)}</td>
                      <td>{formatEuro(row.paid_cents)}</td>
                      <td>{formatEuro(row.balance_cents)}</td>
                      <td>{formatDeadline(row.hold_expires_at)}</td>
                      <td>
                        {paid ? (
                          <>
                            <span>Pagato {formatEuro(paid.amountCents)}</span>{" "}
                            <button
                              type="button"
                              className="secondary"
                              disabled={busy.has(row.booking_id)}
                              aria-label={`Annulla il pagamento di ${name}`}
                              onClick={() => undo(row, paid.paymentId)}
                            >
                              Annulla
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              disabled={busy.has(row.booking_id)}
                              aria-label={`Segna pagato per ${name}`}
                              onClick={() => markPaid(row)}
                            >
                              Segna pagato
                            </button>{" "}
                            <Link to={`/admin/iscrizioni/${row.booking_id}`}>Altro importo</Link>
                          </>
                        )}
                        {errors[row.booking_id] && (
                          <p role="alert" className="notice error">
                            {errors[row.booking_id]}
                          </p>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
