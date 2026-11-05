import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { formatDay } from "../booking";
import { ConfirmDialog } from "../ConfirmDialog";
import { formatEuro } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

type Payment = BookingView["payments"][number];

const CHANNEL_LABELS: Record<string, string> = {
  revolut: "Revolut",
  satispay: "Satispay",
  paypal: "PayPal",
  iban: "Bonifico (IBAN)",
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
      onDone(updated, "Pagamento annullato: non conta più nel saldo.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    } finally {
      setWorking(false);
    }
  }

  if (payments.length === 0) return null;
  return (
    <>
      <ul>
        {payments.map((payment) => {
          const text = `${formatEuro(payment.amount_cents)} il ${formatDay(payment.paid_on)} (${
            CHANNEL_LABELS[payment.channel] ?? payment.channel
          })${payment.note ? `: ${payment.note}` : ""}`;
          return (
            <li key={payment.id}>
              {payment.voided ? (
                <>
                  <s>{text}</s> <strong>annullato</strong>: {payment.void_reason}
                </>
              ) : (
                <>
                  {text}{" "}
                  <button
                    type="button"
                    className="secondary"
                    aria-label={`Annulla il pagamento di ${formatEuro(payment.amount_cents)}`}
                    onClick={(event) => {
                      clickedRef.current = event.currentTarget;
                      setTarget(payment);
                    }}
                  >
                    Annulla
                  </button>
                </>
              )}
            </li>
          );
        })}
      </ul>
      {target && (
        <ConfirmDialog
          title="Annullare questo pagamento?"
          confirmLabel="Sì, annullo"
          working={working}
          confirmDisabled={reason.trim() === ""}
          error={error}
          onConfirm={confirm}
          onCancel={close}
          returnFocusTo={clickedRef}
        >
          <p>
            Il pagamento di {formatEuro(target.amount_cents)} resta in elenco ma non conta più. Se
            la prenotazione era confermata e non è più coperta, torna in attesa di pagamento con un
            nuovo blocco.
          </p>
          <label>
            Motivo (obbligatorio)
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
          </label>
        </ConfirmDialog>
      )}
    </>
  );
}
