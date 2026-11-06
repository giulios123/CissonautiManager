import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useRefreshEventName } from "../eventName";
import { centsToInput, parseEuroToCents } from "../money";

type Channel = { code: string; label: string; instructions: string; enabled: boolean };
type Legal = { kind: string; version: number; body: string } | null;
type Edition = {
  id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  morning_start: string;
  morning_end: string;
  afternoon_start: string;
  afternoon_end: string;
  evening_start: string;
  evening_end: string;
  default_capacity: number;
  hold_days: number;
  waitlist_percent?: number;
  base_fee_cents: number;
  per_day_fee_cents: number;
  lunch_price_cents?: number;
  dinner_price_cents?: number;
  slots: unknown[];
  payment_channels: Channel[];
  privacy: Legal;
  disclaimer: Legal;
  health?: Legal;
};

type Notice = { kind: "ok" | "error"; text: string } | null;

const hhmm = (value: string) => value.slice(0, 5);

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : "Qualcosa è andato storto. Riprova.";
}

function NoticeLine({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.kind === "error" ? "alert" : "status"} className={`notice ${notice.kind}`}>
      {notice.text}
    </p>
  );
}

function EditionSection({
  edition,
  onSaved,
}: {
  edition: Edition | null;
  onSaved: (edition: Edition) => void;
}) {
  const [notice, setNotice] = useState<Notice>(null);
  const refreshEventName = useRefreshEventName();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "");
    const base = parseEuroToCents(text("base_fee"));
    const perDay = parseEuroToCents(text("per_day_fee"));
    const lunch = parseEuroToCents(text("lunch_price"));
    const dinner = parseEuroToCents(text("dinner_price"));
    if (base === null || perDay === null || lunch === null || dinner === null) {
      setNotice({ kind: "error", text: "Gli importi devono essere numeri, ad esempio 10,00." });
      return;
    }
    try {
      const saved = await api<Edition>("/api/admin/edition", {
        method: "PUT",
        json: {
          name: text("name"),
          start_date: text("start_date") || null,
          end_date: text("end_date") || null,
          morning_start: text("morning_start"),
          morning_end: text("morning_end"),
          afternoon_start: text("afternoon_start"),
          afternoon_end: text("afternoon_end"),
          evening_start: text("evening_start"),
          evening_end: text("evening_end"),
          default_capacity: Number(text("default_capacity")),
          hold_days: Number(text("hold_days")),
          waitlist_percent: Number(text("waitlist_percent")),
          base_fee_cents: base,
          per_day_fee_cents: perDay,
          lunch_price_cents: lunch,
          dinner_price_cents: dinner,
        },
      });
      onSaved(saved);
      refreshEventName();
      setNotice({ kind: "ok", text: `Salvato. Slot dell'edizione: ${saved.slots.length}.` });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="edition-title" key={edition?.id ?? "new"}>
      <h2 id="edition-title">Edizione</h2>
      <label>
        Nome
        <input name="name" required defaultValue={edition?.name ?? ""} />
      </label>
      <div className="row">
        <label>
          Primo giorno
          <input type="date" name="start_date" defaultValue={edition?.start_date ?? ""} />
        </label>
        <label>
          Ultimo giorno
          <input type="date" name="end_date" defaultValue={edition?.end_date ?? ""} />
        </label>
      </div>
      <fieldset>
        <legend>Orari degli slot</legend>
        <div className="row">
          <label>
            Mattina dalle
            <input
              type="time"
              name="morning_start"
              required
              defaultValue={hhmm(edition?.morning_start ?? "09:00")}
            />
          </label>
          <label>
            alle
            <input
              type="time"
              name="morning_end"
              required
              defaultValue={hhmm(edition?.morning_end ?? "13:00")}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Pomeriggio dalle
            <input
              type="time"
              name="afternoon_start"
              required
              defaultValue={hhmm(edition?.afternoon_start ?? "14:00")}
            />
          </label>
          <label>
            alle
            <input
              type="time"
              name="afternoon_end"
              required
              defaultValue={hhmm(edition?.afternoon_end ?? "18:00")}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Sera dalle
            <input
              type="time"
              name="evening_start"
              required
              defaultValue={hhmm(edition?.evening_start ?? "19:00")}
            />
          </label>
          <label>
            alle (00:00 = mezzanotte)
            <input
              type="time"
              name="evening_end"
              required
              defaultValue={hhmm(edition?.evening_end ?? "00:00")}
            />
          </label>
        </div>
      </fieldset>
      <div className="row">
        <label>
          Posti per slot di giorno (la sera è senza limite)
          <input
            type="number"
            name="default_capacity"
            min={1}
            required
            defaultValue={edition?.default_capacity ?? 25}
          />
        </label>
        <label>
          Giorni di blocco del posto
          <input
            type="number"
            name="hold_days"
            min={1}
            required
            defaultValue={edition?.hold_days ?? 3}
          />
        </label>
        <label>
          Lista d&apos;attesa (% dei posti)
          <input
            type="number"
            name="waitlist_percent"
            min={0}
            max={100}
            required
            defaultValue={edition?.waitlist_percent ?? 20}
          />
        </label>
      </div>
      <div className="row">
        <label>
          Quota base (€)
          <input
            name="base_fee"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.base_fee_cents ?? 1000)}
          />
        </label>
        <label>
          Quota per ogni giorno (€)
          <input
            name="per_day_fee"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.per_day_fee_cents ?? 100)}
          />
        </label>
      </div>
      <div className="row">
        <label>
          Prezzo del pranzo (€)
          <input
            name="lunch_price"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.lunch_price_cents ?? 800)}
          />
        </label>
        <label>
          Prezzo della cena (€)
          <input
            name="dinner_price"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.dinner_price_cents ?? 1200)}
          />
        </label>
      </div>
      <button type="submit">Salva edizione</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

