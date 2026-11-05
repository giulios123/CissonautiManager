import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { type BookingView, type Me } from "../auth";
import { formatDay, formatDeadline, statusLabel } from "../booking";
import { formatEuro } from "../money";
import { CancelBooking, type CancelOutcome } from "./CancelBooking";
import { DietaryForm } from "./DietaryForm";
import { MealEditor } from "./MealEditor";
import { SlotEditor } from "./SlotEditor";
import { Waitlist } from "./Waitlist";

type State = { status: "loading" } | { status: "anonymous" } | { status: "ready"; me: Me };

function PaymentInstructions({ me }: { me: Me }) {
  return (
    <>
      <p>
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
  );
}

function BookingCard({
  booking,
  me,
  reload,
  onCancelled,
}: {
  booking: BookingView;
  me: Me;
  reload: () => Promise<void>;
  onCancelled: (outcome: CancelOutcome) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [editingMeals, setEditingMeals] = useState(false);
  const meals = booking.meals ?? [];
  const pending = booking.status === "in_attesa_pagamento";
  const confirmedWithBalance = booking.status === "confermata" && booking.balance_cents > 0;
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
          </p>
          <PaymentInstructions me={me} />
        </>
      )}
      {confirmedWithBalance && (
        <>
          <p>Hai cambiato gli slot: la differenza si versa con le stesse istruzioni.</p>
          <PaymentInstructions me={me} />
        </>
      )}
      {booking.status === "scaduta" && (
        <p>
          Il blocco è scaduto e i posti sono stati liberati.{" "}
          <Link to="/iscrizione">Iscriviti di nuovo</Link>
        </p>
      )}
      {booking.status === "disdetta_richiesta" && (
        <p>
          Hai chiesto la disdetta: i posti sono liberi e chi organizza ti scriverà per il rimborso.
        </p>
      )}
      {booking.status === "rimborsata" && (
        <p>
          La disdetta è conclusa e il rimborso è stato gestito.{" "}
          <Link to="/iscrizione">Iscriviti di nuovo</Link>
        </p>
      )}
      {(booking.editable || meals.length > 0) && (
        <section aria-labelledby={`meals-${booking.id}`}>
          <h3 id={`meals-${booking.id}`}>Pranzi e cene</h3>
          {meals.length === 0 ? (
            <p>Nessun pasto scelto.</p>
          ) : (
            <ul>
              {meals.map((meal) => (
                <li key={`${meal.date}:${meal.kind}`}>{meal.label}</li>
              ))}
            </ul>
          )}
          {booking.editable && (
            <button
              type="button"
              className="secondary"
              aria-expanded={editingMeals}
              onClick={() => setEditingMeals((value) => !value)}
            >
              {editingMeals ? "Chiudi i pasti" : "Scegli pranzi e cene"}
            </button>
          )}
          {editingMeals && booking.editable && (
            <MealEditor
              booking={booking}
              lunchCents={me.lunch_price_cents ?? 0}
              dinnerCents={me.dinner_price_cents ?? 0}
              onSaved={reload}
            />
          )}
        </section>
      )}
      {booking.editable && <DietaryForm booking={booking} me={me} onSaved={reload} />}
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
      {(booking.editable || booking.can_cancel) && (
        <div className="actions">
          {booking.editable && (
            <button
              type="button"
              className="secondary"
              aria-expanded={editing}
              onClick={() => setEditing((value) => !value)}
            >
              {editing ? "Chiudi la modifica" : "Cambia i tuoi slot"}
            </button>
          )}
          {booking.can_cancel && <CancelBooking booking={booking} onDone={onCancelled} />}
        </div>
      )}
      {editing && booking.editable && <SlotEditor booking={booking} onSaved={reload} />}
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

const CANCEL_NOTICES: Record<CancelOutcome, string> = {
  removed:
    "Disdetta registrata: l'iscrizione è annullata e i posti sono liberi. Ti abbiamo scritto una email.",
  requested:
    "Disdetta registrata: i posti sono liberi. Chi organizza ti scriverà per il rimborso. Ti abbiamo scritto una email.",
};

export function Personal() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [notice, setNotice] = useState<string | null>(null);
  const navigate = useNavigate();

  // Reloading keeps the current page on screen: only the data is replaced.
  const reload = useCallback(
    () =>
      api<Me>("/api/me")
        .then((me) => setState({ status: "ready", me }))
        .catch(() => setState({ status: "anonymous" })),
    [],
  );

  useEffect(() => {
    void reload();
  }, [reload]);

  if (state.status === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state.status === "anonymous") return <Navigate to="/accedi" replace />;
  const { me } = state;

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate("/accedi");
  }

  async function onCancelled(outcome: CancelOutcome) {
    setNotice(CANCEL_NOTICES[outcome]);
    await reload();
  }

  return (
    <main>
      <h1>Ciao {me.first_name}!</h1>
      {notice && (
        <p role="status" className="notice ok">
          {notice}
        </p>
      )}
      {me.role === "admin" && (
        <p>
          <Link to="/admin">Vai al pannello organizzatori</Link>
        </p>
      )}
      {me.bookings.length === 0
        ? (me.waitlist ?? []).length === 0 && (
            <p>
              Non hai ancora un&apos;iscrizione. <Link to="/iscrizione">Iscriviti al camp</Link>
            </p>
          )
        : me.bookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
              me={me}
              reload={reload}
              onCancelled={onCancelled}
            />
          ))}
      <Waitlist me={me} reload={reload} />
      <PasswordForm hasPassword={me.has_password} />
      <button type="button" onClick={logout}>
        Esci
      </button>
    </main>
  );
}
