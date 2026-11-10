import { useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { StatusBadge } from "../StatusBadge";
import { formatEuro } from "../money";
import { useT } from "../i18n";
import type { Detail } from "./AdminRegistrationDetail";

type Category = "ordinary" | "internal_non_paying";
type Preview = {
  preview_token: string;
  status_before: string;
  status_after: string;
  registration_fee_before_cents: number | null;
  registration_fee_after_cents: number;
  amount_due_before_cents: number;
  amount_due_after_cents: number;
  paid_cents: number;
  balance_before_cents: number;
  balance_after_cents: number;
};

const mealKey = (date: string, kind: string) => `${date}:${kind}`;

/**
 * Category and exemptions of one active booking. The category is a label and changes no amount;
 * the exempted items are worth zero and the others stay due. Nothing is saved until the admin
 * applies a preview that is still valid, and the payments are never touched.
 */
export function AdminExemptions({
  booking,
  category,
  onDone,
}: {
  booking: BookingView;
  category: Category;
  onDone: (detail: Detail, text: string) => void;
}) {
  const t = useT();
  const meals = (booking.meals ?? []).filter((m) => m.payment_mode !== "provider");
  const activities = (booking.activities ?? []).filter((a) => a.payment_mode !== "provider");
  const [chosenCategory, setChosenCategory] = useState<Category>(category);
  const [feeExempt, setFeeExempt] = useState(booking.fee_exempt ?? false);
  const [exemptMeals, setExemptMeals] = useState<Set<string>>(
    new Set(meals.filter((m) => m.exempt).map((m) => mealKey(m.date, m.kind))),
  );
  const [exemptActivities, setExemptActivities] = useState<Set<number>>(
    new Set(activities.filter((a) => a.exempt).map((a) => a.id)),
  );
  const [preview, setPreview] = useState<Preview | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payload = () => ({
    category: chosenCategory,
    fee_exempt: feeExempt,
    meals: [...exemptMeals].map((key) => {
      const [date, kind] = key.split(":");
      return { date, kind };
    }),
    activity_ids: [...exemptActivities],
  });

  // Any change to the choices makes the previous preview obsolete.
  function changed(action: () => void) {
    action();
    setPreview(null);
    setError(null);
  }

  function toggle<T>(set: Set<T>, setter: (next: Set<T>) => void, value: T, on: boolean) {
    changed(() => {
      const next = new Set(set);
      if (on) next.add(value);
      else next.delete(value);
      setter(next);
    });
  }

  async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
    setWorking(true);
    setError(null);
    try {
      return await action();
    } catch (caught) {
      setPreview(null);
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setWorking(false);
    }
  }

  async function saveCategory() {
    const detail = await run(() =>
      api<Detail>(`/api/admin/registrations/${booking.id}/category`, {
        method: "PUT",
        json: { category: chosenCategory },
      }),
    );
    if (detail) onDone(detail, t("exempt.categorySaved"));
  }

  async function makePreview() {
    const result = await run(() =>
      api<Preview>(`/api/admin/registrations/${booking.id}/exemptions/preview`, {
        method: "POST",
        json: payload(),
      }),
    );
    if (result) setPreview(result);
  }

  async function apply() {
    if (!preview) return;
    const detail = await run(() =>
      api<Detail>(`/api/admin/registrations/${booking.id}/exemptions/apply`, {
        method: "POST",
        json: { ...payload(), preview_token: preview.preview_token },
      }),
    );
    if (detail) {
      setPreview(null);
      onDone(detail, t("exempt.applied"));
    }
  }

  return (
    <section aria-labelledby="exempt-title">
      <h2 id="exempt-title">{t("exempt.title")}</h2>
      <p className="legal">{t("exempt.intro")}</p>
      <label>
        {t("exempt.category")}
        <select
          value={chosenCategory}
          onChange={(event) => changed(() => setChosenCategory(event.target.value as Category))}
        >
          <option value="ordinary">{t("exempt.categoryOrdinary")}</option>
          <option value="internal_non_paying">{t("exempt.categoryInternal")}</option>
        </select>
      </label>
      {chosenCategory === "internal_non_paying" && !feeExempt && (
        <p className="legal">{t("exempt.suggestFee")}</p>
      )}
      <p>
        <button
          type="button"
          className="secondary"
          disabled={working || chosenCategory === category}
          onClick={() => void saveCategory()}
        >
          {t("exempt.saveCategory")}
        </button>
      </p>
      <fieldset>
        <legend>{t("exempt.items")}</legend>
        <label className="check">
          <input
            type="checkbox"
            checked={feeExempt}
            onChange={(event) => changed(() => setFeeExempt(event.target.checked))}
          />
          {t("exempt.fee")}
        </label>
        {meals.map((meal) => {
          const key = mealKey(meal.date, meal.kind);
          return (
            <label className="check" key={key}>
              <input
                type="checkbox"
                checked={exemptMeals.has(key)}
                onChange={(event) => toggle(exemptMeals, setExemptMeals, key, event.target.checked)}
              />
              {meal.label}
            </label>
          );
        })}
        {activities.map((activity) => (
          <label className="check" key={activity.id}>
            <input
              type="checkbox"
              checked={exemptActivities.has(activity.id)}
              onChange={(event) =>
                toggle(exemptActivities, setExemptActivities, activity.id, event.target.checked)
              }
            />
            {activity.label}
          </label>
        ))}
      </fieldset>
      <p className="legal">{t("exempt.lostIfRemoved")}</p>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <p>
        <button type="button" disabled={working} onClick={() => void makePreview()}>
          {t("exempt.preview")}
        </button>
      </p>
      {preview && (
        <div className="table-wrap">
          <table>
            <caption>{t("exempt.previewCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("rep.colEntry")}</th>
                <th scope="col">{t("exempt.before")}</th>
                <th scope="col">{t("exempt.after")}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">{t("money.registrationFee")}</th>
                <td>
                  {preview.registration_fee_before_cents == null
                    ? "-"
                    : formatEuro(preview.registration_fee_before_cents)}
                </td>
                <td>{formatEuro(preview.registration_fee_after_cents)}</td>
              </tr>
              <tr>
                <th scope="row">{t("money.totalDue")}</th>
                <td>{formatEuro(preview.amount_due_before_cents)}</td>
                <td>{formatEuro(preview.amount_due_after_cents)}</td>
              </tr>
              <tr>
                <th scope="row">{t("people.colPaid")}</th>
                <td>{formatEuro(preview.paid_cents)}</td>
                <td>{formatEuro(preview.paid_cents)}</td>
              </tr>
              <tr>
                <th scope="row">{t("people.colBalance")}</th>
                <td>{formatEuro(preview.balance_before_cents)}</td>
                <td>{formatEuro(preview.balance_after_cents)}</td>
              </tr>
              <tr>
                <th scope="row">{t("people.colStatus")}</th>
                <td>
                  <StatusBadge status={preview.status_before} />
                </td>
                <td>
                  <StatusBadge status={preview.status_after} />
                </td>
              </tr>
            </tbody>
          </table>
          <p>
            <button type="button" disabled={working} onClick={() => void apply()}>
              {t("exempt.apply")}
            </button>
          </p>
        </div>
      )}
    </section>
  );
}
