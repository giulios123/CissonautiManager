import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatDay } from "../booking";
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

const KIND = { lunch: "Pranzo", dinner: "Cena" } as const;
const DIETS: [string, string][] = [
  ["omnivore", "onnivori"],
  ["vegetarian", "vegetariani"],
  ["vegan", "vegani"],
  ["none", "senza indicazione"],
];

export const HEALTH_DATA_WARNING =
  "Il file contiene allergie e intolleranze, che sono dati sanitari: conservalo con cura e non condividerlo. Vuoi scaricarlo?";

function dietSummary(diets: Record<string, number>) {
  return DIETS.filter(([key]) => diets[key])
    .map(([key, label]) => `${diets[key]} ${label}`)
    .join(", ");
}

export function AdminMeals() {
  const [days, setDays] = useState<MealDay[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<{ days: MealDay[] }>("/api/admin/views/meals")
      .then((data) => setDays(data.days))
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide">
      <h1>Pasti</h1>
      <p>
        Chi mangia a ogni pranzo e cena, con regime e allergie. Allergie e intolleranze sono dati
        sanitari: le vedono solo gli organizzatori.
      </p>
      {failed && <p role="alert">Non riesco a caricare la vista.</p>}
      {days === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : days.length === 0 ? (
        <p>Nessun giorno: configura prima l&apos;edizione nelle Impostazioni.</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/meals" warning={HEALTH_DATA_WARNING} />
          </p>
          {days.map((day) => (
            <div className="table-wrap" key={day.date}>
              <table>
                <caption>{formatDay(day.date)}</caption>
                <thead>
                  <tr>
                    <th scope="col">Pasto</th>
                    <th scope="col">Persone</th>
                    <th scope="col">Regimi</th>
                    <th scope="col">Chi c&apos;è</th>
                    <th scope="col">Allergie e intolleranze</th>
                  </tr>
                </thead>
                <tbody>
                  {day.meals.map((meal) => {
                    const allergic = meal.people.filter((p) => p.allergies);
                    return (
                      <tr key={meal.kind}>
                        <th scope="row">{KIND[meal.kind]}</th>
                        <td>{meal.count}</td>
                        <td>{meal.count === 0 ? "-" : dietSummary(meal.diets)}</td>
                        <td>
                          {meal.people.length === 0 ? (
                            "-"
                          ) : (
                            <ul className="plain">
                              {meal.people.map((person) => (
                                <li key={person.booking_id}>
                                  <Link to={`/admin/iscrizioni/${person.booking_id}`}>
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
