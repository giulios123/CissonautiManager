import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDay, formatDeadline, statusLabel } from "../booking";
import { type BookingView } from "../auth";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";

type Detail = {
  participant: {
    first_name: string;
    last_name: string;
    email: string;
    phone: string | null;
    invited_by: string | null;
    can_bring: string | null;
    personal_code: string;
  };
  booking: BookingView;
  privacy: { version: number; accepted_at: string };
  disclaimer: { version: number; accepted_at: string };
  warning: string | null;
};

const CHANNELS = [
  ["revolut", "Revolut"],
  ["satispay", "Satispay"],
  ["paypal", "PayPal"],
  ["iban", "Bonifico (IBAN)"],
] as const;

export function AdminRegistrationDetail() {
  const { id } = useParams();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failed, setFailed] = useState(false);
  const [amount, setAmount] = useState("");
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    api<Detail>(`/api/admin/registrations/${id}`)
      .then(setDetail)
      .catch(() => setFailed(true));
  }, [id]);

  if (failed) return <main role="alert">Iscrizione non trovata.</main>;
  if (!detail) return <main aria-busy="true">Caricamento…</main>;

  const { participant, booking } = detail;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const cents = parseEuroToCents(amount);
    if (cents === null || cents === 0) {
      setNotice({ ok: false, text: "Scrivi un importo valido, ad esempio 12,00." });
      return;
    }
    try {
      const updated = await api<Detail>(`/api/admin/registrations/${id}/payments`, {
        method: "POST",
        json: {
          amount_cents: cents,
          channel: String(data.get("channel")),
          paid_on: String(data.get("paid_on") ?? "") || null,
          note: String(data.get("note") ?? "") || null,
        },
      });
      setDetail(updated);
      setAmount("");
      form.reset();
      setNotice({
        ok: true,
        text:
          updated.booking.status === "confermata"
            ? "Pagamento registrato: l'iscrizione è confermata e la persona riceve un'email."
            : "Pagamento registrato.",
      });
    } catch (error) {
      setNotice({ ok: false, text: error instanceof ApiError ? error.message : "Riprova." });
    }
  }

  return (
    <main>
      <p>
        <Link to="/admin">← Tutte le iscrizioni</Link>
      </p>
      <h1>
        {participant.first_name} {participant.last_name}
      </h1>
      {detail.warning && (
        <p role="alert" className="notice error">
          {detail.warning}
        </p>
      )}

      <section aria-labelledby="who">
        <h2 id="who">Dati</h2>
        <dl>
          <dt>Email</dt>
          <dd>{participant.email}</dd>
          <dt>Telefono</dt>
          <dd>{participant.phone ?? "-"}</dd>
          <dt>Invitato da</dt>
          <dd>{participant.invited_by ?? "-"}</dd>
          <dt>Cosa porta al camp</dt>
          <dd className="legal">{participant.can_bring ?? "-"}</dd>
          <dt>Causale</dt>
          <dd>{participant.personal_code}</dd>
          <dt>Privacy accettata</dt>
          <dd>
            versione {detail.privacy.version}, {formatDeadline(detail.privacy.accepted_at)}
          </dd>
          <dt>Scarico accettato</dt>
          <dd>
            versione {detail.disclaimer.version}, {formatDeadline(detail.disclaimer.accepted_at)}
          </dd>
        </dl>
      </section>

      <section aria-labelledby="booking">
        <h2 id="booking">Iscrizione: {statusLabel(booking.status)}</h2>
        <ul>
          {booking.slots.map((slot) => (
            <li key={slot.label}>{slot.label}</li>
          ))}
        </ul>
        <p>
          Dovuto <strong>{formatEuro(booking.amount_due_cents)}</strong>, versato{" "}
          <strong>{formatEuro(booking.paid_cents)}</strong>, saldo{" "}
          <strong>{formatEuro(booking.balance_cents)}</strong>.
          {booking.status === "in_attesa_pagamento" && (
            <> Il posto è bloccato fino al {formatDeadline(booking.hold_expires_at)}.</>
          )}
        </p>
        {booking.payments.length > 0 && (
          <ul>
            {booking.payments.map((payment, index) => (
              <li key={index}>
                {formatEuro(payment.amount_cents)} il {formatDay(payment.paid_on)} (
                {payment.channel}){payment.note ? `: ${payment.note}` : ""}
              </li>
            ))}
          </ul>
        )}
      </section>

      <form onSubmit={submit} aria-labelledby="pay-title">
        <h2 id="pay-title">Registra un pagamento</h2>
        <label>
          Importo (€)
          <input
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </label>
        {booking.balance_cents > 0 && (
          <p>
            <button
              type="button"
              className="secondary"
              onClick={() => setAmount(centsToInput(booking.balance_cents))}
            >
              Metti il saldo ({formatEuro(booking.balance_cents)})
            </button>
          </p>
        )}
        <label>
          Canale
          <select name="channel" defaultValue="iban">
            {CHANNELS.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Data del pagamento (vuota = oggi)
          <input type="date" name="paid_on" />
        </label>
        <label>
          Nota (facoltativa)
          <input name="note" maxLength={1000} />
        </label>
        <button type="submit">Registra pagamento</button>
        {notice && (
          <p
            role={notice.ok ? "status" : "alert"}
            className={`notice ${notice.ok ? "ok" : "error"}`}
          >
            {notice.text}
          </p>
        )}
      </form>
    </main>
  );
}
