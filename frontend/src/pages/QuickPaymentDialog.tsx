import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { useI18n, useT, type MessageKey } from "../i18n";
import { formatEuro, parseEuroToCents } from "../money";

export type CollectRow = {
  booking_id: number;
  first_name: string;
  last_name: string;
  email: string;
  personal_code: string;
  status: string;
  confirmation_policy: "legacy_total" | "registration_fee";
  registration_fee_cents: number | null;
  confirmation_balance_cents: number | null;
  confirmation_due_cents: number | null;
  amount_due_cents: number;
  paid_cents: number;
  balance_cents: number;
  hold_expires_at: string;
};

const CHANNELS = [
  ["revolut", "channel.revolut"],
  ["satispay", "channel.satispay"],
  ["paypal", "channel.paypal"],
  ["iban", "channel.iban"],
] as const satisfies readonly (readonly [string, MessageKey])[];

function todayInRome() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Rome",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

export function QuickPaymentDialog({
  initialRow,
  channel,
  onCancel,
  onSaved,
}: {
  initialRow: CollectRow;
  channel: string;
  onCancel: () => void;
  onSaved: (
    row: CollectRow,
    paymentId: number,
    amount: number,
    undoUntil: string | null,
    replayed: boolean,
    warning: string | null,
  ) => void;
}) {
  const { locale } = useI18n();
  const t = useT();
  const initialLocale = useRef(locale);
  const triggerRef = useRef<HTMLElement | null>(document.activeElement as HTMLElement);
  const [requestChannel] = useState(channel);
  const [row, setRow] = useState(initialRow);
  const [amount, setAmount] = useState("");
  const [paidOn, setPaidOn] = useState(todayInRome);
  const [note, setNote] = useState("");
  const [key, setKey] = useState(crypto.randomUUID());
  const [working, setWorking] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [canSave, setCanSave] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialLocale.current !== locale && !working && !uncertain) onCancel();
  }, [locale, onCancel, uncertain, working]);

  async function submit() {
    const cents = parseEuroToCents(amount);
    if (cents === null || cents <= 0) {
      setError(t("quickPayment.invalidAmount"));
      return;
    }
    setWorking(true);
    setError(null);
    try {
      const result = await api<{
        payment_id: number;
        payment_replayed: boolean;
        payment_undo_until: string | null;
        warning: string | null;
        participant: {
          first_name: string;
          last_name: string;
          email: string;
          personal_code: string;
        };
        booking: {
          status: string;
          confirmation_policy: "legacy_total" | "registration_fee";
          registration_fee_cents: number | null;
          confirmation_balance_cents: number | null;
          confirmation_due_cents: number | null;
          amount_due_cents: number;
          paid_cents: number;
          balance_cents: number;
          hold_expires_at: string;
        };
      }>(`/api/admin/registrations/${row.booking_id}/payments`, {
        method: "POST",
        json: {
          amount_cents: cents,
          channel: requestChannel,
          paid_on: paidOn,
          note,
          defer_confirmation_email: true,
          request_key: key,
          expected_snapshot: {
            status: row.status,
            confirmation_policy: row.confirmation_policy,
            amount_due_cents: row.amount_due_cents,
            paid_cents: row.paid_cents,
            registration_fee_cents: row.registration_fee_cents,
            confirmation_due_cents: row.confirmation_due_cents,
          },
        },
      });
      setUncertain(false);
      onSaved(
        {
          ...row,
          first_name: result.participant.first_name,
          last_name: result.participant.last_name,
          email: result.participant.email,
          personal_code: result.participant.personal_code,
          status: result.booking.status,
          confirmation_policy: result.booking.confirmation_policy,
          registration_fee_cents: result.booking.registration_fee_cents,
          confirmation_balance_cents: result.booking.confirmation_balance_cents,
          confirmation_due_cents: result.booking.confirmation_due_cents,
          amount_due_cents: result.booking.amount_due_cents,
          paid_cents: result.booking.paid_cents,
          balance_cents: result.booking.balance_cents,
          hold_expires_at: result.booking.hold_expires_at,
        },
        result.payment_id,
        cents,
        result.payment_undo_until,
        result.payment_replayed,
        result.warning,
      );
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) {
        if (caught.code === "payment_request_conflict") {
          setUncertain(true);
          setError(caught.message);
          return;
        }
        try {
          const latest = await api<CollectRow[]>("/api/admin/views/to-collect");
          const fresh = latest.find((item) => item.booking_id === row.booking_id);
          if (fresh) {
            setRow(fresh);
            setKey(crypto.randomUUID());
            setCanSave(true);
            setError(t("quickPayment.changed"));
          } else {
            setCanSave(false);
            setError(t("quickPayment.noLongerDue"));
          }
        } catch {
          setError(t("quickPayment.refreshFailed"));
        }
      } else {
        if (!(caught instanceof ApiError) || caught.status >= 500) setUncertain(true);
        setError(caught instanceof Error ? caught.message : t("common.retryShortly"));
      }
    } finally {
      setWorking(false);
    }
  }

  return (
    <ConfirmDialog
      title={t("quickPayment.title")}
      confirmLabel={t(uncertain ? "quickPayment.retry" : "quickPayment.save")}
      cancelLabel={t("dialog.back")}
      working={working}
      cancelDisabled={working || uncertain}
      confirmDisabled={!canSave}
      error={error}
      onConfirm={submit}
      onCancel={onCancel}
      returnFocusTo={triggerRef}
    >
      <p>
        {row.first_name} {row.last_name} · {row.personal_code}
      </p>
      <p>{t("quickPayment.totalBalance", { amount: formatEuro(row.balance_cents) })}</p>
      {row.confirmation_balance_cents !== null && (
        <p>
          {t("quickPayment.confirmationBalance", {
            amount: formatEuro(row.confirmation_balance_cents),
          })}
        </p>
      )}
      <label>
        {t("quickPayment.amount")}
        <input
          autoFocus
          inputMode="decimal"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          disabled={working || uncertain}
        />
      </label>
      <label>
        {t("quickPayment.channel")}
        <select value={requestChannel} disabled>
          {CHANNELS.map(([code, label]) => (
            <option key={code} value={code}>
              {t(label)}
            </option>
          ))}
        </select>
      </label>
      <label>
        {t("quickPayment.date")}
        <input
          type="date"
          value={paidOn}
          onChange={(e) => setPaidOn(e.target.value)}
          disabled={working || uncertain}
        />
      </label>
      <label>
        {t("quickPayment.note")}
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          disabled={working || uncertain}
        />
      </label>
    </ConfirmDialog>
  );
}
