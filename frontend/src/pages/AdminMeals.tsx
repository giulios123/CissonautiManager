import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDay } from "../booking";
import { useT, type MessageKey } from "../i18n";
import { tNow } from "../i18n/messages";
import { adminGuestPath, adminRegistrationPath } from "../routes";
import { CsvButton } from "./CsvButton";
import { CollectionDetails, CollectionFields, type CollectionTerms } from "../collection";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";

type MealPerson = {
  // A participant has a booking; an external guest has a guest id.
  booking_id: number | null;
  guest_id?: number | null;
  external?: boolean;
  first_name: string;
  last_name: string;
  diet: string | null;
  allergies: string | null;
  included_in_fee?: boolean;
  exempt?: boolean;
  collectable_cents: number;
};
type Meal = CollectionTerms & {
  kind: "lunch" | "dinner";
  count: number;
  diets: Record<string, number>;
  people: MealPerson[];
};
type MealDay = { date: string; meals: Meal[] };

const KIND = { lunch: "meals.kindLunch", dinner: "meals.kindDinner" } as const;
const DIETS: [string, MessageKey][] = [
  ["omnivore", "meals.dietOmnivore"],
  ["vegetarian", "meals.dietVegetarian"],
  ["vegan", "meals.dietVegan"],
  ["none", "meals.dietNone"],
];

const personKey = (person: MealPerson) =>
  person.external ? `g${person.guest_id}` : `b${person.booking_id}`;
const personPath = (person: MealPerson) =>
  person.external ? adminGuestPath(person.guest_id!) : adminRegistrationPath(person.booking_id!);

export const healthDataWarning = () => tNow("meals.healthWarning");

function dietSummary(diets: Record<string, number>) {
  return DIETS.filter(([key]) => diets[key])
    .map(([key, label]) => `${diets[key]} ${tNow(label)}`)
    .join(", ");
}

export function AdminMeals() {
  const t = useT();
  const [days, setDays] = useState<MealDay[] | null>(null);
  const [failed, setFailed] = useState(false);

  const load = useCallback(
    () =>
      api<{ days: MealDay[] }>("/api/admin/views/meals")
        .then((data) => setDays(data.days))
        .catch(() => setFailed(true)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main className="wide">
      <h1>{t("meals.title")}</h1>
      <p>{t("meals.intro")}</p>
      {failed && <p role="alert">{t("slots.loadError")}</p>}
      {days === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : days.length === 0 ? (
        <p>{t("week.noDays")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/meals" warning={healthDataWarning()} />
          </p>
          {days.map((day) => (
            <div className="table-wrap" key={day.date}>
              <table>
                <caption>{formatDay(day.date)}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("meals.colMeal")}</th>
                    <th scope="col">{t("slots.colPeople")}</th>
                    <th scope="col">{t("meals.colDiets")}</th>
                    <th scope="col">{t("meals.colWho")}</th>
                    <th scope="col">{t("meals.colAllergies")}</th>
                    <th scope="col">{t("collection.who")}</th>
                  </tr>
                </thead>
                <tbody>
                  {day.meals.map((meal) => {
                    const allergic = meal.people.filter((p) => p.allergies);
                    return (
                      <tr key={meal.kind}>
                        <th scope="row">{t(KIND[meal.kind])}</th>
                        <td>{meal.count}</td>
                        <td>{meal.count === 0 ? "-" : dietSummary(meal.diets)}</td>
                        <td>
                          {meal.people.length === 0 ? (
                            "-"
                          ) : (
                            <ul className="plain">
                              {meal.people.map((person) => (
                                <li key={personKey(person)}>
                                  <Link to={personPath(person)}>
                                    {person.first_name} {person.last_name}
                                  </Link>
                                  {person.external && <small> · {t("guests.badge")}</small>}
                                  {person.exempt && <small> · {t("collection.exempt")}</small>}
                                  {person.included_in_fee && (
                                    <small> · {t("collection.included")}</small>
                                  )}
                                </li>
                              ))}
                            </ul>
                          )}
                        </td>
                        <td>
                          {allergic.length === 0 ? (
                            "-"
                          ) : (
                            <ul className="plain">
                              {allergic.map((person) => (
                                <li key={personKey(person)}>
                                  {person.first_name} {person.last_name}: {person.allergies}
                                </li>
                              ))}
                            </ul>
                          )}
                        </td>
                        <td>
                          {meal.price_cents !== undefined && formatEuro(meal.price_cents)}
                          <CollectionDetails terms={meal} />
                          <MealPaymentEditor
                            key={`${day.date}:${meal.kind}:${meal.payment_mode}:${meal.price_cents}`}
                            day={day.date}
                            meal={meal}
                            onSaved={load}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ))}
        </>
      )}
    </main>
  );
}

function MealPaymentEditor({
  day,
  meal,
  onSaved,
}: {
  day: string;
  meal: Meal;
  onSaved: () => Promise<void>;
}) {
  const t = useT();
  const [mode, setMode] = useState<"organizer" | "provider">(meal.payment_mode ?? "organizer");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const price = mode === "provider" ? parseEuroToCents(String(data.get("price"))) : null;
    if (mode === "provider" && price === null) {
      setError(t("aact.priceInvalid"));
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await api(`/api/admin/meals/${day}/${meal.kind}`, {
        method: "PUT",
        json: {
          payment_mode: mode,
          price_cents: price,
          payment_instructions:
            mode === "provider" ? String(data.get("payment_instructions")).trim() : null,
        },
      });
      setSaved(true);
      await onSaved();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setSaving(false);
    }
  }
  return (
    <details>
      <summary>{t("collection.configure")}</summary>
      <form onSubmit={save} aria-label={`${formatDay(day)} ${t(KIND[meal.kind])}`}>
        <CollectionFields mode={mode} onChange={setMode} instructions={meal.payment_instructions} />
        {mode === "provider" && (
          <label>
            {t("aact.price")}
            <input
              name="price"
              required
              inputMode="decimal"
              defaultValue={centsToInput(meal.price_cents ?? 0)}
            />
          </label>
        )}
        {meal.count > 0 && <p>{t("collection.repriceWarning")}</p>}
        {error && <p role="alert">{error}</p>}
        {saved && <p role="status">{t("collection.saved")}</p>}
        <button disabled={saving} type="submit">
          {t("collection.save")}
        </button>
      </form>
    </details>
  );
}
