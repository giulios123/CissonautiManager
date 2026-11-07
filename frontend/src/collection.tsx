import { useT } from "./i18n";
import { formatEuro } from "./money";

export type CollectionTerms = {
  price_cents?: number;
  payment_mode?: "organizer" | "provider";
  collectable_cents?: number;
  payment_instructions?: string | null;
};

export const collectableCents = (terms: CollectionTerms) =>
  terms.payment_mode === "provider" ? 0 : (terms.collectable_cents ?? terms.price_cents ?? 0);

export function CollectionDetails({ terms }: { terms: CollectionTerms }) {
  const t = useT();
  if (terms.payment_mode !== "provider") return null;
  return (
    <span className="legal">
      <br />
      <strong>{t("collection.direct", { cost: formatEuro(terms.price_cents ?? 0) })}</strong>
      <br />
      {terms.payment_instructions}
    </span>
  );
}

export function CollectionFields({
  mode,
  onChange,
  instructions,
}: {
  mode: string;
  onChange: (mode: "organizer" | "provider") => void;
  instructions?: string | null;
}) {
  const t = useT();
  return (
    <>
      <label>
        {t("collection.who")}
        <select
          name="payment_mode"
          value={mode}
          onChange={(e) => onChange(e.target.value as "organizer" | "provider")}
        >
          <option value="organizer">{t("collection.organizer")}</option>
          <option value="provider">{t("collection.provider")}</option>
        </select>
      </label>
      {mode === "provider" && (
        <label>
          {t("collection.instructions")}
          <textarea
            name="payment_instructions"
            required
            maxLength={5000}
            rows={3}
            defaultValue={instructions ?? ""}
          />
        </label>
      )}
    </>
  );
}
