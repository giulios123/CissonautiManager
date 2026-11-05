import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { priceLabel } from "../activities";
import type { ActivityOffer, BookingView } from "../auth";
import { formatDay, periodLabel } from "../booking";
import { formatEuro } from "../money";

function seatsText(offer: ActivityOffer) {
  if (offer.free === null) return "senza limite di posti";
  if (offer.free < 1) return offer.joined ? "completo, il tuo posto c'è" : "completo";
  return `${offer.free} posti liberi`;
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
    offers.filter((o) => ids.has(o.id)).reduce((sum, o) => sum + o.price_cents, 0);
  const fee = booking.amount_due_cents - price(original) + price(new Set(selected));
  const delta = fee - booking.amount_due_cents;
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
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
    } finally {
      setSaving(false);
    }
  }

  if (offers.length === 0)
    return <p>Per ora non ci sono attività nei momenti in cui sei presente.</p>;

  return (
    <form onSubmit={save} aria-label="Scegli le attività">
      {offers.map((offer) => {
        const full = offer.free !== null && offer.free < 1 && !offer.joined;
        const locked = (offer.past || full) && !admin;
        return (
          <label className="check" key={offer.id}>
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
              {offer.past ? "giorno passato" : seatsText(offer)}
              {offer.description && (
                <>
                  <br />
                  <small>{offer.description}</small>
                </>
              )}
            </span>
          </label>
        );
      })}
      {admin && (
        <label className="check">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
          Forza oltre la capienza
        </label>
      )}
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
          Attività aggiornate.
        </p>
      )}
      <button type="submit" disabled={!changed || saving}>
        Salva le attività
      </button>
    </form>
  );
}
