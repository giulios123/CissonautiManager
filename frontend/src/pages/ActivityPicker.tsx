import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { priceLabel } from "../activities";
import type { ActivityOffer, BookingView } from "../auth";
import { formatDay, periodLabel } from "../booking";
import { useT } from "../i18n";
import { getLocale } from "../i18n/locale";
import { tNow, translatePlural } from "../i18n/messages";
import { formatEuro } from "../money";
import { collectableCents, CollectionDetails } from "../collection";

function seatsText(offer: ActivityOffer) {
  if (offer.free === null) return tNow("act.unlimited");
  if (offer.free < 1) return offer.joined ? tNow("act.fullMine") : tNow("act.full");
  return translatePlural(getLocale(), "seats.free", offer.free);
}

/** Join or leave the activities of the moments the person is present. */
export function ActivityPicker<T = unknown>({
  booking,
  offers,
  onSaved,
  path = "/api/me/booking/activities",
  admin = false,
}: {
  booking: BookingView;
  offers: ActivityOffer[];
  onSaved: (result: T) => Promise<void> | void;
  // Admins save through their own endpoint, can change past days and go over capacity.
  path?: string;
  admin?: boolean;
}) {
  const t = useT();
  const original = new Set(offers.filter((o) => o.joined).map((o) => o.id));
  // Offers can change while the picker is open (a slot change drops an activity): only the
  // activities still offered can be chosen and sent.
  const offered = new Set(offers.map((o) => o.id));
  const [selected, setSelected] = useState<Set<number>>(new Set(original));
  const [force, setForce] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const price = (ids: Set<number>) =>
    offers.filter((o) => ids.has(o.id)).reduce((sum, o) => sum + collectableCents(o), 0);
  const fee = booking.amount_due_cents - price(original) + price(new Set(selected));
  const delta = fee - booking.amount_due_cents;
  const feePolicy = booking.confirmation_policy === "registration_fee";
  const chosen = new Set([...selected].filter((id) => offered.has(id)));
  const changed = chosen.size !== original.size || [...chosen].some((id) => !original.has(id));

  function toggle(id: number, checked: boolean) {
    setSaved(false);
    setSelected((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const json = admin ? { activity_ids: [...chosen], force } : { activity_ids: [...chosen] };
      const result = await api<T>(path, { method: "PUT", json });
      await onSaved(result);
      setSaved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setSaving(false);
    }
  }

  if (offers.length === 0) return <p>{t("act.none")}</p>;

  return (
    <form onSubmit={save} aria-label={t("act.aria")}>
      {offers.map((offer) => {
        const full = offer.free !== null && offer.free < 1 && !offer.joined;
        const locked = (offer.past || full) && !admin;
        return (
          <div className="activity-option" key={offer.id}>
            <label className="check">
              <input
                type="checkbox"
                checked={selected.has(offer.id)}
                disabled={locked}
                onChange={(e) => toggle(offer.id, e.target.checked)}
              />
              <span>
                <strong>{offer.title}</strong>, {formatDay(offer.date)}{" "}
                {periodLabel(offer.period).toLowerCase()}
                {offer.time_label && ` (${offer.time_label})`} · {priceLabel(offer.price_cents)} ·{" "}
                {offer.past ? t("edit.pastDay") : seatsText(offer)}
              </span>
            </label>
            <details>
              <summary>{t("act.details")}</summary>
              {offer.description && <p>{offer.description}</p>}
              <p>
                {formatDay(offer.date)} · {periodLabel(offer.period)}
                {offer.start_time && offer.end_time && ` · ${offer.start_time}–${offer.end_time}`}
              </p>
              <p>
                {priceLabel(offer.price_cents)} · {t("collection.who")}:{" "}
                {t(
                  offer.payment_mode === "provider"
                    ? "collection.provider"
                    : "collection.organizer",
                )}
              </p>
              {offer.capacity !== null && <p>{seatsText(offer)}</p>}
              <CollectionDetails terms={offer} />
            </details>
          </div>
        );
      })}
      {admin && (
        <label className="check">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
          {t("act.force")}
        </label>
      )}
      <p aria-live="polite" className="fee">
        {feePolicy && booking.registration_fee_cents != null && (
          <>
            {t("money.registrationFee")}{" "}
            <strong>{formatEuro(booking.registration_fee_cents)}</strong>
            <br />
          </>
        )}
        {feePolicy ? t("edit.newTotal") : t("edit.newFee")} <strong>{formatEuro(fee)}</strong>
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
          {t("act.updated")}
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        {t("act.save")}
      </button>
    </form>
  );
}
