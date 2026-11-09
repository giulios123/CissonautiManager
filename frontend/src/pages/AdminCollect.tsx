import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDeadline } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { useT, type MessageKey } from "../i18n";
import { tNow } from "../i18n/messages";
import { formatEuro } from "../money";
import { adminRegistrationPath } from "../routes";
import type { Detail } from "./AdminRegistrationDetail";
import { CollectGuests } from "./CollectGuests";
import { QuickPaymentDialog, type CollectRow } from "./QuickPaymentDialog";

type Row = CollectRow;

// The row is kept with the payment, so it stays on screen until its own undo window ends,
// whatever the list says after a refresh.
type Done = { paymentId: number; amountCents: number; row: Row };

const CHANNELS = [
  ["revolut", "channel.revolut"],
  ["satispay", "channel.satispay"],
  ["paypal", "channel.paypal"],
  ["iban", "channel.iban"],
] as const satisfies readonly (readonly [string, MessageKey])[];

/** How long a row shows "Annulla" after it was marked as paid. */
export const UNDO_WINDOW_MS = 10_000;
const CHANNEL_KEY = "collect-channel";

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
  const t = useT();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [channel, setChannel] = useState(savedChannel);
  const [done, setDone] = useState<Record<number, Done>>({});
  const doneRef = useRef<Record<number, Done>>({});
  const [busy, setBusy] = useState<Set<number>>(new Set());
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");
  const [quickPaymentRow, setQuickPaymentRow] = useState<Row | null>(null);
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());
  const feePolicy = rows?.some((row) => row.confirmation_policy === "registration_fee") ?? false;

  const load = useCallback(() => {
    api<Row[]>("/api/admin/views/to-collect")
      .then((loaded) => {
        // Rows paid a moment ago are no longer listed by the server but must stay in place
        // until their undo window is over.
        setRows((previous) => {
          const next = [...loaded];
          for (const { row } of Object.values(doneRef.current)) {
            const currentIndex = next.findIndex((r) => r.booking_id === row.booking_id);
            if (currentIndex >= 0) {
              next[currentIndex] = row;
              continue;
            }
            const previousIndex = previous?.findIndex((r) => r.booking_id === row.booking_id) ?? -1;
            next.splice(
              previousIndex < 0 ? next.length : Math.min(previousIndex, next.length),
              0,
              row,
            );
          }
          return next;
        });
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

  function updateDone(change: (current: Record<number, Done>) => Record<number, Done>) {
    doneRef.current = change(doneRef.current);
    setDone(doneRef.current);
  }

  /** End of a row's undo window: settled rows leave the list, undone ones come back. */
  function finish(id: number, settled: boolean) {
    timers.current.delete(id);
    // A settled row is removed before its paid state is cleared, or it would flash back as
    // payable and could be paid twice while the list reloads.
    if (settled) setRows((current) => current?.filter((r) => r.booking_id !== id) ?? current);
    updateDone((current) => without(current, id));
    load();
  }

  async function markPaid(row: Row) {
    const name = `${row.first_name} ${row.last_name}`;
    const amountCents =
      row.confirmation_policy === "registration_fee" &&
      (row.status === "in_attesa_pagamento" || row.status === "scaduta") &&
      row.confirmation_balance_cents != null &&
      row.confirmation_balance_cents > 0
        ? row.confirmation_balance_cents
        : row.balance_cents;
    setBusyFor(row.booking_id, true);
    setErrors((current) => without(current, row.booking_id));
    try {
      const detail = await api<Detail>(`/api/admin/registrations/${row.booking_id}/payments`, {
        method: "POST",
        json: {
          amount_cents: amountCents,
          channel,
          defer_confirmation_email: true,
        },
      });
      if (detail.payment_id == null) throw new Error("missing payment id");
      updateDone((current) => ({
        ...current,
        [row.booking_id]: {
          paymentId: detail.payment_id as number,
          amountCents,
          row,
        },
      }));
      timers.current.set(
        row.booking_id,
        setTimeout(() => finish(row.booking_id, true), UNDO_WINDOW_MS),
      );
      setMessage(
        t("collect.paymentRecorded", { amount: formatEuro(amountCents), name }) +
          (detail.warning ? ` ${detail.warning}` : ""),
      );
    } catch (error) {
      setErrors((current) => ({
        ...current,
        [row.booking_id]: error instanceof ApiError ? error.message : t("collect.cannotRecord"),
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
        json: { reason: tNow("collect.undoReason") },
      });
      const timer = timers.current.get(row.booking_id);
      if (timer) clearTimeout(timer);
      setMessage(t("collect.paymentUndone", { name }));
      finish(row.booking_id, false);
    } catch (error) {
      setErrors((current) => ({
        ...current,
        [row.booking_id]: error instanceof ApiError ? error.message : t("collect.cannotUndo"),
      }));
    } finally {
      setBusyFor(row.booking_id, false);
    }
  }

  const needle = query.trim().toLowerCase();
  const shown = rows?.filter((row) => !needle || matches(row, needle)) ?? [];

  return (
    <>
      <main className="wide">
        <h1>{t("collect.title")}</h1>
        <p>{t("collect.intro")}</p>
        <div className="row filters">
          <label>
            {t("collect.channel")}
            <select value={channel} onChange={(e) => chooseChannel(e.target.value)}>
              {CHANNELS.map(([code, label]) => (
                <option key={code} value={code}>
                  {t(label)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("collect.search")}
            <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
        </div>
        <p role="status" aria-live="polite" className="notice ok" hidden={!message}>
          {message}
        </p>
        {failed && <p role="alert">{t("collect.loadError")}</p>}
        {rows === null ? (
          <p aria-busy="true">{t("common.loading")}</p>
        ) : rows.length === 0 ? (
          <p>{t("collect.empty")}</p>
        ) : shown.length === 0 ? (
          <p>{t("collect.noResults")}</p>
        ) : (
          <>
            <p>{t("collect.count", { n: shown.length })}</p>
            <div className="table-wrap">
              <table>
                <caption className="sr-only">{t("collect.caption")}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("people.colPerson")}</th>
                    <th scope="col">{t("collect.colReference")}</th>
                    <th scope="col">{t("people.colStatus")}</th>
                    {feePolicy && (
                      <>
                        <th scope="col">{t("collect.colRegistrationFee")}</th>
                        <th scope="col">{t("collect.colToConfirm")}</th>
                      </>
                    )}
                    <th scope="col">{feePolicy ? t("collect.colTotal") : t("people.colDue")}</th>
                    <th scope="col">{t("people.colPaid")}</th>
                    <th scope="col">{t("people.colBalance")}</th>
                    <th scope="col">{t("people.colDeadline")}</th>
                    <th scope="col">{t("collect.colAction")}</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.map((row) => {
                    const name = `${row.first_name} ${row.last_name}`;
                    const paid = done[row.booking_id];
                    return (
                      <tr key={row.booking_id}>
                        <th scope="row">
                          <Link to={adminRegistrationPath(row.booking_id)}>{name}</Link>
                          <br />
                          <small>{row.email}</small>
                        </th>
                        <td>{row.personal_code}</td>
                        <td>
                          <StatusBadge status={row.status} />
                        </td>
                        {feePolicy && (
                          <>
                            <td>
                              {row.registration_fee_cents == null
                                ? "-"
                                : formatEuro(row.registration_fee_cents)}
                            </td>
                            <td>
                              {row.confirmation_balance_cents == null
                                ? "-"
                                : formatEuro(row.confirmation_balance_cents)}
                            </td>
                          </>
                        )}
                        <td>{formatEuro(row.amount_due_cents)}</td>
                        <td>{formatEuro(row.paid_cents)}</td>
                        <td>{formatEuro(row.balance_cents)}</td>
                        <td>{formatDeadline(row.hold_expires_at)}</td>
                        <td>
                          {paid ? (
                            <>
                              <span>
                                {t("collect.paid", { amount: formatEuro(paid.amountCents) })}
                              </span>{" "}
                              <button
                                type="button"
                                className="secondary"
                                disabled={busy.has(row.booking_id)}
                                aria-label={t("collect.undoAria", { name })}
                                onClick={() => undo(row, paid.paymentId)}
                              >
                                {t("collect.undo")}
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                type="button"
                                disabled={busy.has(row.booking_id)}
                                aria-label={t("collect.markAria", { name })}
                                onClick={() => markPaid(row)}
                              >
                                {t("collect.mark")}
                              </button>{" "}
                              <button
                                type="button"
                                className="link"
                                onClick={() => setQuickPaymentRow(row)}
                              >
                                {t("collect.otherAmount")}
                              </button>
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
        <CollectGuests />
      </main>
      {quickPaymentRow && (
        <QuickPaymentDialog
          initialRow={quickPaymentRow}
          channel={channel}
          onCancel={() => setQuickPaymentRow(null)}
          onSaved={(savedRow, paymentId, amountCents, undoUntil, replayed, warning) => {
            setQuickPaymentRow(null);
            const remaining = undoUntil
              ? Math.max(0, new Date(undoUntil).getTime() - Date.now())
              : replayed
                ? 0
                : UNDO_WINDOW_MS;
            if (replayed && remaining === 0) {
              load();
              setMessage(t("quickPayment.alreadyRecorded") + (warning ? ` ${warning}` : ""));
              return;
            }
            setDone((current) => ({
              ...current,
              [savedRow.booking_id]: { paymentId, amountCents, row: savedRow },
            }));
            setRows(
              (current) =>
                current?.map((item) =>
                  item.booking_id === savedRow.booking_id ? savedRow : item,
                ) ?? current,
            );
            doneRef.current = {
              ...doneRef.current,
              [savedRow.booking_id]: { paymentId, amountCents, row: savedRow },
            };
            if (remaining === 0) finish(savedRow.booking_id, true);
            else
              timers.current.set(
                savedRow.booking_id,
                setTimeout(() => finish(savedRow.booking_id, true), remaining),
              );
            setMessage(
              replayed
                ? t("quickPayment.alreadyRecorded") + (warning ? ` ${warning}` : "")
                : t("collect.paymentRecorded", {
                    amount: formatEuro(amountCents),
                    name: `${savedRow.first_name} ${savedRow.last_name}`,
                  }) + (warning ? ` ${warning}` : ""),
            );
          }}
        />
      )}
    </>
  );
}
