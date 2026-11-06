import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView, Me } from "../auth";
import { useT, type MessageKey } from "../i18n";

const DIETS: readonly (readonly [string, MessageKey])[] = [
  ["", "diet.notSpecified"],
  ["omnivore", "diet.omnivore"],
  ["vegetarian", "diet.vegetarian"],
  ["vegan", "diet.vegan"],
];

/** Diet (no consent needed) and allergies (kept only with the specific health data consent). */
export function DietaryForm({
  booking,
  me,
  onSaved,
}: {
  booking: BookingView;
  me: Me;
  onSaved: () => Promise<void> | void;
}) {
  const t = useT();
  const [diet, setDiet] = useState(booking.diet ?? "");
  const [allergies, setAllergies] = useState(booking.allergies ?? "");
  const consentText = me.health_consent;
  const hadConsent = booking.health_consent_version != null;
  // A consent given to an older text does not count for the current one: it must be renewed.
  const textChanged = hadConsent && booking.health_consent_version !== consentText?.version;
  const [consent, setConsent] = useState(hadConsent && !textChanged);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    // Without consent, allergies can only be withdrawn (if they were given before), never added.
    if (allergies.trim() && !consent && !hadConsent) {
      setMessage({
        ok: false,
        text: t("diet.consentNeeded"),
      });
      return;
    }
    try {
      await api("/api/me/booking/dietary", {
        method: "PUT",
        json: {
          diet: diet || null,
          allergies: consent ? allergies : null,
          consent,
          consent_version: consent ? (consentText?.version ?? null) : null,
        },
      });
      if (!consent) setAllergies("");
      await onSaved();
      setMessage({ ok: true, text: t("diet.saved") });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : t("common.somethingWrong"),
      });
    }
  }

  return (
    <form onSubmit={save} aria-labelledby={`diet-${booking.id}`}>
      <h3 id={`diet-${booking.id}`}>{t("diet.title")}</h3>
      <p className="legal">{t("diet.onlyOrganizers")}</p>
      <label>
        {t("diet.regime")}
        <select value={diet} onChange={(e) => setDiet(e.target.value)}>
          {DIETS.map(([value, label]) => (
            <option key={value} value={value}>
              {t(label)}
            </option>
          ))}
        </select>
      </label>
      {consentText ? (
        <>
          <label>
            {t("diet.allergies")}
            <textarea
              rows={2}
              maxLength={2000}
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
            />
          </label>
          <details>
            <summary>{t("diet.readConsent")}</summary>
            <p className="legal">{consentText.body}</p>
          </details>
          <label className="check">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            {t("diet.consent")}
          </label>
          {textChanged && <p className="legal">{t("diet.consentChanged")}</p>}
          {!consent && hadConsent && <p className="legal">{t("diet.withdrawWarning")}</p>}
        </>
      ) : (
        <p>{t("diet.writeToOrganizers")}</p>
      )}
      <button type="submit">{t("diet.save")}</button>
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
