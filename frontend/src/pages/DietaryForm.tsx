import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView, Me } from "../auth";

const DIETS = [
  ["", "Non indicato"],
  ["omnivore", "Onnivoro"],
  ["vegetarian", "Vegetariano"],
  ["vegan", "Vegano"],
] as const;

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
        text: "Per salvare allergie e intolleranze spunta il consenso al trattamento dei dati sanitari.",
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
      setMessage({ ok: true, text: "Esigenze alimentari salvate." });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : "Qualcosa è andato storto. Riprova.",
      });
    }
  }

  return (
    <form onSubmit={save} aria-labelledby={`diet-${booking.id}`}>
      <h3 id={`diet-${booking.id}`}>Esigenze alimentari</h3>
      <p className="legal">Le vedono solo gli organizzatori.</p>
      <label>
        Regime alimentare
        <select value={diet} onChange={(e) => setDiet(e.target.value)}>
          {DIETS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {consentText ? (
        <>
          <label>
            Allergie e intolleranze
            <textarea
              rows={2}
              maxLength={2000}
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
            />
          </label>
          <details>
            <summary>Leggi il consenso per i dati sanitari</summary>
            <p className="legal">{consentText.body}</p>
          </details>
          <label className="check">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            Acconsento al trattamento dei miei dati sanitari (allergie e intolleranze)
          </label>
          {textChanged && (
            <p className="legal">
              Il testo del consenso è cambiato: rileggilo e spunta di nuovo per mantenere le
              allergie.
            </p>
          )}
          {!consent && hadConsent && (
            <p className="legal">Salvando senza consenso le allergie vengono cancellate.</p>
          )}
        </>
      ) : (
        <p>Per indicare allergie e intolleranze scrivi a chi organizza.</p>
      )}
      <button type="submit">Salva esigenze alimentari</button>
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
