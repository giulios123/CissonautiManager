import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { formatDeadline, toRomeLocalInput } from "../booking";
import type { Detail } from "./AdminRegistrationDetail";

type Props = {
  bookingId: number;
  status: string;
  holdExpiresAt: string;
  onDone: (detail: Detail, text: string) => void;
};

/** Extend a pending hold, or bring an expired booking back. */
export function AdminHoldActions({ bookingId, status, holdExpiresAt, onDone }: Props) {
  const [error, setError] = useState<string | null>(null);

  async function call(request: Promise<Detail>, text: string) {
    setError(null);
    try {
      onDone(await request, text);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    }
  }

  function extend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const hold = String(new FormData(event.currentTarget).get("hold") ?? "");
    // Without a time zone, the server reads the value as Rome time.
    void call(
      api<Detail>(`/api/admin/registrations/${bookingId}`, {
        method: "PATCH",
        json: { hold_expires_at: hold },
      }),
      "Scadenza prorogata.",
    );
  }

  if (status === "in_attesa_pagamento") {
    return (
      <form onSubmit={extend} aria-labelledby="extend-title" key={holdExpiresAt}>
        <h2 id="extend-title">Proroga il blocco</h2>
        <p>
          Ora il posto è bloccato fino al {formatDeadline(holdExpiresAt)}. Scegli una nuova
          scadenza, in orario italiano.
        </p>
        <label>
          Nuova scadenza
          <input
            type="datetime-local"
            name="hold"
            defaultValue={toRomeLocalInput(holdExpiresAt)}
            required
          />
        </label>
        <button type="submit">Proroga</button>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
      </form>
    );
  }

  if (status === "scaduta") {
    return (
      <section aria-labelledby="revive-title">
        <h2 id="revive-title">Riattiva la prenotazione</h2>
        <p>
          Rimette i posti in blocco per i giorni previsti, se ci sono ancora per tutti gli slot. Se
          un pagamento già registrato copre la quota, la conferma subito.
        </p>
        <button
          type="button"
          onClick={() =>
            void call(
              api<Detail>(`/api/admin/registrations/${bookingId}/reactivate`, { method: "POST" }),
              "Prenotazione riattivata.",
            )
          }
        >
          Riattiva la prenotazione
        </button>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
      </section>
    );
  }
  return null;
}
