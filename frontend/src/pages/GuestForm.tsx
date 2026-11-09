import { useState, type FormEvent } from "react";
import { ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { type GuestInput } from "../guests";
import { useT } from "../i18n";

const text = (value: string) => (value.trim() === "" ? null : value);

/**
 * Identity, diet and allergies of an external guest. The server answers 409 when someone with the
 * same name is already in the edition: the admin then confirms it is another person.
 */
export function GuestForm({
  initial,
  submitLabel,
  onSubmit,
}: {
  initial: GuestInput;
  submitLabel: string;
  onSubmit: (input: GuestInput) => Promise<void>;
}) {
  const t = useT();
  const [value, setValue] = useState<GuestInput>(initial);
  const [error, setError] = useState<string | null>(null);
  const [duplicate, setDuplicate] = useState<string | null>(null);
  const [working, setWorking] = useState(false);

  function set<K extends keyof GuestInput>(key: K, next: GuestInput[K]) {
    setValue((current) => ({ ...current, [key]: next }));
  }

  async function send(confirmDuplicate: boolean) {
    setError(null);
    setWorking(true);
    try {
      await onSubmit({
        ...value,
        allergies: value.allergies_consent ? text(value.allergies ?? "") : null,
        ...(confirmDuplicate ? { confirm_duplicate: true } : {}),
      });
      setDuplicate(null);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409 && !confirmDuplicate) {
        setDuplicate(caught.message);
      } else {
        setDuplicate(null);
        setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
      }
    } finally {
      setWorking(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send(false);
  }

  return (
    <form onSubmit={submit}>
      <label>
        {t("guests.first")}
        <input
          required
          maxLength={100}
          value={value.first_name}
          onChange={(event) => set("first_name", event.target.value)}
        />
      </label>
      <label>
        {t("guests.last")}
        <input
          required
          maxLength={100}
          value={value.last_name}
          onChange={(event) => set("last_name", event.target.value)}
        />
      </label>
      <label>
        {t("guests.payer")}
        <select
          value={value.payer}
          onChange={(event) => set("payer", event.target.value as GuestInput["payer"])}
        >
          <option value="paying">{t("guests.payerPaying")}</option>
          <option value="non_paying">{t("guests.payerNon")}</option>
        </select>
      </label>
      <label>
        {t("guests.phone")}
        <input
          type="tel"
          maxLength={50}
          value={value.phone ?? ""}
          onChange={(event) => set("phone", text(event.target.value))}
        />
      </label>
      <label>
        {t("guests.reference")}
        <input
          maxLength={200}
          value={value.reference ?? ""}
          onChange={(event) => set("reference", text(event.target.value))}
        />
      </label>
      <label>
        {t("guests.diet")}
        <select
          value={value.diet ?? ""}
          onChange={(event) => set("diet", (event.target.value || null) as GuestInput["diet"])}
        >
          <option value="">{t("meals.dietNone")}</option>
          <option value="omnivore">{t("meals.dietOmnivore")}</option>
          <option value="vegetarian">{t("meals.dietVegetarian")}</option>
          <option value="vegan">{t("meals.dietVegan")}</option>
        </select>
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={value.allergies_consent}
          onChange={(event) => set("allergies_consent", event.target.checked)}
        />
        {t("guests.consent")}
      </label>
      <p className="legal">{t("guests.consentHint")}</p>
      {value.allergies_consent && (
        <label>
          {t("guests.allergies")}
          <textarea
            rows={3}
            maxLength={2000}
            value={value.allergies ?? ""}
            onChange={(event) => set("allergies", event.target.value)}
          />
        </label>
      )}
      <label>
        {t("guests.note")}
        <textarea
          rows={3}
          maxLength={5000}
          value={value.internal_note ?? ""}
          onChange={(event) => set("internal_note", text(event.target.value))}
        />
      </label>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <button type="submit" disabled={working}>
        {submitLabel}
      </button>
      {duplicate && (
        <ConfirmDialog
          title={t("guests.duplicateTitle")}
          confirmLabel={t("guests.duplicateConfirm")}
          working={working}
          onConfirm={() => void send(true)}
          onCancel={() => setDuplicate(null)}
        >
          <p>{duplicate}</p>
        </ConfirmDialog>
      )}
    </form>
  );
}
