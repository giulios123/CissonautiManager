import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { CollectionDetails, type CollectionTerms } from "../collection";
import { ConfirmDialog } from "../ConfirmDialog";
import { guestInput, type Guest, type GuestInput } from "../guests";
import { useT, type MessageKey } from "../i18n";
import { ROUTES } from "../routes";
import { GuestForm } from "./GuestForm";

type MealDay = {
  date: string;
  meals: (CollectionTerms & { kind: "lunch" | "dinner" })[];
};

const KIND: Record<"lunch" | "dinner", MessageKey> = {
  lunch: "meals.kindLunch",
  dinner: "meals.kindDinner",
};
const mealKey = (date: string, kind: string) => `${date}:${kind}`;

/** One external guest: details, meals, activities. */
export function AdminGuestDetail() {
  const t = useT();
  const navigate = useNavigate();
  const { id } = useParams();
  const [guest, setGuest] = useState<Guest | null>(null);
  const [days, setDays] = useState<MealDay[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [failed, setFailed] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const deleteButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    Promise.all([
      api<Guest>(`/api/admin/guests/${id}`),
      api<{ days: MealDay[] }>("/api/admin/views/meals"),
      api<Activity[]>("/api/admin/activities"),
    ])
      .then(([loaded, meals, list]) => {
        setGuest(loaded);
        setDays(meals.days);
        setActivities(list);
      })
      .catch(() => setFailed(true));
  }, [id]);

  if (failed) return <main role="alert">{t("guests.notFound")}</main>;
  if (!guest) return <main aria-busy="true">{t("common.loading")}</main>;

  async function reloadActivities() {
    setActivities(await api<Activity[]>("/api/admin/activities"));
  }

  async function saveDetails(input: GuestInput) {
    setGuest(await api<Guest>(`/api/admin/guests/${id}`, { method: "PATCH", json: input }));
  }

  async function remove() {
    await api(`/api/admin/guests/${id}`, { method: "DELETE" });
    navigate(ROUTES.adminGuests);
  }

  return (
    <main className="wide">
      <p>
        <Link to={ROUTES.adminGuests}>{t("guests.back")}</Link>
      </p>
      <h1>
        {guest.first_name} {guest.last_name} <small>({t("guests.badge")})</small>
      </h1>
      <GuestForm
        initial={guestInput(guest)}
        submitLabel={t("guests.save")}
        onSubmit={saveDetails}
      />
      <MealsForm
        guestId={guest.id}
        days={days}
        selected={guest.meals.map((m) => mealKey(m.date, m.kind))}
        onSaved={setGuest}
      />
      <ActivitiesForm
        guestId={guest.id}
        activities={activities}
        selected={guest.activities.map((a) => a.id)}
        onSaved={async (updated) => {
          setGuest(updated);
          await reloadActivities();
        }}
      />
      <p>
        <button
          ref={deleteButton}
          type="button"
          className="secondary"
          onClick={() => setDeleting(true)}
        >
          {t("guests.delete")}
        </button>
      </p>
      {deleting && (
        <ConfirmDialog
          title={t("guests.deleteTitle", { name: `${guest.first_name} ${guest.last_name}` })}
          confirmLabel={t("guests.deleteConfirm")}
          onConfirm={() => void remove()}
          onCancel={() => setDeleting(false)}
          returnFocusTo={deleteButton}
        >
          <p>{t("guests.deleteBody")}</p>
        </ConfirmDialog>
      )}
    </main>
  );
}

function MealsForm({
  guestId,
  days,
  selected,
  onSaved,
}: {
  guestId: number;
  days: MealDay[];
  selected: string[];
  onSaved: (guest: Guest) => void;
}) {
  const t = useT();
  const [chosen, setChosen] = useState<Set<string>>(new Set(selected));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function toggle(key: string, checked: boolean) {
    setSaved(false);
    setChosen((current) => {
      const next = new Set(current);
      if (checked) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      const meals = [...chosen].map((key) => {
        const [date, kind] = key.split(":");
        return { date, kind };
      });
      onSaved(
        await api<Guest>(`/api/admin/guests/${guestId}/meals`, { method: "PUT", json: { meals } }),
      );
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    }
  }

  return (
    <form onSubmit={save} aria-labelledby="guest-meals">
      <h2 id="guest-meals">{t("guests.mealsTitle")}</h2>
      <p className="legal">{t("guests.mealsHint")}</p>
      {days.map((day) =>
        day.meals.map((meal) => {
          const key = mealKey(day.date, meal.kind);
          return (
            <label className="check" key={key}>
              <input
                type="checkbox"
                checked={chosen.has(key)}
                onChange={(event) => toggle(key, event.target.checked)}
              />
              <span>
                {formatDay(day.date)} · {t(KIND[meal.kind])}
                <CollectionDetails terms={meal} />
              </span>
            </label>
          );
        }),
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          {t("guests.saved")}
        </p>
      )}
      <button type="submit">{t("guests.saveMeals")}</button>
    </form>
  );
}

function ActivitiesForm({
  guestId,
  activities,
  selected,
  onSaved,
}: {
  guestId: number;
  activities: Activity[];
  selected: number[];
  onSaved: (guest: Guest) => Promise<void>;
}) {
  const t = useT();
  const [chosen, setChosen] = useState<Set<number>>(new Set(selected));
  const [force, setForce] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function toggle(activityId: number, checked: boolean) {
    setSaved(false);
    setChosen((current) => {
      const next = new Set(current);
      if (checked) next.add(activityId);
      else next.delete(activityId);
      return next;
    });
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setWarning(null);
    try {
      const updated = await api<Guest>(`/api/admin/guests/${guestId}/activities`, {
        method: "PUT",
        json: { activity_ids: [...chosen], force },
      });
      setWarning(updated.warning ?? null);
      await onSaved(updated);
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    }
  }

  return (
    <form onSubmit={save} aria-labelledby="guest-activities">
      <h2 id="guest-activities">{t("guests.activitiesTitle")}</h2>
      {activities.length === 0 && <p>{t("guests.activitiesNone")}</p>}
      {activities.map((activity) => (
        <label className="check" key={activity.id}>
          <input
            type="checkbox"
            checked={chosen.has(activity.id)}
            onChange={(event) => toggle(activity.id, event.target.checked)}
          />
          <span>
            <strong>{activity.title}</strong>, {formatDay(activity.date)}{" "}
            {periodLabel(activity.period).toLowerCase()} · {priceLabel(activity.price_cents)} ·{" "}
            {seatsLabel(activity)}
          </span>
        </label>
      ))}
      {activities.length > 0 && (
        <label className="check">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
          {t("act.force")}
        </label>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {warning && (
        <p role="status" className="notice">
          {warning}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          {t("guests.saved")}
        </p>
      )}
      <button type="submit" disabled={activities.length === 0}>
        {t("guests.saveActivities")}
      </button>
    </form>
  );
}
