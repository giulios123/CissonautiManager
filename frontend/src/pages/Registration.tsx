import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import {
  canJoinWaitlist,
  feePreview,
  formatDayShort,
  formatDeadline,
  isFull,
  periodLabel,
  seatsLabel,
  type Day,
} from "../booking";
import type { PickerDay } from "../daySelection";
import { EVENT_NAME } from "../eventName";
import { formatEuro } from "../money";
import { DayPicker } from "./DayPicker";

type Channel = { code: string; label: string; instructions: string };
type Legal = { version: number; body: string };
type PublicEdition = {
  registration_open: boolean;
  name: string | null;
  registration_intro: string | null;
  base_fee_cents: number | null;
  per_day_fee_cents: number | null;
  hold_days: number | null;
  days: Day[];
  payment_channels: Channel[];
  privacy: Legal | null;
  disclaimer: Legal | null;
};
type Summary = {
  personal_code: string;
  amount_due_cents: number;
  hold_expires_at: string;
  slots: { label: string }[];
  payment_channels: Channel[];
};
type Waitlisted = { label: string; position: number };
type Outcome =
  | { kind: "created"; booking: Summary; waitlist: Waitlisted[] }
  | { kind: "waitlisted"; personalCode: string; waitlist: Waitlisted[] }
  | { kind: "already"; message: string };

/** Label of a full slot: whether its waitlist can still be joined. */
function fullSlotLabel(slot: Day["slots"][number]) {
  if (canJoinWaitlist(slot)) return "completo, spunta per entrare in lista d'attesa";
  if (slot.waitlist_free === 0) return "completo, anche la lista d'attesa";
  return seatsLabel(slot);
}

const fetchEdition = () => api<PublicEdition>("/api/public/edition");

