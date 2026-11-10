import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { formatDay } from "../booking";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT, type MessageKey } from "../i18n";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

type Refund = NonNullable<BookingView["refunds"]>[number];

const CHANNELS = [
  ["revolut", "channel.revolut"],
  ["satispay", "channel.satispay"],
  ["paypal", "channel.paypal"],
  ["iban", "channel.iban"],
] as const satisfies readonly (readonly [string, MessageKey])[];

const CHANNEL_LABELS: Record<string, MessageKey> = Object.fromEntries(CHANNELS);

function todayInRome() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Rome",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

/**
 * Credit of an active booking (what was paid beyond the total due) and the refunds given back.
 * A refund never exceeds the credit and changes neither the place nor the payments.
 */
export function AdminCreditRefunds({
  booking,
  onDone,
}: {
  booking: BookingView;
  onDone: (detail: Detail, text: string) => void;
}) {
  const t = useT();
  const refunds = booking.refunds ?? [];
  const credit = Math.max(booking.paid_cents - booking.amount_due_cents, 0);
  const [adding, setAdding] = useState(false);
  const [voiding, setVoiding] = useState<Refund | null>(null);
  const clicked = useRef<HTMLButtonElement | null>(null);

  if (credit === 0 && refunds.length === 0) return null;
  return (
    <section aria-labelledby="credit-refunds">
      <h3 id="credit-refunds">{t("creditRefund.title")}</h3>
      {credit > 0 && (
        <p>
          {t("creditRefund.credit", { amount: formatEuro(credit) })}{" "}
          {booking.editable && (
            <button
              type="button"
              className="secondary"
              onClick={(event) => {
                clicked.current = event.currentTarget;
                setAdding(true);
              }}
            >
              {t("creditRefund.add")}
            </button>
          )}
        </p>
      )}
      {refunds.length > 0 && (
        <ul>
          {refunds.map((refund) => {
            const channel = CHANNEL_LABELS[refund.channel]
              ? t(CHANNEL_LABELS[refund.channel])
              : refund.channel;
            const text = `${t("me.refundLine", {
              amount: formatEuro(refund.amount_cents),
              date: formatDay(refund.refunded_on),
              channel,
            })}${refund.note ? `: ${refund.note}` : ""}`;
            return (
              <li key={refund.id}>
                {refund.voided ? (
                  <>
                    <s>{text}</s> <strong>{t("dsub.voidedWord")}</strong>: {refund.void_reason}
                  </>
                ) : (
                  <>
                    {text}{" "}
                    <button
                      type="button"
                      className="secondary"
                      aria-label={t("creditRefund.voidAria", {
                        amount: formatEuro(refund.amount_cents),
                      })}
                      onClick={(event) => {
                        clicked.current = event.currentTarget;
                        setVoiding(refund);
                      }}
                    >
                      {t("collect.undo")}
                    </button>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {adding && (
        <RefundDialog
          bookingId={booking.id}
          credit={credit}
          returnFocusTo={clicked}
          onCancel={() => setAdding(false)}
          onSaved={(detail) => {
            setAdding(false);
            onDone(detail, t("creditRefund.recorded"));
          }}
        />
      )}
      {voiding && (
        <VoidDialog
          bookingId={booking.id}
          refund={voiding}
          returnFocusTo={clicked}
          onCancel={() => setVoiding(null)}
          onSaved={(detail) => {
            setVoiding(null);
            onDone(detail, t("creditRefund.voided"));
          }}
        />
      )}
    </section>
  );
}

function RefundDialog({
  bookingId,
  credit,
  returnFocusTo,
  onCancel,
  onSaved,
}: {
  bookingId: number;
  credit: number;
  returnFocusTo: React.RefObject<HTMLElement | null>;
  onCancel: () => void;
  onSaved: (detail: Detail) => void;
}) {
  const t = useT();
  const [amount, setAmount] = useState(centsToInput(credit));
  const [channel, setChannel] = useState<string>(CHANNELS[0][0]);
  const [refundedOn, setRefundedOn] = useState(todayInRome);
  const [note, setNote] = useState("");
  // The same key for every retry: a refund sent twice is recorded once.
  const [key] = useState(() => crypto.randomUUID());
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const cents = parseEuroToCents(amount);
    if (cents === null || cents <= 0) {
      setError(t("quickPayment.invalidAmount"));
      return;
    }
    setWorking(true);
    setError(null);
    try {
      const detail = await api<Detail>(`/api/admin/registrations/${bookingId}/refunds`, {
        method: "POST",
        json: {
          amount_cents: cents,
          channel,
          refunded_on: refundedOn,
          note: note.trim() || null,
          request_key: key,
        },
      });
      onSaved(detail);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <ConfirmDialog
      title={t("creditRefund.dialogTitle")}
      confirmLabel={t("creditRefund.save")}
      cancelLabel={t("dialog.back")}
      working={working}
      cancelDisabled={working}
      error={error}
      onConfirm={() => void submit()}
      onCancel={onCancel}
      returnFocusTo={returnFocusTo}
    >
      <p>{t("creditRefund.credit", { amount: formatEuro(credit) })}</p>
      <label>
        {t("creditRefund.amount")}
        <input
          autoFocus
          inputMode="decimal"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          disabled={working}
        />
      </label>
      <label>
        {t("quickPayment.channel")}
        <select
          value={channel}
          onChange={(event) => setChannel(event.target.value)}
          disabled={working}
        >
          {CHANNELS.map(([code, label]) => (
            <option key={code} value={code}>
              {t(label)}
            </option>
          ))}
        </select>
      </label>
      <label>
        {t("creditRefund.date")}
        <input
          type="date"
          value={refundedOn}
          onChange={(event) => setRefundedOn(event.target.value)}
          disabled={working}
        />
      </label>
      <label>
        {t("quickPayment.note")}
        <textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          disabled={working}
        />
      </label>
    </ConfirmDialog>
  );
}

function VoidDialog({
  bookingId,
  refund,
  returnFocusTo,
  onCancel,
  onSaved,
}: {
  bookingId: number;
  refund: Refund;
  returnFocusTo: React.RefObject<HTMLElement | null>;
  onCancel: () => void;
  onSaved: (detail: Detail) => void;
}) {
  const t = useT();
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setWorking(true);
    setError(null);
    try {
      onSaved(
        await api<Detail>(`/api/admin/registrations/${bookingId}/refunds/${refund.id}/void`, {
          method: "POST",
          json: { reason: reason.trim() },
        }),
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <ConfirmDialog
      title={t("creditRefund.voidTitle")}
      confirmLabel={t("dsub.voidConfirm")}
      working={working}
      confirmDisabled={reason.trim() === ""}
      error={error}
      onConfirm={() => void confirm()}
      onCancel={onCancel}
      returnFocusTo={returnFocusTo}
    >
      <p>{t("creditRefund.voidBody", { amount: formatEuro(refund.amount_cents) })}</p>
      <label>
        {t("dsub.reason")}
        <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
      </label>
    </ConfirmDialog>
  );
}
