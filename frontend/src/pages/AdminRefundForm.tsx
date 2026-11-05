import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
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
  const [amount, setAmount] = useState(paidCents > 0 ? centsToInput(paidCents) : "0,00");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const data = new FormData(event.currentTarget);
    const cents = parseEuroToCents(amount);
    if (cents === null) {
      setError(
        "Scrivi un importo valido, ad esempio 11,00 (anche 0 se non c'è nulla da rimborsare).",
      );
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
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="refund-title">
      <h2 id="refund-title">Segna come rimborsata</h2>
      <p>
        Il rimborso lo fai fuori dal sistema e scrivi tu alla persona: qui lo registri per chiudere
        la disdetta.
      </p>
      <label>
        Importo rimborsato (€)
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
            Tutto quanto versato ({formatEuro(paidCents)})
          </button>
        </p>
      )}
      <label>
        Data del rimborso (vuota = oggi)
        <input type="date" name="refunded_on" />
      </label>
      <label>
        Nota (facoltativa)
        <input name="note" maxLength={1000} />
      </label>
      <button type="submit">Segna come rimborsata</button>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </form>
  );
}
