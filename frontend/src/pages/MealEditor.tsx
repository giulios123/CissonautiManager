import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView, MealView } from "../auth";
import { formatDay } from "../booking";
import { formatEuro } from "../money";

const key = (meal: { date: string; kind: string }) => `${meal.date}:${meal.kind}`;
const KIND_LABELS = { lunch: "Pranzo", dinner: "Cena" } as const;

/** New amount: the current one, minus the meals given up, plus the meals added. */
export function mealsPreview(
  booking: BookingView,
  selected: Set<string>,
  lunchCents: number,
  dinnerCents: number,
): number {
  const price = (kind: string) => (kind === "lunch" ? lunchCents : dinnerCents);
  const current = booking.meals ?? [];
  const before = current.reduce((sum, meal) => sum + price(meal.kind), 0);
  const after = (booking.allowed_meals ?? [])
    .filter((meal) => selected.has(key(meal)))
    .reduce((sum, meal) => sum + price(meal.kind), 0);
  return booking.amount_due_cents - before + after;
}

export function MealEditor({
  booking,
  lunchCents,
  dinnerCents,
  onSaved,
}: {
  booking: BookingView;
  lunchCents: number;
  dinnerCents: number;
  onSaved: () => Promise<void> | void;
}) {
  const original = new Set((booking.meals ?? []).map(key));
  const [selected, setSelected] = useState<Set<string>>(new Set(original));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const allowed = booking.allowed_meals ?? [];
  const days = [...new Set(allowed.map((meal) => meal.date))];
  const fee = mealsPreview(booking, selected, lunchCents, dinnerCents);
  const delta = fee - booking.amount_due_cents;
  const changed = selected.size !== original.size || [...selected].some((k) => !original.has(k));

  function toggle(meal: MealView, checked: boolean) {
    setSaved(false);
    setSelected((current) => {
      const next = new Set(current);
      if (checked) next.add(key(meal));
      else next.delete(key(meal));
      return next;
    });
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const meals = allowed
        .filter((meal) => selected.has(key(meal)))
        .map(({ date, kind }) => ({ date, kind }));
      await api("/api/me/booking/meals", { method: "PUT", json: { meals } });
      await onSaved();
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
    } finally {
      setSaving(false);
    }
  }

  if (allowed.length === 0) return <p>Scegli prima almeno uno slot per poter aderire ai pasti.</p>;

  return (
    <form onSubmit={save} aria-label="Scegli pranzi e cene">
      <p className="legal">
        Pranzo {formatEuro(lunchCents)}, cena {formatEuro(dinnerCents)}. Il pranzo si sceglie nei
        giorni in cui ci sei di mattina o di pomeriggio, la cena quando ci sei la sera.
      </p>
      {days.map((day) => (
        <fieldset key={day}>
          <legend>{formatDay(day)}</legend>
          {allowed
            .filter((meal) => meal.date === day)
            .map((meal) => (
              <label className="check" key={key(meal)}>
                <input
                  type="checkbox"
                  checked={selected.has(key(meal))}
                  disabled={Boolean(meal.past)}
                  onChange={(e) => toggle(meal, e.target.checked)}
                />
                <span>
                  {KIND_LABELS[meal.kind]}
                  {meal.past ? " · giorno passato" : ""}
                </span>
              </label>
            ))}
        </fieldset>
      ))}
      <p aria-live="polite" className="fee">
        Nuova quota: <strong>{formatEuro(fee)}</strong>
        {delta !== 0 && (
          <>
            {" "}
            ({formatEuro(Math.abs(delta))} {delta > 0 ? "in più" : "in meno"} di ora)
          </>
        )}
      </p>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          Pasti aggiornati.
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        Salva i pasti
      </button>
    </form>
  );
}
