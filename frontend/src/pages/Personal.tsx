import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { type BookingView, type Me } from "../auth";
import { formatDay, formatDeadline, statusLabel } from "../booking";
import { periodLabel } from "../booking";
import { getLocale } from "../i18n/locale";
import { translatePlural } from "../i18n/messages";
import { useI18n, type MessageKey } from "../i18n";
import { formatEuro } from "../money";
import { ROUTES } from "../routes";
import { StatusBadge } from "../StatusBadge";
import { CollectionDetails } from "../collection";
import { PresenceSummary } from "../PresenceSummary";
import { ConsentPanel } from "../consents";
import { PrivacyAcceptancePanel } from "../privacy";
import { CancelBooking, type CancelOutcome } from "./CancelBooking";
import { ActivityPicker } from "./ActivityPicker";
import { Contributions } from "./Contributions";
import { DietaryForm } from "./DietaryForm";
import { MealEditor } from "./MealEditor";
import { SlotEditor } from "./SlotEditor";
import { Waitlist } from "./Waitlist";

function ProfileCompletion() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [municipalities, setMunicipalities] = useState<
    Array<{ name: string; province: string; region: string; istat_code: string }>
  >([]);
  const [countries, setCountries] = useState<Array<{ code: string; name: string }>>([]);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    void api<Record<string, unknown>>("/api/me/profile")
      .then((data) => {
        const annual =
          typeof data.profile === "object" && data.profile !== null
            ? (data.profile as Record<string, unknown>)
            : {};
        setProfile({ ...data, ...annual });
        setOpen(data.complete !== true);
      })
      .catch(() => setProfile(null));
  }, []);
  useEffect(() => {
    void api<Array<{ code: string; name: string }>>("/api/public/countries")
      .then((items) => setCountries(Array.isArray(items) ? items : []))
      .catch(() => setCountries([]));
  }, []);
  useEffect(() => {
    const city = String(profile?.city ?? "").trim();
    if (city.length < 2) {
      return;
    }
    const timer = window.setTimeout(() => {
      void api<Array<{ name: string; province: string; region: string; istat_code: string }>>(
        `/api/public/municipalities?q=${encodeURIComponent(city)}`,
      )
        .then((items) => setMunicipalities(Array.isArray(items) ? items : []))
        .catch(() => setMunicipalities([]));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [profile?.city]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const val = (key: string) => String(form.get(key) ?? "").trim();
    try {
      await api("/api/me/profile", {
        method: "PUT",
        json: {
          phone: val("phone"),
          telegram: val("telegram"),
          linkedin: val("linkedin"),
          city: val("city"),
          province: val("province") || null,
          region: val("region") || null,
          country: val("country"),
          istat_code: val("istat_code") || null,
          job_title: val("job_title"),
          company: val("company"),
          expectations: val("expectations"),
          attended_previous: val("attended_previous") === "yes",
        },
      });
      setMessage(t("profile.saved"));
      setOpen(false);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : t("common.somethingWrong"));
    }
  }
  if (!profile || (profile.complete === true && !open)) return null;
  const missingLabels: Record<string, MessageKey> = {
    phone: "reg.phone",
    telegram: "profile.telegram",
    linkedin: "profile.linkedin",
    city: "profile.city",
    province: "profile.province",
    country: "profile.country",
    job_title: "profile.jobTitle",
    company: "profile.company",
    expectations: "profile.expectations",
    attended_previous: "profile.previous",
  };
  const missingFields = Array.isArray(profile.missing_fields)
    ? (profile.missing_fields as string[]).map((name) => t(missingLabels[name] ?? "profile.city"))
    : [];
  return (
    <section className="card" aria-labelledby="profile-title">
      <h2 id="profile-title">{t("profile.incomplete")}</h2>
      {missingFields.length > 0 && (
        <p>{t("profile.missing", { fields: missingFields.join(", ") })}</p>
      )}
      {open ? (
        <form onSubmit={submit}>
          {(
            [
              ["phone", "reg.phone"],
              ["telegram", "profile.telegram"],
              ["linkedin", "profile.linkedin"],
              ["city", "profile.city"],
              ["province", "profile.province"],
              ["region", "profile.region"],
              ["country", "profile.country"],
              ["istat_code", "profile.istatCode"],
              ["job_title", "profile.jobTitle"],
              ["company", "profile.company"],
              ["expectations", "profile.expectations"],
            ] as const
          ).map(([name, label]) => (
            <label key={name}>
              {t(label)}
              <input
                name={name}
                required={
                  !["region", "istat_code"].includes(name) &&
                  (name !== "province" ||
                    (["italia", "italy"].includes(String(profile.country ?? "").toLowerCase()) &&
                      !profile.istat_code))
                }
                defaultValue={
                  ["city", "province", "region", "istat_code", "country"].includes(name)
                    ? undefined
                    : String(profile[name] ?? "")
                }
                list={
                  name === "city"
                    ? "profile-municipality-options"
                    : name === "country"
                      ? "profile-country-options"
                      : undefined
                }
                {...(["city", "province", "region", "istat_code", "country"].includes(name)
                  ? {
                      value: String(profile[name] ?? ""),
                      onChange: (event: ChangeEvent<HTMLInputElement>) => {
                        const value = event.currentTarget.value;
                        if (name === "country") {
                          setProfile({
                            ...profile,
                            country: value,
                            province: "",
                            region: "",
                            istat_code: "",
                          });
                          return;
                        }
                        if (name !== "city") {
                          setProfile({ ...profile, [name]: value });
                          return;
                        }
                        const match = municipalities.find(
                          (item) => `${item.name} — ${item.province}` === value,
                        );
                        setProfile({
                          ...profile,
                          city: match?.name ?? value,
                          province: match?.province ?? "",
                          region: match?.region ?? "",
                          istat_code: match?.istat_code ?? "",
                        });
                      },
                    }
                  : {})}
              />
            </label>
          ))}
          <datalist id="profile-municipality-options">
            {String(profile.city ?? "").trim().length >= 2 &&
              municipalities.map((item, index) => (
                <option
                  key={`${item.name}-${item.province}-${index}`}
                  value={`${item.name} — ${item.province}`}
                  label={item.region}
                />
              ))}
          </datalist>
          <datalist id="profile-country-options">
            {countries.map((item) => (
              <option key={item.code} value={item.name} />
            ))}
          </datalist>
          <label>
            {t("profile.previous")}
            <select
              name="attended_previous"
              required
              defaultValue={
                typeof profile.attended_previous === "boolean"
                  ? profile.attended_previous
                    ? "yes"
                    : "no"
                  : ""
              }
            >
              <option value="" disabled>
                {t("profile.choose")}
              </option>
              <option value="yes">{t("common.yes")}</option>
              <option value="no">{t("common.no")}</option>
            </select>
          </label>
          <button type="submit">{t("profile.save")}</button>
        </form>
      ) : (
        <button type="button" onClick={() => setOpen(true)}>
          {t("profile.save")}
        </button>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}

type State = { status: "loading" } | { status: "anonymous" } | { status: "ready"; me: Me };

function PaymentInstructions({ me }: { me: Me }) {
  const { t } = useI18n();
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
  privacyRequired,
}: {
  booking: BookingView;
  me: Me;
  reload: () => Promise<void>;
  onCancelled: (outcome: CancelOutcome) => Promise<void>;
  privacyRequired: boolean;
}) {
  const { t } = useI18n();
  const [editing, setEditing] = useState(false);
  const [editingMeals, setEditingMeals] = useState(false);
  const [editingActivities, setEditingActivities] = useState(false);
  const activities = booking.activities ?? [];
  const meals = booking.meals ?? [];
  const pending = booking.status === "in_attesa_pagamento";
  const feePolicy = booking.confirmation_policy === "registration_fee";
  const confirmedWithBalance = booking.status === "confermata" && booking.balance_cents > 0;
  return (
    <section
      aria-label={t("me.sectionLabel", { status: statusLabel(booking.status) })}
      className="card"
    >
      <h2>
        <StatusBadge status={booking.status} />
      </h2>
      <p>
        {feePolicy && booking.registration_fee_cents != null && (
          <>
            {t("money.registrationFee")}{" "}
            <strong>{formatEuro(booking.registration_fee_cents)}</strong>
            <br />
          </>
        )}
        {feePolicy ? t("money.totalDue") : t("me.fee")}{" "}
        <strong>{formatEuro(booking.amount_due_cents)}</strong>
        {feePolicy && pending && booking.confirmation_balance_cents != null && (
          <>
            <br />
            {t("money.confirmationDue")}{" "}
            <strong>{formatEuro(booking.confirmation_balance_cents)}</strong>
          </>
        )}
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
      <PresenceSummary slots={booking.slots} schedule={booking.schedule} />
      {booking.editable && (
        <button
          type="button"
          className="secondary"
          aria-expanded={editing}
          disabled={privacyRequired}
          onClick={() => setEditing((value) => !value)}
        >
          {privacyRequired
            ? t("privacy.blocked")
            : editing
              ? t("me.closeEdit")
              : t("me.editPresences")}
        </button>
      )}
      {pending && (
        <>
          <p>
            {t("me.holdBefore")} <strong>{formatDeadline(booking.hold_expires_at)}</strong>.
          </p>
          <PaymentInstructions me={me} />
          {feePolicy && <p className="legal">{t("money.extrasLater")}</p>}
        </>
      )}
      {confirmedWithBalance && (
        <>
          <p>{feePolicy ? t("money.confirmed") : t("me.changedSlots")}</p>
          <PaymentInstructions me={me} />
          {feePolicy && <p className="legal">{t("money.extrasLater")}</p>}
        </>
      )}
      {feePolicy && booking.status === "confermata" && !confirmedWithBalance && (
        <p className="legal">{t("money.confirmed")}</p>
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
                <li key={`${meal.date}:${meal.kind}`}>
                  {meal.label}
                  <CollectionDetails terms={meal} />
                </li>
              ))}
            </ul>
          )}
          {booking.editable && (
            <button
              type="button"
              className="secondary"
              aria-expanded={editingMeals}
              disabled={privacyRequired}
              onClick={() => setEditingMeals((value) => !value)}
            >
              {privacyRequired
                ? t("privacy.blocked")
                : editingMeals
                  ? t("me.closeMeals")
                  : t("me.chooseMeals")}
            </button>
          )}
          {editingMeals && booking.editable && !privacyRequired && (
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
              {activities.map((activity) => {
                const offer = me.activities?.find((item) => item.id === activity.id);
                return (
                  <li key={activity.id}>
                    {activity.label}
                    {activity.time_label && ` (${activity.time_label})`}
                    <details>
                      <summary>{t("act.details")}</summary>
                      {activity.description && <p>{activity.description}</p>}
                      <p>
                        {formatDay(activity.date)} · {periodLabel(activity.period)}
                        {activity.start_time &&
                          activity.end_time &&
                          ` · ${activity.start_time}–${activity.end_time}`}
                      </p>
                      <p>
                        {formatEuro(activity.price_cents)} · {t("collection.who")}:{" "}
                        {t(
                          activity.payment_mode === "provider"
                            ? "collection.provider"
                            : "collection.organizer",
                        )}
                      </p>
                      {offer?.capacity !== null && offer?.capacity !== undefined && (
                        <p>
                          {offer.free === null
                            ? t("act.unlimited")
                            : translatePlural(getLocale(), "seats.free", offer.free)}
                        </p>
                      )}
                      <CollectionDetails terms={activity} />
                    </details>
                  </li>
                );
              })}
            </ul>
          )}
          {booking.editable && (
            <button
              type="button"
              className="secondary"
              aria-expanded={editingActivities}
              disabled={privacyRequired}
              onClick={() => setEditingActivities((value) => !value)}
            >
              {privacyRequired
                ? t("privacy.blocked")
                : editingActivities
                  ? t("me.closeActivities")
                  : t("me.chooseActivities")}
            </button>
          )}
          {editingActivities && booking.editable && !privacyRequired && (
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
          {booking.can_cancel && <CancelBooking booking={booking} onDone={onCancelled} />}
        </div>
      )}
      {editing && booking.editable && !privacyRequired && (
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
  const { t } = useI18n();
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
  const { t, locale } = useI18n();
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

  // The labels of slots, meals and activities come from the server in the language of the
  // request: when the language changes, ask again.
  useEffect(() => {
    void reload();
  }, [reload, locale]);

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
        <p className="admin-bar">
          <Link to={ROUTES.admin} className="button secondary">
            {t("me.toAdmin")}
          </Link>
        </p>
      )}
      <ProfileCompletion />
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
              privacyRequired={Boolean(me.privacy_acceptance_required)}
            />
          ))}
      {me.privacy_associated && <PrivacyAcceptancePanel onRefresh={reload} />}
      {me.bookings.some((b) => b.editable) && (
        <Contributions
          me={me}
          editable={!me.privacy_acceptance_required}
          readOnly={Boolean(me.privacy_acceptance_required)}
          reload={reload}
        />
      )}
      <Waitlist me={me} reload={reload} privacyRequired={Boolean(me.privacy_acceptance_required)} />
      <ConsentPanel />
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
