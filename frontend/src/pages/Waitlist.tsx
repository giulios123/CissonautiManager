import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Me } from "../auth";
import { canJoinWaitlist, formatDay, hhmm, periodLabel, type Day } from "../booking";

const ACTIVE = new Set(["in_attesa_pagamento", "confermata"]);

const fetchDays = () =>
  api<{ days: Day[] }>("/api/public/edition").then((edition) => edition.days ?? []);

/** The person's waitlist entries, and the full slots they can still wait for. */
export function Waitlist({ me, reload }: { me: Me; reload: () => Promise<void> }) {
  const [days, setDays] = useState<Day[] | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const entries = me.waitlist ?? [];
  const listed = new Set(entries.map((entry) => entry.slot_id));
  const booked = new Set(
    me.bookings
      .filter((booking) => ACTIVE.has(booking.status))
      .flatMap((booking) => booking.slots.map((slot) => slot.id)),
  );

  useEffect(() => {
    fetchDays()
      .then(setDays)
      .catch(() => setDays([]));
  }, []);

  async function act(path: string, method: "POST" | "DELETE", okText: string, json?: unknown) {
    setBusy(true);
    setMessage(null);
    try {
      await api(path, { method, json });
      await reload();
      setMessage({ ok: true, text: okText });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : "Qualcosa è andato storto. Riprova.",
      });
    } finally {
      setDays(await fetchDays().catch(() => days));
      setBusy(false);
    }
  }

  const joinable = (days ?? []).flatMap((day) =>
    day.past
      ? []
      : day.slots
          .filter((slot) => canJoinWaitlist(slot) && !listed.has(slot.id) && !booked.has(slot.id))
          .map((slot) => ({ day, slot })),
  );
  if (entries.length === 0 && joinable.length === 0) return null;

  return (
    <section className="card" aria-labelledby="waitlist-title">
      <h2 id="waitlist-title">Lista d&apos;attesa</h2>
      {entries.length > 0 ? (
        <>
          <p>Se si libera un posto ti arriva un&apos;email e lo slot diventa tuo.</p>
          <ul>
            {entries.map((entry) => (
              <li key={entry.id}>
                {entry.label}: sei <strong>{entry.position}° in lista</strong>{" "}
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    act(`/api/me/waitlist/${entry.id}`, "DELETE", "Sei uscito dalla lista.")
                  }
                >
                  Esci dalla lista
                </button>
              </li>
            ))}
          </ul>
          {me.bookings.every((booking) => !ACTIVE.has(booking.status)) && (
            <p>Finché non si libera un posto non devi pagare nulla.</p>
          )}
        </>
      ) : (
        <p>Questi slot sono al completo, ma puoi metterti in lista.</p>
      )}
      {joinable.length > 0 && (
        <ul aria-label="Slot pieni con lista aperta">
          {joinable.map(({ day, slot }) => (
            <li key={slot.id}>
              {formatDay(day.date)}, {periodLabel(slot.period).toLowerCase()}{" "}
              {hhmm(slot.start_time)}-{hhmm(slot.end_time)}{" "}
              <button
                type="button"
                className="secondary"
                disabled={busy}
                onClick={() =>
                  act("/api/me/waitlist", "POST", "Sei in lista d'attesa.", { slot_id: slot.id })
                }
              >
                Mettiti in lista
              </button>
            </li>
          ))}
        </ul>
      )}
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`notice ${message.ok ? "ok" : "error"}`}
        >
          {message.text}
        </p>
      )}
    </section>
  );
}
