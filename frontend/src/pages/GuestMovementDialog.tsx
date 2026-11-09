import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import type { Guest } from "../guests";
import { useT, type MessageKey } from "../i18n";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";

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

/**
 * Records a payment from, or a refund to, an external guest. The same request key is kept for
 * every retry, so a payment sent twice (double click, lost answer) is recorded once.
 */
export function GuestMovementDialog({
  guest,
  kind,
  suggestedCents,
  onCancel,
  onSaved,
}: {
  guest: { id: number; first_name: string; last_name: string };
  kind: "payment" | "refund";
  suggestedCents: number;
  onCancel: () => void;
  onSaved: (guest: Guest) => void;
}) {
  const t = useT();
  const triggerRef = useRef<HTMLElement | null>(document.activeElement as HTMLElement);
  const [amount, setAmount] = useState(suggestedCents > 0 ? centsToInput(suggestedCents) : "");
  const [channel, setChannel] = useState<string>(CHANNELS[0][0]);
  const [paidOn, setPaidOn] = useState(todayInRome);
  const [note, setNote] = useState("");
  const [key] = useState(() => crypto.randomUUID());
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refund = kind === "refund";

  async function submit() {
    const cents = parseEuroToCents(amount);
    if (cents === null || cents <= 0) {
      setError(t("quickPayment.invalidAmount"));
      return;
    }
    setWorking(true);
    setError(null);
    try {
      const updated = await api<Guest>(`/api/admin/guests/${guest.id}/movements`, {
        method: "POST",
        json: {
          kind,
          amount_cents: cents,
          channel,
          paid_on: paidOn,
          note: note.trim() || null,
          request_key: key,
        },
      });
      onSaved(updated);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <ConfirmDialog
      title={t(refund ? "guestMoney.refundTitle" : "guestMoney.paymentTitle")}
      confirmLabel={t(refund ? "guestMoney.refundSave" : "quickPayment.save")}
      cancelLabel={t("dialog.back")}
      working={working}
      cancelDisabled={working}
      error={error}
      onConfirm={() => void submit()}
      onCancel={onCancel}
      returnFocusTo={triggerRef}
    >
      <p>
        {guest.first_name} {guest.last_name}
      </p>
      {suggestedCents > 0 && (
        <p>
          {t(refund ? "guestMoney.creditIs" : "guestMoney.balanceIs", {
            amount: formatEuro(suggestedCents),
          })}
        </p>
      )}
      <label>
        {t("quickPayment.amount")}
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
        {t("quickPayment.date")}
        <input
          type="date"
          value={paidOn}
          onChange={(event) => setPaidOn(event.target.value)}
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
