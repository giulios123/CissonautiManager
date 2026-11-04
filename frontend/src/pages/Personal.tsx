import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { type BookingView, type Me } from "../auth";
import { formatDay, formatDeadline, statusLabel } from "../booking";
import { formatEuro } from "../money";

type State = { status: "loading" } | { status: "anonymous" } | { status: "ready"; me: Me };

function BookingCard({ booking, me }: { booking: BookingView; me: Me }) {
  const pending = booking.status === "in_attesa_pagamento";
  return (
    <section aria-label={`Iscrizione ${statusLabel(booking.status)}`} className="card">
      <h2>{statusLabel(booking.status)}</h2>
      <ul>
        {booking.slots.map((slot) => (
          <li key={slot.label}>{slot.label}</li>
        ))}
      </ul>
      <p>
        Quota: <strong>{formatEuro(booking.amount_due_cents)}</strong>
        <br />
        Versato: <strong>{formatEuro(booking.paid_cents)}</strong>
        <br />
        {booking.balance_cents > 0 && (
          <>
            Ancora da versare: <strong>{formatEuro(booking.balance_cents)}</strong>
          </>
        )}
        {booking.balance_cents < 0 && (
          <>
            Versato in più: <strong>{formatEuro(-booking.balance_cents)}</strong>
          </>
        )}
        {booking.balance_cents === 0 && "Saldo a posto."}
      </p>
      {pending && (
        <>
          <p>
            Il posto è bloccato fino al <strong>{formatDeadline(booking.hold_expires_at)}</strong>.
            Causale: <strong>{me.personal_code}</strong>
          </p>
          <ul>
            {me.payment_channels.map((channel) => (
              <li key={channel.code}>
                <strong>{channel.label}</strong>
                <br />
                <span className="legal">{channel.instructions}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      {booking.status === "scaduta" && (
        <p>
          Il blocco è scaduto e i posti sono stati liberati.{" "}
          <Link to="/iscrizione">Iscriviti di nuovo</Link>
        </p>
      )}
      {booking.payments.length > 0 && (
        <details>
          <summary>Pagamenti registrati</summary>
          <ul>
            {booking.payments.map((payment, index) => (
              <li key={index}>
                {formatEuro(payment.amount_cents)} il {formatDay(payment.paid_on)} (
                {payment.channel})
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function PasswordForm({ hasPassword }: { hasPassword: boolean }) {
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const password = String(new FormData(form).get("password") ?? "");
    try {
      await api("/api/me/password", { method: "PUT", json: { password } });
      form.reset();
      setMessage({ ok: true, text: "Password salvata." });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : "Riprova tra poco.",
      });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="pw-title">
      <h2 id="pw-title">{hasPassword ? "Cambia password" : "Imposta una password"}</h2>
      <p>Facoltativa: il link via email funziona sempre.</p>
      <label>
        Nuova password (almeno 10 caratteri)
        <input
          type="password"
          name="password"
          minLength={10}
          autoComplete="new-password"
          required
        />
      </label>
      <button type="submit">Salva password</button>
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`notice ${message.ok ? "ok" : "error"}`}
        >
          {message.text}
        </p>
      )}
    </form>
  );
}

export function Personal() {
  const [state, setState] = useState<State>({ status: "loading" });
  const navigate = useNavigate();

  useEffect(() => {
    api<Me>("/api/me")
      .then((me) => setState({ status: "ready", me }))
      .catch(() => setState({ status: "anonymous" }));
  }, []);

  if (state.status === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state.status === "anonymous") return <Navigate to="/accedi" replace />;
  const { me } = state;

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate("/accedi");
  }

  return (
    <main>
      <h1>Ciao {me.first_name}!</h1>
      {me.role === "admin" && (
        <p>
          <Link to="/admin">Vai al pannello organizzatori</Link>
        </p>
      )}
      {me.bookings.length === 0 ? (
        <p>
          Non hai ancora un&apos;iscrizione. <Link to="/iscrizione">Iscriviti al camp</Link>
        </p>
      ) : (
        me.bookings.map((booking) => <BookingCard key={booking.id} booking={booking} me={me} />)
      )}
      <PasswordForm hasPassword={me.has_password} />
      <button type="button" onClick={logout}>
        Esci
      </button>
    </main>
  );
}
