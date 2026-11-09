import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView, MealView } from "../auth";
import { formatDay } from "../booking";
import { useT } from "../i18n";
import { formatEuro } from "../money";
import { CollectionDetails } from "../collection";

const key = (meal: { date: string; kind: string }) => `${meal.date}:${meal.kind}`;
const KIND_LABELS = { lunch: "meal.lunch", dinner: "meal.dinner" } as const;
const NO_MEALS: MealView[] = [];

type MealPreview = {
  registration_fee_cents: number;
  amount_due_cents: number;
  included_meals: [string, string][];
};

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
  const [previewState, setPreviewState] = useState<{
    signature: string;
    value: MealPreview;
  } | null>(null);
  const [previewError, setPreviewError] = useState<{ signature: string; value: string } | null>(
    null,
  );
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const allowed = booking.allowed_meals ?? NO_MEALS;
  const days = [...new Set(allowed.map((meal) => meal.date))];
  const selectedMeals = allowed
    .filter((meal) => selected.has(key(meal)))
    .map(({ date, kind }) => ({ date, kind }));
  const signature = JSON.stringify(selectedMeals);
  const preview = previewState?.signature === signature ? previewState.value : null;
  const fee = preview?.amount_due_cents ?? booking.amount_due_cents;
  const delta = fee - booking.amount_due_cents;
  const feePolicy = booking.confirmation_policy === "registration_fee";
  const included = new Set(preview?.included_meals?.map(([day, kind]) => `${day}:${kind}`) ?? []);
  const changed = selected.size !== original.size || [...selected].some((k) => !original.has(k));
  const displayedError =
    error ?? (previewError?.signature === signature ? previewError.value : null);

  useEffect(() => {
    let current = true;
    const meals = JSON.parse(signature) as { date: string; kind: string }[];
    void api<MealPreview>(`${path}/preview`, { method: "POST", json: { meals } })
      .then((result) => {
        if (current) setPreviewState({ signature, value: result });
      })
      .catch((caught) => {
        if (current)
          setPreviewError({
            signature,
            value: caught instanceof ApiError ? caught.message : t("common.somethingWrong"),
          });
      });
    return () => {
      current = false;
    };
  }, [path, signature, t]);

  function toggle(meal: MealView, checked: boolean) {
    setSaved(false);
    setError(null);
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
                  <CollectionDetails
                    terms={{
                      ...meal,
                      included_in_fee: preview ? included.has(key(meal)) : meal.included_in_fee,
                    }}
                  />
                  {meal.past && !allowPast ? ` · ${t("edit.pastDay")}` : ""}
                </span>
              </label>
            ))}
        </fieldset>
      ))}
      <p aria-live="polite" className="fee">
        {feePolicy && booking.registration_fee_cents != null && (
          <>
            {t("money.registrationFee")}{" "}
            <strong>{formatEuro(booking.registration_fee_cents)}</strong>
            <br />
          </>
        )}
        {feePolicy ? t("edit.newTotal") : t("edit.newFee")}{" "}
        {preview ? <strong>{formatEuro(fee)}</strong> : t("meal.previewLoading")}
        {delta !== 0 && (
          <>
            {" "}
            {t(delta > 0 ? "edit.delta.more" : "edit.delta.less", {
              amount: formatEuro(Math.abs(delta)),
            })}
          </>
        )}
      </p>
      {displayedError && (
        <p role="alert" className="notice error">
          {displayedError}
        </p>
      )}
      {saved && (
        <p role="status" className="notice ok">
          {t("meal.updated")}
        </p>
      )}
      <button type="submit" disabled={!changed || saving || !preview}>
        {t("meal.save")}
      </button>
    </form>
  );
}
