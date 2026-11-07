import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { CollectionDetails } from "../collection";
import { formatDay, formatDeadline } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { type ActivityOffer, type BookingView } from "../auth";
import { useT, type MessageKey } from "../i18n";
import { adminActivityPath, ROUTES } from "../routes";
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
import { PresenceSummary } from "../PresenceSummary";

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

const DIET_LABELS: Record<string, MessageKey> = {
  omnivore: "det.dietOmnivore",
  vegetarian: "det.dietVegetarian",
  vegan: "det.dietVegan",
};

const CHANNELS = [
  ["revolut", "channel.revolut"],
  ["satispay", "channel.satispay"],
  ["paypal", "channel.paypal"],
  ["iban", "channel.iban"],
] as const satisfies readonly (readonly [string, MessageKey])[];

export function AdminRegistrationDetail() {
  const t = useT();
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

  if (failed) return <main role="alert">{t("det.notFound")}</main>;
  if (!detail) return <main aria-busy="true">{t("common.loading")}</main>;

  const { participant, booking } = detail;

  function afterCancel(result: AdminCancelResult) {
    if (result.outcome === "removed" || !result.detail) {
      navigate(ROUTES.admin, {
        state: {
          notice: t("det.removedNotice", {
            name: `${participant.first_name} ${participant.last_name}`,
          }),
        },
      });
      return;
    }
    showUpdated(result.detail, t("det.cancelledNotice"));
  }

  function reload() {
    api<Detail>(`/api/admin/registrations/${id}`)
      .then(setDetail)
      .catch(() => setNotice({ ok: false, text: t("det.cannotRefresh") }));
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
      setNotice({ ok: false, text: t("det.amountInvalid") });
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
            ? t("det.paymentConfirmed")
            : t("det.paymentRecorded"),
      });
    } catch (error) {
      setNotice({ ok: false, text: error instanceof ApiError ? error.message : t("det.retry") });
    }
  }

  return (
    <main>
      <p>
        <Link to={ROUTES.admin}>{t("det.backAll")}</Link>
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
        <h2 id="who">{t("det.data")}</h2>
        <dl>
          <dt>{t("login.email")}</dt>
          <dd>{participant.email}</dd>
          <dt>{t("people.colPhone")}</dt>
          <dd>{participant.phone ?? "-"}</dd>
          <dt>{t("det.invitedBy")}</dt>
          <dd>{participant.invited_by ?? "-"}</dd>
          {participant.id !== undefined && (
            <>
              <dt>{t("det.invited")}</dt>
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
          <dt>{t("det.canBring")}</dt>
          <dd className="legal">{participant.can_bring ?? "-"}</dd>
          <dt>{t("det.reference")}</dt>
          <dd>{participant.personal_code}</dd>
          <dt>{t("det.privacyAccepted")}</dt>
          <dd>
            {t("det.version", {
              n: detail.privacy.version,
              when: formatDeadline(detail.privacy.accepted_at),
            })}
          </dd>
          <dt>{t("det.waiverAccepted")}</dt>
          <dd>
            {t("det.version", {
              n: detail.disclaimer.version,
              when: formatDeadline(detail.disclaimer.accepted_at),
            })}
          </dd>
        </dl>
      </section>

      <section aria-labelledby="booking">
        <h2 id="booking">
          {t("det.registration")} <StatusBadge status={booking.status} />
        </h2>
        <p>
          {t("det.due")} <strong>{formatEuro(booking.amount_due_cents)}</strong>,{" "}
          {t("det.paidLower")} <strong>{formatEuro(booking.paid_cents)}</strong>,{" "}
          {t("det.balanceLower")} <strong>{formatEuro(booking.balance_cents)}</strong>.
          {booking.status === "in_attesa_pagamento" && (
            <> {t("det.heldUntil", { date: formatDeadline(booking.hold_expires_at) })}</>
          )}
        </p>
        <PresenceSummary slots={booking.slots} schedule={booking.schedule} />
        <AdminPayments bookingId={booking.id} payments={booking.payments} onDone={showUpdated} />
      </section>

      <section aria-labelledby="meals-title">
        <h2 id="meals-title">{t("det.mealsTitle")}</h2>
        {(booking.meals ?? []).length === 0 ? (
          <p>{t("det.noMeals")}</p>
        ) : (
          <ul>
            {(booking.meals ?? []).map((meal) => (
              <li key={`${meal.date}:${meal.kind}`}>
                {meal.label}
                <CollectionDetails terms={meal} />
              </li>
            ))}
          </ul>
        )}
        <p>
          {t("det.diet", {
            diet: booking.diet ? t(DIET_LABELS[booking.diet]) : t("det.dietNotSpecified"),
          })}
          <br />
          {t("det.allergies", { text: booking.allergies ?? t("det.noneSpecified") })}
          {booking.health_consent_version != null &&
            t("det.consentVersion", { n: booking.health_consent_version })}
          .
        </p>
        {booking.editable && (
          <button
            type="button"
            className="secondary"
            aria-expanded={editingMeals}
            onClick={() => setEditingMeals((value) => !value)}
          >
            {editingMeals ? t("det.closeMealsEdit") : t("det.editMeals")}
          </button>
        )}
        {editingMeals && booking.editable && (
          <MealEditor<Detail>
            booking={booking}
            lunchCents={detail.lunch_price_cents ?? 0}
            dinnerCents={detail.dinner_price_cents ?? 0}
            path={`/api/admin/registrations/${booking.id}/meals`}
            allowPast
            onSaved={(updated) => showUpdated(updated, t("meal.updated"))}
          />
        )}
      </section>

      <section aria-labelledby="activities-title">
        <h2 id="activities-title">{t("me.activities")}</h2>
        {(booking.activities ?? []).length === 0 ? (
          <p>{t("det.noActivities")}</p>
        ) : (
          <ul>
            {(booking.activities ?? []).map((activity) => (
              <li key={activity.id}>
                <Link to={adminActivityPath(activity.id)}>{activity.label}</Link>
                {activity.time_label && ` (${activity.time_label})`}
                <CollectionDetails terms={activity} />
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
            {editingActivities ? t("det.closeActivitiesEdit") : t("det.editActivities")}
          </button>
        )}
        {editingActivities && booking.editable && (
          <ActivityPicker<Detail>
            booking={booking}
            offers={detail.activity_offers ?? []}
            path={`/api/admin/registrations/${booking.id}/activities`}
            admin
            onSaved={(updated) => showUpdated(updated, t("act.updated"))}
          />
        )}
      </section>

      {(booking.editable || booking.can_cancel) && (
        <section aria-labelledby="actions-title">
          <h2 id="actions-title">{t("det.actionsTitle")}</h2>
          <div className="actions">
            {booking.editable && (
              <button
                type="button"
                className="secondary"
                aria-expanded={editingSlots}
                onClick={() => setEditingSlots((value) => !value)}
              >
                {editingSlots ? t("det.closeSlotsEdit") : t("det.editSlots")}
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
          {t("det.refunded", { amount: formatEuro(detail.refund.amount_cents) })}
          {detail.refund.refunded_on &&
            t("det.refundedOn", { date: formatDay(detail.refund.refunded_on) })}
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
              text: t("det.cancellationClosed"),
            });
          }}
        />
      )}

      <form onSubmit={submit} aria-labelledby="pay-title">
        <h2 id="pay-title">{t("det.recordPayment")}</h2>
        <label>
          {t("det.amount")}
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
              {t("det.useBalance", { amount: formatEuro(booking.balance_cents) })}
            </button>
          </p>
        )}
        <label>
          {t("det.channel")}
          <select name="channel" defaultValue="iban">
            {CHANNELS.map(([code, label]) => (
              <option key={code} value={code}>
                {t(label)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("det.paidOn")}
          <input type="date" name="paid_on" />
        </label>
        <label>
          {t("det.note")}
          <input name="note" maxLength={1000} />
        </label>
        <button type="submit">{t("det.recordButton")}</button>
      </form>

      <AdminEditDetails bookingId={booking.id} participant={participant} onDone={showUpdated} />

      {(detail.waitlist ?? []).length > 0 && (
        <section aria-labelledby="waitlist-title">
          <h2 id="waitlist-title">{t("wl.title")}</h2>
          <ul>
            {(detail.waitlist ?? []).map((item) => (
              <li key={item.id}>
                {t("det.waitlistLine", { label: item.label, position: item.position })}
              </li>
            ))}
          </ul>
          <p>
            {t("det.removeFromListBefore")} <Link to={ROUTES.adminDays}>{t("slots.title")}</Link>.
          </p>
        </section>
      )}
      <AdminHistory history={detail.history ?? []} />
    </main>
  );
}
