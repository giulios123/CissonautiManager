import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useT } from "../i18n";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

export function AdminRefundForm({
  bookingId,
  paidCents,
  onDone,
}: {
  bookingId: number;
  paidCents: number;
  onDone: (detail: Detail) => void;
}) {
  const t = useT();
  const [amount, setAmount] = useState(paidCents > 0 ? centsToInput(paidCents) : "0,00");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const data = new FormData(event.currentTarget);
    const cents = parseEuroToCents(amount);
    if (cents === null) {
      setError(t("dsub.refundAmountInvalid"));
      return;
    }
    try {
      onDone(
        await api<Detail>(`/api/admin/registrations/${bookingId}/refund`, {
          method: "POST",
          json: {
            amount_cents: cents,
            refunded_on: String(data.get("refunded_on") ?? "") || null,
            note: String(data.get("note") ?? "") || null,
          },
        }),
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="refund-title">
      <h2 id="refund-title">{t("dsub.refundTitle")}</h2>
      <p>{t("dsub.refundIntro")}</p>
      <label>
        {t("dsub.refundAmount")}
        <input
          inputMode="decimal"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          required
        />
      </label>
      {paidCents > 0 && (
        <p>
          <button
            type="button"
            className="secondary"
            onClick={() => setAmount(centsToInput(paidCents))}
          >
            {t("dsub.refundAll", { amount: formatEuro(paidCents) })}
          </button>
        </p>
      )}
      <label>
        {t("dsub.refundDate")}
        <input type="date" name="refunded_on" />
      </label>
      <label>
        {t("det.note")}
        <input name="note" maxLength={1000} />
      </label>
      <button type="submit">{t("dsub.refundTitle")}</button>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </form>
  );
}