function ChannelsSection({ edition }: { edition: Edition }) {
  const [channels, setChannels] = useState(edition.payment_channels);
  const [notice, setNotice] = useState<Notice>(null);

  const update = (code: string, patch: Partial<Channel>) =>
    setChannels((current) => current.map((c) => (c.code === code ? { ...c, ...patch } : c)));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const saved = await api<Channel[]>("/api/admin/payment-channels", {
        method: "PUT",
        json: channels.map(({ code, instructions, enabled }) => ({ code, instructions, enabled })),
      });
      setChannels(saved);
      setNotice({ kind: "ok", text: "Canali salvati." });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="channels-title">
      <h2 id="channels-title">Canali di pagamento</h2>
      {channels.map((channel) => (
        <fieldset key={channel.code}>
          <legend>{channel.label}</legend>
          <label className="check">
            <input
              type="checkbox"
              checked={channel.enabled}
              onChange={(e) => update(channel.code, { enabled: e.target.checked })}
            />
            Attivo
          </label>
          <label>
            Istruzioni per {channel.label}
            <textarea
              rows={3}
              value={channel.instructions}
              onChange={(e) => update(channel.code, { instructions: e.target.value })}
            />
          </label>
        </fieldset>
      ))}
      <button type="submit">Salva canali</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

function LegalSection({
  kind,
  title,
  current,
}: {
  kind: "privacy" | "disclaimer" | "health";
  title: string;
  current: Legal;
}) {
  const [body, setBody] = useState(current?.body ?? "");
  const [version, setVersion] = useState(current?.version ?? 0);
  const [notice, setNotice] = useState<Notice>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const saved = await api<{ version: number }>("/api/admin/legal-documents", {
        method: "POST",
        json: { kind, body },
      });
      setVersion(saved.version);
      setNotice({ kind: "ok", text: `Pubblicata la versione ${saved.version}.` });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby={`${kind}-title`}>
      <h3 id={`${kind}-title`}>{title}</h3>
      <p>{version ? `Versione attuale: ${version}` : "Nessun testo pubblicato."}</p>
      <label>
        Testo
        <textarea rows={8} value={body} onChange={(e) => setBody(e.target.value)} required />
      </label>
      <button type="submit">Pubblica nuova versione</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

export function AdminSettings() {
  const [edition, setEdition] = useState<Edition | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    api<Edition>("/api/admin/edition")
      .then((loaded) => {
        setEdition(loaded);
        setState("ready");
      })
      .catch((error) =>
        setState(error instanceof ApiError && error.status === 404 ? "ready" : "error"),
      );
  }, []);

  if (state === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state === "error") return <main role="alert">Non riesco a caricare le impostazioni.</main>;

  return (
    <main>
      <h1>Impostazioni</h1>
      <EditionSection edition={edition} onSaved={setEdition} />
      {edition ? (
        <>
          <ChannelsSection edition={edition} />
          <section aria-labelledby="legal-title">
            <h2 id="legal-title">Testi legali</h2>
            <p>Ogni modifica crea una nuova versione. Le iscrizioni conservano quella accettata.</p>
            <LegalSection kind="privacy" title="Informativa privacy" current={edition.privacy} />
            <LegalSection
              kind="disclaimer"
              title="Scarico di responsabilità"
              current={edition.disclaimer}
            />
            <LegalSection
              kind="health"
              title="Consenso per allergie e intolleranze (dati sanitari)"
              current={edition.health ?? null}
            />
          </section>
        </>
      ) : (
        <p>Salva l'edizione per configurare canali di pagamento e testi legali.</p>
      )}
    </main>
  );
}
