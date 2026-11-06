import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatDay } from "../booking";
import { useT, type MessageKey } from "../i18n";
import { tNow } from "../i18n/messages";
import { adminRegistrationPath } from "../routes";
import { CsvButton } from "./CsvButton";

type MealPerson = {
  booking_id: number;
  first_name: string;
  last_name: string;
  diet: string | null;
  allergies: string | null;
};
type Meal = {
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

  useEffect(() => {
    api<{ days: MealDay[] }>("/api/admin/views/meals")
      .then((data) => setDays(data.days))
      .catch(() => setFailed(true));
  }, []);

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
                                <li key={person.booking_id}>
                                  <Link to={adminRegistrationPath(person.booking_id)}>
                                    {person.first_name} {person.last_name}
                                  </Link>
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
                                <li key={person.booking_id}>
                                  {person.first_name} {person.last_name}: {person.allergies}
                                </li>
                              ))}
                            </ul>
                          )}
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
