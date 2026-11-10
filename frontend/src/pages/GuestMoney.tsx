import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import { formatDay } from "../booking";
import { ConfirmDialog } from "../ConfirmDialog";
import type { Guest, GuestMovement } from "../guests";
import { useT, type MessageKey } from "../i18n";
import { formatEuro } from "../money";
import { GuestMovementDialog } from "./GuestMovementDialog";

const CHANNEL_LABELS: Record<string, MessageKey> = {
  revolut: "channel.revolut",
  satispay: "channel.satispay",
  paypal: "channel.paypal",
  iban: "channel.iban",
};

/** What the guest owes and has paid, with the register of payments and refunds. */
export function GuestMoney({ guest, onChange }: { guest: Guest; onChange: (g: Guest) => void }) {
  const t = useT();
  const [dialog, setDialog] = useState<"payment" | "refund" | null>(null);
  const [voiding, setVoiding] = useState<GuestMovement | null>(null);
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const clicked = useRef<HTMLButtonElement | null>(null);
  const credit = Math.max(-guest.balance_cents, 0);

  function closeVoid() {
    setVoiding(null);
    setReason("");
    setError(null);
  }

  async function confirmVoid() {
    if (!voiding) return;
    setWorking(true);
    setError(null);
    try {
      const updated = await api<Guest>(`/api/admin/guests/movements/${voiding.id}/void`, {
        method: "POST",
        json: { reason: reason.trim() },
      });
      closeVoid();
      setNotice(t("guestMoney.voided"));
      onChange(updated);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <section aria-labelledby="guest-money">
      <h2 id="guest-money">{t("guestMoney.title")}</h2>
      {guest.payer === "non_paying" && <p className="legal">{t("guestMoney.nonPaying")}</p>}
      {guest.items.length > 0 && (
        <ul className="plain">
          {guest.items.map((item) => (
            <li key={item.label}>
              {item.label} ·{" "}
              {item.collectable_cents === 0 && item.price_cents > 0
                ? t("guestMoney.provider", { cost: formatEuro(item.price_cents) })
                : formatEuro(item.collectable_cents)}
            </li>
          ))}
        </ul>
      )}
      <dl>
        <dt>{t("people.colDue")}</dt>
        <dd>{formatEuro(guest.due_cents)}</dd>
        <dt>{t("people.colPaid")}</dt>
        <dd>{formatEuro(guest.paid_cents - guest.refunded_cents)}</dd>
        <dt>{credit > 0 ? t("guestMoney.credit") : t("people.colBalance")}</dt>
        <dd>{formatEuro(credit > 0 ? credit : guest.balance_cents)}</dd>
      </dl>
      {notice && (
        <p role="status" className="notice ok">
          {notice}
        </p>
      )}
      <p>
        <button
          type="button"
          onClick={(event) => {
            clicked.current = event.currentTarget;
            setNotice("");
            setDialog("payment");
          }}
        >
          {t("guestMoney.addPayment")}
        </button>{" "}
        {credit > 0 && (
          <button
            type="button"
            className="secondary"
            onClick={(event) => {
              clicked.current = event.currentTarget;
              setNotice("");
              setDialog("refund");
            }}
          >
            {t("guestMoney.addRefund")}
          </button>
        )}
      </p>
      {guest.movements.length > 0 && (
        <ul>
          {guest.movements.map((movement) => {
            const channel = CHANNEL_LABELS[movement.channel]
              ? t(CHANNEL_LABELS[movement.channel])
              : movement.channel;
            const text = `${t(
              movement.kind === "refund" ? "guestMoney.lineRefund" : "guestMoney.linePayment",
              {
                amount: formatEuro(movement.amount_cents),
                date: formatDay(movement.paid_on),
                channel,
              },
            )}${movement.note ? `: ${movement.note}` : ""}`;
            return (
              <li key={movement.id}>
                {movement.voided_at ? (
                  <>
                    <s>{text}</s> <strong>{t("dsub.voidedWord")}</strong>: {movement.void_reason}
                  </>
                ) : (
                  <>
                    {text}{" "}
                    <button
                      type="button"
                      className="secondary"
                      aria-label={t("dsub.voidAria", { amount: formatEuro(movement.amount_cents) })}
                      onClick={(event) => {
                        clicked.current = event.currentTarget;
                        setVoiding(movement);
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
      {dialog && (
        <GuestMovementDialog
          guest={guest}
          kind={dialog}
          suggestedCents={dialog === "refund" ? credit : Math.max(guest.balance_cents, 0)}
          onCancel={() => setDialog(null)}
          onSaved={(updated) => {
            setNotice(t(dialog === "refund" ? "guestMoney.refundRecorded" : "det.paymentRecorded"));
            setDialog(null);
            onChange(updated);
          }}
        />
      )}
      {voiding && (
        <ConfirmDialog
          title={t("guestMoney.voidTitle")}
          confirmLabel={t("dsub.voidConfirm")}
          working={working}
          confirmDisabled={reason.trim() === ""}
          error={error}
          onConfirm={() => void confirmVoid()}
          onCancel={closeVoid}
          returnFocusTo={clicked}
        >
          <p>{t("guestMoney.voidBody", { amount: formatEuro(voiding.amount_cents) })}</p>
          <label>
            {t("dsub.reason")}
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
          </label>
        </ConfirmDialog>
      )}
    </section>
  );
}
