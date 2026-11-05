import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { Detail } from "./AdminRegistrationDetail";

export function AdminEditDetails({
  bookingId,
  participant,
  onDone,
}: {
  bookingId: number;
  participant: Detail["participant"];
  onDone: (detail: Detail, text: string) => void;
}) {
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "");
    try {
      const updated = await api<Detail>(`/api/admin/registrations/${bookingId}`, {
        method: "PATCH",
        json: {
          first_name: text("first_name"),
          last_name: text("last_name"),
          email: text("email"),
          phone: text("phone"),
          invited_by: text("invited_by"),
          can_bring: text("can_bring"),
        },
      });
      onDone(updated, "Dati salvati.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    }
  }

  return (
    // Keyed on the saved values so the fields show what the server now holds.
    <form onSubmit={submit} aria-labelledby="edit-title" key={JSON.stringify(participant)}>
      <h2 id="edit-title">Modifica i dati</h2>
      <div className="row">
        <label>
          Nome
          <input name="first_name" defaultValue={participant.first_name} required maxLength={100} />
        </label>
        <label>
          Cognome
          <input name="last_name" defaultValue={participant.last_name} required maxLength={100} />
        </label>
      </div>
      <label>
        Email
        <input type="email" name="email" defaultValue={participant.email} required />
      </label>
      <label>
        Telefono (vuoto = nessuno)
        <input type="tel" name="phone" defaultValue={participant.phone ?? ""} maxLength={50} />
      </label>
      <label>
        Invitato da (vuoto = nessuno)
        <input name="invited_by" defaultValue={participant.invited_by ?? ""} maxLength={200} />
      </label>
      <label>
        Cosa porta al camp
        <textarea
          name="can_bring"
          rows={3}
          defaultValue={participant.can_bring ?? ""}
          required
          maxLength={2000}
        />
      </label>
      <button type="submit">Salva i dati</button>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </form>
  );
}