export function Registration() {
  const [edition, setEdition] = useState<PublicEdition | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    fetchEdition()
      .then(setEdition)
      .catch(() => setLoadError(true));
  }, []);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  if (loadError)
    return <main role="alert">Non riesco a caricare la pagina. Riprova tra poco.</main>;
  if (!edition) return <main aria-busy="true">Caricamento…</main>;

  if (outcome?.kind === "already") {
    return (
      <main>
        <h1>Sei già iscritto</h1>
        <p role="status">{outcome.message}</p>
      </main>
    );
  }
  if (outcome?.kind === "created")
    return <Confirmation booking={outcome.booking} waitlist={outcome.waitlist} />;
  if (outcome?.kind === "waitlisted")
    return <WaitlistConfirmation personalCode={outcome.personalCode} waitlist={outcome.waitlist} />;

  if (!edition.registration_open || !edition.privacy || !edition.disclaimer) {
    return (
      <main>
        <h1>{edition.name ?? EVENT_NAME}</h1>
        <p>Le iscrizioni non sono ancora aperte. Torna a trovarci presto!</p>
      </main>
    );
  }

  const { privacy, disclaimer } = edition;
  const fullIds = new Set(
    edition.days.flatMap((day) => day.slots.filter((slot) => isFull(slot)).map((slot) => slot.id)),
  );
  const toBook = new Set([...selected].filter((id) => !fullIds.has(id)));
  const toWait = [...selected].filter((id) => fullIds.has(id));
  const fee = feePreview(
    edition.days,
    toBook,
    edition.base_fee_cents ?? 0,
    edition.per_day_fee_cents ?? 0,
  );

  const pickerDays: PickerDay[] = edition.days.map((day) => ({
    date: day.date,
    slots: day.slots.map((slot) => {
      const full = isFull(slot);
      return {
        id: slot.id,
        period: slot.period,
        start_time: slot.start_time,
        end_time: slot.end_time,
        full,
        disabled: full && !canJoinWaitlist(slot),
        hint: full ? fullSlotLabel(slot) : seatsLabel(slot),
      };
    }),
  }));
  const chosenDays = edition.days
    .map((day) => ({
      date: day.date,
      label: formatDayShort(day.date),
      slots: day.slots
        .filter((slot) => selected.has(slot.id))
        .map((slot) => ({
          id: slot.id,
          period: periodLabel(slot.period),
          waiting: fullIds.has(slot.id),
        })),
    }))
    .filter((day) => day.slots.length > 0);
  const first = edition.days[0]?.date;
  const last = edition.days[edition.days.length - 1]?.date;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (selected.size === 0) {
      setError("Scegli almeno uno slot.");
      return;
    }
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "");
    setSending(true);
    try {
      const result = await api<{
        result: string;
        message?: string;
        booking?: Summary;
        personal_code?: string;
        waitlist?: Waitlisted[];
      }>("/api/public/registrations", {
        method: "POST",
        json: {
          first_name: text("first_name"),
          last_name: text("last_name"),
          email: text("email"),
          phone: text("phone") || null,
          invited_by: text("invited_by") || null,
          can_bring: text("can_bring"),
          slot_ids: [...toBook],
          waitlist_slot_ids: toWait,
          accept_privacy: data.get("accept_privacy") === "on",
          accept_disclaimer: data.get("accept_disclaimer") === "on",
          privacy_version: privacy.version,
          disclaimer_version: disclaimer.version,
        },
      });
      if (result.result === "created" && result.booking) {
        setOutcome({ kind: "created", booking: result.booking, waitlist: result.waitlist ?? [] });
      } else if (result.result === "waitlisted") {
        setOutcome({
          kind: "waitlisted",
          personalCode: result.personal_code ?? "",
          waitlist: result.waitlist ?? [],
        });
      } else {
        setOutcome({ kind: "already", message: result.message ?? "Risulti già iscritto." });
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
      if (caught instanceof ApiError && caught.status === 409) {
        setSelected(new Set());
        setEdition(await fetchEdition().catch(() => edition));
      }
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="wide">
      <h1>{edition.name}</h1>
      <p className="lead intro-text">
        {edition.registration_intro ??
          "Scegli i momenti in cui vuoi venire. Puoi scegliere più giorni e più fasce orarie."}
      </p>
      {first && last && (
        <p className="meta">
          <span className="chip static">
            {formatDayShort(first)} – {formatDayShort(last)}
          </span>
        </p>
      )}
      <div className="hold-banner">
        <p className="hold-title">Il tuo posto resta bloccato per {edition.hold_days} giorni</p>
        <ol className="steps">
          <li>Scegli i turni</li>
          <li>Inserisci i tuoi dati</li>
          <li>
            <strong>Paga la quota</strong> per confermare
          </li>
        </ol>
      </div>
      <form id="registration" onSubmit={submit} noValidate={false} className="with-summary">
        <div className="form-main">
          <section aria-labelledby="when-title">
            <h2 id="when-title">Quando vieni</h2>
            <DayPicker days={pickerDays} selected={selected} onChange={setSelected} />
          </section>

          <fieldset>
            <legend>I tuoi dati</legend>
            <div className="row">
              <label>
                Nome
                <input name="first_name" autoComplete="given-name" required maxLength={100} />
              </label>
              <label>
                Cognome
                <input name="last_name" autoComplete="family-name" required maxLength={100} />
              </label>
            </div>
            <label>
              Email
              <input type="email" name="email" autoComplete="email" required />
            </label>
            <label>
              Telefono (facoltativo)
              <input type="tel" name="phone" autoComplete="tel" maxLength={50} />
            </label>
            <label>
              Chi ti ha invitato? (facoltativo)
              <input name="invited_by" maxLength={200} />
            </label>
            <label>
              Cosa puoi portare al camp?
              <textarea name="can_bring" rows={3} required maxLength={2000} />
            </label>
          </fieldset>

          <fieldset>
            <legend>Consensi</legend>
            <details>
              <summary>Leggi l'informativa privacy</summary>
              <p className="legal">{privacy.body}</p>
            </details>
            <label className="check">
              <input type="checkbox" name="accept_privacy" required />
              Ho letto e accetto l'informativa privacy
            </label>
            <details>
              <summary>Leggi lo scarico di responsabilità</summary>
              <p className="legal">{disclaimer.body}</p>
            </details>
            <label className="check">
              <input type="checkbox" name="accept_disclaimer" required />
              Ho letto e accetto lo scarico di responsabilità
            </label>
          </fieldset>

          {error && (
            <p role="alert" tabIndex={-1} ref={errorRef} className="notice error">
              {error}
            </p>
          )}
        </div>

        <aside className="summary" aria-label="Il tuo riepilogo">
          <div className="summary-head">
            <h2>Il tuo riepilogo</h2>
            <span className="count" aria-live="polite">
              {selected.size} {selected.size === 1 ? "turno" : "turni"} · {chosenDays.length}{" "}
              {chosenDays.length === 1 ? "giorno" : "giorni"}
            </span>
          </div>
          {chosenDays.length > 0 && (
            <ul className="plain summary-list">
              {chosenDays.map((day) => (
                <li key={day.date}>
                  <span className="summary-day">{day.label}</span>
                  <span className="summary-slots">
                    {day.slots.map((slot) => (
                      <button
                        type="button"
                        key={slot.id}
                        className={`summary-pill${slot.waiting ? " waiting" : ""}`}
                        title={slot.waiting ? "Lista d'attesa" : undefined}
                        aria-label={`Togli ${day.label} · ${slot.period}${slot.waiting ? " · lista d'attesa" : ""}`}
                        onClick={() =>
                          setSelected((current) => {
                            const next = new Set(current);
                            next.delete(slot.id);
                            return next;
                          })
                        }
                      >
                        {slot.period}
                        <span aria-hidden="true"> ×</span>
                      </button>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p aria-live="polite" className="fee">
            {toBook.size === 0 && toWait.length > 0 ? (
              "Solo lista d'attesa: per ora non devi pagare nulla."
            ) : (
              <>
                Quota da versare: <strong>{formatEuro(fee)}</strong>
              </>
            )}
            {toBook.size > 0 && toWait.length > 0 && (
              <>
                <br />
                In lista d&apos;attesa: {toWait.length} slot, si pagano solo se si libera un posto.
              </>
            )}
          </p>
          <p className="summary-note">La prenotazione è confermata solo dopo il pagamento.</p>
          <button type="submit" form="registration" disabled={sending}>
            {sending ? "Invio in corso…" : "Iscriviti"}
          </button>
        </aside>
      </form>
    </main>
  );
}

function WaitlistSummary({ waitlist }: { waitlist: Waitlisted[] }) {
  if (waitlist.length === 0) return null;
  return (
    <>
      <h2>In lista d&apos;attesa</h2>
      <ul>
        {waitlist.map((item) => (
          <li key={item.label}>
            {item.label}: sei {item.position}° in lista
          </li>
        ))}
      </ul>
      <p>Se si libera un posto ti scriviamo e lo slot diventa tuo.</p>
    </>
  );
}

function WaitlistConfirmation({
  personalCode,
  waitlist,
}: {
  personalCode: string;
  waitlist: Waitlisted[];
}) {
  return (
    <main>
      <h1>Sei in lista d&apos;attesa</h1>
      <p role="status">
        Gli slot che hai scelto sono al completo. Ti abbiamo inviato un&apos;email con il tuo link
        personale. Controlla anche lo spam.
      </p>
      <WaitlistSummary waitlist={waitlist} />
      <p>
        Finché non si libera un posto non devi pagare nulla. Il tuo codice è{" "}
        <strong>{personalCode}</strong>.
      </p>
      <p>
        <a href="/accedi" target="_blank" rel="noopener">
          Vai alla tua pagina personale
        </a>{" "}
        (si apre in una nuova finestra)
      </p>
    </main>
  );
}

function Confirmation({ booking, waitlist }: { booking: Summary; waitlist: Waitlisted[] }) {
  return (
    <main>
      <h1>Iscrizione ricevuta</h1>
      <p role="status">
        Ti abbiamo inviato un&apos;email con il riepilogo e il tuo link personale. Controlla anche
        lo spam.
      </p>
      <h2>I tuoi slot</h2>
      <ul>
        {booking.slots.map((slot) => (
          <li key={slot.label}>{slot.label}</li>
        ))}
      </ul>
      <WaitlistSummary waitlist={waitlist} />
      <h2>Come pagare</h2>
      <p>
        Quota: <strong>{formatEuro(booking.amount_due_cents)}</strong>
        <br />
        Causale: <strong>{booking.personal_code}</strong>
      </p>
      <p>
        Il posto è bloccato fino al <strong>{formatDeadline(booking.hold_expires_at)}</strong>. Se
        non paghi entro quella data si libera.
      </p>
      {booking.payment_channels.length > 0 ? (
        <ul>
          {booking.payment_channels.map((channel) => (
            <li key={channel.code}>
              <strong>{channel.label}</strong>
              <br />
              <span className="legal">{channel.instructions}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>Le istruzioni di pagamento arriveranno presto.</p>
      )}
      <p>
        <a href="/accedi" target="_blank" rel="noopener">
          Vai alla tua pagina personale
        </a>{" "}
        (si apre in una nuova finestra)
      </p>
    </main>
  );
}
