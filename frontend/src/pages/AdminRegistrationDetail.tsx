import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDay, formatDeadline } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { type ActivityOffer, type BookingView } from "../auth";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";
import { AdminCancelBooking, type AdminCancelResult } from "./AdminCancelBooking";
import { AdminEditDetails } from "./AdminEditDetails";
import { AdminHistory, type HistoryEntry } from "./AdminHistory";
import { AdminHoldActions } from "./AdminHoldActions";
import { AdminPayments } from "./AdminPayments";
import { AdminRefundForm } from "./AdminRefundForm";
import { AdminSlotEditor } from "./AdminSlotEditor";
import { ActivityPicker } from "./ActivityPicker";
import { MealEditor } from "./MealEditor";
import { PlusOneToggle } from "./PlusOneToggle";

export type Detail = {
  participant: {
    id?: number;
    plus_one_verified_at?: string | null;
    plus_one_verified_by?: string | null;
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
  refund: { amount_cents: number; refunded_on: string | null; note: string | null } | null;
  history: HistoryEntry[];
  warning: string | null;
  // Only in the response to a new payment: the payment that request created.
  payment_id?: number | null;
  waitlist?: { id: number; label: string; position: number; created_at: string }[];
  lunch_price_cents?: number;
  dinner_price_cents?: number;
  activity_offers?: ActivityOffer[];
};

const DIET_LABELS: Record<string, string> = {
  omnivore: "onnivoro",
  vegetarian: "vegetariano",
  vegan: "vegano",
};

const CHANNELS = [
  ["revolut", "Revolut"],
  ["satispay", "Satispay"],
  ["paypal", "PayPal"],
  ["iban", "Bonifico (IBAN)"],
] as const;

export function AdminRegistrationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [editingSlots, setEditingSlots] = useState(false);
  const [editingMeals, setEditingMeals] = useState(false);
  const [editingActivities, setEditingActivities] = useState(false);
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

  function afterCancel(result: AdminCancelResult) {
    if (result.outcome === "removed" || !result.detail) {
      navigate("/admin", {
        state: {
          notice: `Iscrizione di ${participant.first_name} ${participant.last_name} disdetta e rimossa.`,
        },
      });
      return;
    }
    showUpdated(
      result.detail,
      "Disdetta registrata: i posti sono liberi e la persona è stata avvisata.",
    );
  }

  function reload() {
    api<Detail>(`/api/admin/registrations/${id}`)
      .then(setDetail)
      .catch(() => setNotice({ ok: false, text: "Non riesco ad aggiornare la scheda." }));
  }

  function showUpdated(updated: Detail, text: string) {
    setDetail(updated);
    setNotice({ ok: true, text });
  }

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
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
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
          {participant.id !== undefined && (
            <>
              <dt>Invitato</dt>
              <dd>
                <PlusOneToggle
                  participantId={participant.id}
                  invitedBy={participant.invited_by}
                  verified={Boolean(participant.plus_one_verified_at)}
                  verifiedAt={participant.plus_one_verified_at ?? null}
                  verifiedBy={participant.plus_one_verified_by ?? null}
                  onChanged={reload}
                />
              </dd>
            </>
          )}
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
        <h2 id="booking">
          Iscrizione: <StatusBadge status={booking.status} />
        </h2>
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
        <AdminPayments bookingId={booking.id} payments={booking.payments} onDone={showUpdated} />
      </section>

      <section aria-labelledby="meals-title">
        <h2 id="meals-title">Pasti ed esigenze alimentari</h2>
        {(booking.meals ?? []).length === 0 ? (
          <p>Nessun pasto.</p>
        ) : (
          <ul>
            {(booking.meals ?? []).map((meal) => (
              <li key={`${meal.date}:${meal.kind}`}>{meal.label}</li>
            ))}
          </ul>
        )}
        <p>
          Regime: {booking.diet ? DIET_LABELS[booking.diet] : "non indicato"}.
          <br />
          Allergie e intolleranze: {booking.allergies ?? "nessuna indicata"}
          {booking.health_consent_version != null &&
            ` (consenso versione ${booking.health_consent_version})`}
          .
        </p>
        {booking.editable && (
          <button
            type="button"
            className="secondary"
            aria-expanded={editingMeals}
            onClick={() => setEditingMeals((value) => !value)}
          >
            {editingMeals ? "Chiudi la modifica dei pasti" : "Cambia i pasti"}
          </button>
        )}
        {editingMeals && booking.editable && (
          <MealEditor<Detail>
            booking={booking}
            lunchCents={detail.lunch_price_cents ?? 0}
            dinnerCents={detail.dinner_price_cents ?? 0}
            path={`/api/admin/registrations/${booking.id}/meals`}
            allowPast
            onSaved={(updated) => showUpdated(updated, "Pasti aggiornati.")}
          />
        )}
      </section>

      <section aria-labelledby="activities-title">
        <h2 id="activities-title">Attività</h2>
        {(booking.activities ?? []).length === 0 ? (
          <p>Nessuna attività.</p>
        ) : (
          <ul>
            {(booking.activities ?? []).map((activity) => (
              <li key={activity.id}>
                <Link to={`/admin/attivita/${activity.id}`}>{activity.label}</Link>
              </li>
            ))}
          </ul>
        )}
        {booking.editable && (
          <button
            type="button"
            className="secondary"
            aria-expanded={editingActivities}
            onClick={() => setEditingActivities((value) => !value)}
          >
            {editingActivities ? "Chiudi la modifica delle attività" : "Cambia le attività"}
          </button>
        )}
        {editingActivities && booking.editable && (
          <ActivityPicker<Detail>
            booking={booking}
            offers={detail.activity_offers ?? []}
            path={`/api/admin/registrations/${booking.id}/activities`}
            admin
            onSaved={(updated) => showUpdated(updated, "Attività aggiornate.")}
          />
        )}
      </section>

      {(booking.editable || booking.can_cancel) && (
        <section aria-labelledby="actions-title">
          <h2 id="actions-title">Azioni sull&apos;iscrizione</h2>
          <div className="actions">
            {booking.editable && (
              <button
                type="button"
                className="secondary"
                aria-expanded={editingSlots}
                onClick={() => setEditingSlots((value) => !value)}
              >
                {editingSlots ? "Chiudi la modifica degli slot" : "Cambia gli slot"}
              </button>
            )}
            {booking.can_cancel && (
              <AdminCancelBooking bookingId={booking.id} booking={booking} onDone={afterCancel} />
            )}
          </div>
          {editingSlots && booking.editable && (
            <AdminSlotEditor
              bookingId={booking.id}
              booking={booking}
              onDone={(updated, text) => {
                showUpdated(updated, text);
              }}
            />
          )}
        </section>
      )}

      <AdminHoldActions
        bookingId={booking.id}
        status={booking.status}
        holdExpiresAt={booking.hold_expires_at}
        onDone={showUpdated}
      />

      {detail.refund && (
        <p className="notice ok">
          Rimborsati {formatEuro(detail.refund.amount_cents)}
          {detail.refund.refunded_on && <> il {formatDay(detail.refund.refunded_on)}</>}
          {detail.refund.note ? ` (${detail.refund.note})` : ""}.
        </p>
      )}
      {booking.status === "disdetta_richiesta" && (
        <AdminRefundForm
          bookingId={booking.id}
          paidCents={booking.paid_cents}
          onDone={(updated) => {
            setDetail(updated);
            setNotice({
              ok: true,
              text: "Disdetta chiusa. Ricorda di scrivere tu alla persona.",
            });
          }}
        />
      )}

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
      </form>

      <AdminEditDetails bookingId={booking.id} participant={participant} onDone={showUpdated} />

      {(detail.waitlist ?? []).length > 0 && (
        <section aria-labelledby="waitlist-title">
          <h2 id="waitlist-title">Lista d&apos;attesa</h2>
          <ul>
            {(detail.waitlist ?? []).map((item) => (
              <li key={item.id}>
                {item.label}: {item.position}° in lista
              </li>
            ))}
          </ul>
          <p>
            Per togliere la persona da una lista usa <Link to="/admin/giorni">Giorni e slot</Link>.
          </p>
        </section>
      )}
      <AdminHistory history={detail.history ?? []} />
    </main>
  );
}
