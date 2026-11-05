import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { type BookingView, type Me } from "../auth";
import { formatDay, formatDeadline, statusLabel } from "../booking";
import { useT, type MessageKey } from "../i18n";
import { formatEuro } from "../money";
import { ROUTES } from "../routes";
import { StatusBadge } from "../StatusBadge";
import { CancelBooking, type CancelOutcome } from "./CancelBooking";
import { ActivityPicker } from "./ActivityPicker";
import { Contributions } from "./Contributions";
import { DietaryForm } from "./DietaryForm";
import { MealEditor } from "./MealEditor";
import { SlotEditor } from "./SlotEditor";
import { Waitlist } from "./Waitlist";

type State = { status: "loading" } | { status: "anonymous" } | { status: "ready"; me: Me };

function PaymentInstructions({ me }: { me: Me }) {
  const t = useT();
  return (
    <>
      <p>
        {t("me.reference")} <strong>{me.personal_code}</strong>
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
  const t = useT();
  const [editing, setEditing] = useState(false);
  const [editingMeals, setEditingMeals] = useState(false);
  const [editingActivities, setEditingActivities] = useState(false);
  const activities = booking.activities ?? [];
  const meals = booking.meals ?? [];
  const pending = booking.status === "in_attesa_pagamento";
  const confirmedWithBalance = booking.status === "confermata" && booking.balance_cents > 0;
  return (
    <section
      aria-label={t("me.sectionLabel", { status: statusLabel(booking.status) })}
      className="card"
    >
      <h2>
        <StatusBadge status={booking.status} />
      </h2>
      <ul>
        {booking.slots.map((slot) => (
          <li key={slot.label}>{slot.label}</li>
        ))}
      </ul>
      <p>
        {t("me.fee")} <strong>{formatEuro(booking.amount_due_cents)}</strong>
        <br />
        {t("me.paid")} <strong>{formatEuro(booking.paid_cents)}</strong>
        <br />
        {booking.balance_cents > 0 && (
          <>
            {t("me.toPay")} <strong>{formatEuro(booking.balance_cents)}</strong>
          </>
        )}
        {booking.balance_cents < 0 && (
          <>
            {t("me.overpaid")} <strong>{formatEuro(-booking.balance_cents)}</strong>
          </>
        )}
        {booking.balance_cents === 0 && t("me.settled")}
      </p>
      {pending && (
        <>
          <p>
            {t("me.holdBefore")} <strong>{formatDeadline(booking.hold_expires_at)}</strong>.
          </p>
          <PaymentInstructions me={me} />
        </>
      )}
      {confirmedWithBalance && (
        <>
          <p>{t("me.changedSlots")}</p>
          <PaymentInstructions me={me} />
        </>
      )}
      {booking.status === "scaduta" && (
        <p>
          {t("me.expired")} <Link to={ROUTES.register}>{t("me.signUpAgain")}</Link>
        </p>
      )}
      {booking.status === "disdetta_richiesta" && <p>{t("me.cancelRequested")}</p>}
      {booking.status === "rimborsata" && (
        <p>
          {t("me.refunded")} <Link to={ROUTES.register}>{t("me.signUpAgain")}</Link>
        </p>
      )}
      {(booking.editable || meals.length > 0) && (
        <section aria-labelledby={`meals-${booking.id}`}>
          <h3 id={`meals-${booking.id}`}>{t("me.meals")}</h3>
          {meals.length === 0 ? (
            <p>{t("me.noMeals")}</p>
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
              {editingMeals ? t("me.closeMeals") : t("me.chooseMeals")}
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
      {(booking.editable || activities.length > 0) && (
        <section aria-labelledby={`activities-${booking.id}`}>
          <h3 id={`activities-${booking.id}`}>{t("me.activities")}</h3>
          {activities.length === 0 ? (
            <p>{t("me.noActivities")}</p>
          ) : (
            <ul>
              {activities.map((activity) => (
                <li key={activity.id}>{activity.label}</li>
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
              {editingActivities ? t("me.closeActivities") : t("me.chooseActivities")}
            </button>
          )}
          {editingActivities && booking.editable && (
            <ActivityPicker booking={booking} offers={me.activities ?? []} onSaved={reload} />
          )}
        </section>
      )}
      {booking.editable && <DietaryForm booking={booking} me={me} onSaved={reload} />}
      {booking.payments.length > 0 && (
        <details>
          <summary>{t("me.payments")}</summary>
          <ul>
            {booking.payments.map((payment, index) => (
              <li key={index}>
                {t("me.paymentLine", {
                  amount: formatEuro(payment.amount_cents),
                  date: formatDay(payment.paid_on),
                  channel: payment.channel,
                })}
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
              {editing ? t("me.closeEdit") : t("me.editSlots")}
            </button>
          )}
          {booking.can_cancel && <CancelBooking booking={booking} onDone={onCancelled} />}
        </div>
      )}
      {editing && booking.editable && (
        <SlotEditor
          booking={booking}
          onSaved={reload}
          extras={{
            meals: booking.meals ?? [],
            activities: (me.activities ?? []).filter((offer) => offer.joined),
            lunchCents: me.lunch_price_cents ?? 0,
            dinnerCents: me.dinner_price_cents ?? 0,
          }}
        />
      )}
    </section>
  );
}

function PasswordForm({ hasPassword }: { hasPassword: boolean }) {
  const t = useT();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const password = String(new FormData(form).get("password") ?? "");
    try {
      await api("/api/me/password", { method: "PUT", json: { password } });
      form.reset();
      setMessage({ ok: true, text: t("me.passwordSaved") });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : t("common.retryShortly"),
      });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="pw-title">
      <h2 id="pw-title">{hasPassword ? t("me.changePassword") : t("me.setPassword")}</h2>
      <p>{t("me.passwordOptional")}</p>
      <label>
        {t("me.newPassword")}
        <input
          type="password"
          name="password"
          minLength={10}
          autoComplete="new-password"
          required
        />
      </label>
      <button type="submit">{t("me.savePassword")}</button>
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

const CANCEL_NOTICES: Record<CancelOutcome, MessageKey> = {
  removed: "me.cancelRemoved",
  requested: "me.cancelRequestedNotice",
};

export function Personal() {
  const t = useT();
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

  if (state.status === "loading") return <main aria-busy="true">{t("common.loading")}</main>;
  if (state.status === "anonymous") return <Navigate to={ROUTES.login} replace />;
  const { me } = state;

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate(ROUTES.login);
  }

  async function onCancelled(outcome: CancelOutcome) {
    setNotice(t(CANCEL_NOTICES[outcome]));
    await reload();
  }

  return (
    <main>
      <h1>{t("me.hello", { name: me.first_name })}</h1>
      {notice && (
        <p role="status" className="notice ok">
          {notice}
        </p>
      )}
      {me.role === "admin" && (
        <p>
          <Link to={ROUTES.admin}>{t("me.toAdmin")}</Link>
        </p>
      )}
      {me.bookings.length === 0
        ? (me.waitlist ?? []).length === 0 && (
            <p>
              {t("me.noRegistration")} <Link to={ROUTES.register}>{t("home.register")}</Link>
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
      {me.bookings.some((b) => b.editable) && <Contributions me={me} editable reload={reload} />}
      <Waitlist me={me} reload={reload} />
      <PasswordForm hasPassword={me.has_password} />
      <p>
        <Link to={ROUTES.guide}>{t("me.guide")}</Link>
      </p>
      <button type="button" className="secondary" onClick={logout}>
        {t("me.logout")}
      </button>
    </main>
  );
}
