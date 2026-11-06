import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { formatDay } from "../booking";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT, type MessageKey } from "../i18n";
import { formatEuro } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

type Payment = BookingView["payments"][number];

const CHANNEL_LABELS: Record<string, MessageKey> = {
  revolut: "channel.revolut",
  satispay: "channel.satispay",
  paypal: "channel.paypal",
  iban: "channel.iban",
};

export function AdminPayments({
  bookingId,
  payments,
  onDone,
}: {
  bookingId: number;
  payments: Payment[];
  onDone: (detail: Detail, text: string) => void;
}) {
  const t = useT();
  const [target, setTarget] = useState<Payment | null>(null);
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clickedRef = useRef<HTMLButtonElement | null>(null);

  function close() {
    setTarget(null);
    setReason("");
    setError(null);
  }

  async function confirm() {
    if (!target) return;
    setWorking(true);
    setError(null);
    try {
      const updated = await api<Detail>(
        `/api/admin/registrations/${bookingId}/payments/${target.id}/void`,
        { method: "POST", json: { reason: reason.trim() } },
      );
      close();
      onDone(updated, t("dsub.paymentVoided"));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  if (payments.length === 0) return null;
  return (
    <>
      <ul>
        {payments.map((payment) => {
          const channel = CHANNEL_LABELS[payment.channel]
            ? t(CHANNEL_LABELS[payment.channel])
            : payment.channel;
          const text = `${t("dsub.paymentLine", {
            amount: formatEuro(payment.amount_cents),
            date: formatDay(payment.paid_on),
            channel,
          })}${payment.note ? `: ${payment.note}` : ""}`;
          return (
            <li key={payment.id}>
              {payment.voided ? (
                <>
                  <s>{text}</s> <strong>{t("dsub.voidedWord")}</strong>: {payment.void_reason}
                </>
              ) : (
                <>
                  {text}{" "}
                  <button
                    type="button"
                    className="secondary"
                    aria-label={t("dsub.voidAria", { amount: formatEuro(payment.amount_cents) })}
                    onClick={(event) => {
                      clickedRef.current = event.currentTarget;
                      setTarget(payment);
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
      {target && (
        <ConfirmDialog
          title={t("dsub.voidTitle")}
          confirmLabel={t("dsub.voidConfirm")}
          working={working}
          confirmDisabled={reason.trim() === ""}
          error={error}
          onConfirm={confirm}
          onCancel={close}
          returnFocusTo={clickedRef}
        >
          <p>{t("dsub.voidBody", { amount: formatEuro(target.amount_cents) })}</p>
          <label>
            {t("dsub.reason")}
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
          </label>
        </ConfirmDialog>
      )}
    </>
  );
}
