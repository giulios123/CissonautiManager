import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView, MealView } from "../auth";
import { formatDay } from "../booking";
import { useT } from "../i18n";
import { formatEuro } from "../money";
import { collectableCents, CollectionDetails } from "../collection";

const key = (meal: { date: string; kind: string }) => `${meal.date}:${meal.kind}`;
const KIND_LABELS = { lunch: "meal.lunch", dinner: "meal.dinner" } as const;

/** New amount: the current one, minus the meals given up, plus the meals added. */
export function mealsPreview(
  booking: BookingView,
  selected: Set<string>,
  lunchCents: number,
  dinnerCents: number,
): number {
  const price = (meal: MealView) =>
    meal.price_cents !== undefined
      ? collectableCents(meal)
      : meal.kind === "lunch"
        ? lunchCents
        : dinnerCents;
  const current = booking.meals ?? [];
  const before = current.reduce((sum, meal) => sum + price(meal), 0);
  const after = (booking.allowed_meals ?? [])
    .filter((meal) => selected.has(key(meal)))
    .reduce((sum, meal) => sum + price(meal), 0);
  return booking.amount_due_cents - before + after;
}

export function MealEditor<T = unknown>({
  booking,
  lunchCents,
  dinnerCents,
  onSaved,
  path = "/api/me/booking/meals",
  allowPast = false,
}: {
  booking: BookingView;
  lunchCents: number;
  dinnerCents: number;
  onSaved: (result: T) => Promise<void> | void;
  // Admins save through their own endpoint and can change days already over.
  path?: string;
  allowPast?: boolean;
}) {
  const t = useT();
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
      const result = await api<T>(path, { method: "PUT", json: { meals } });
      await onSaved(result);
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setSaving(false);
    }
  }

  if (allowed.length === 0) return <p>{t("meal.chooseSlotFirst")}</p>;

  return (
    <form onSubmit={save} aria-label={t("me.chooseMeals")}>
      <p className="legal">
        {t("meal.prices", { lunch: formatEuro(lunchCents), dinner: formatEuro(dinnerCents) })}
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
                  disabled={Boolean(meal.past) && !allowPast}
                  onChange={(e) => toggle(meal, e.target.checked)}
                />
                <span>
                  {t(KIND_LABELS[meal.kind])}
                  {meal.price_cents !== undefined && ` · ${formatEuro(meal.price_cents)}`}
                  <CollectionDetails terms={meal} />
                  {meal.past && !allowPast ? ` · ${t("edit.pastDay")}` : ""}
                </span>
              </label>
            ))}
        </fieldset>
      ))}
      <p aria-live="polite" className="fee">
        {t("edit.newFee")} <strong>{formatEuro(fee)}</strong>
        {delta !== 0 && (
          <>
            {" "}
            {t(delta > 0 ? "edit.delta.more" : "edit.delta.less", {
              amount: formatEuro(Math.abs(delta)),
            })}
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
          {t("meal.updated")}
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        {t("meal.save")}
      </button>
    </form>
  );
}
