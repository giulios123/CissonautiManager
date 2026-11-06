import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";

type Parts = { subject: string; intro: string; closing: string };
type Stored = { subject: string | null; intro: string | null; closing: string | null };
type EmailText = {
  kind: string;
  label: string;
  automatic: string;
  defaults: Parts;
  stored: Stored;
};
type Texts = {
  placeholders: string[];
  emails: EmailText[];
  registration_intro: { stored: string | null; default: string };
};
type Notice = { ok: boolean; text: string } | null;

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : "Qualcosa è andato storto. Riprova.";
}

function NoticeLine({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
      {notice.text}
    </p>
  );
}

function IntroSection({ intro }: { intro: Texts["registration_intro"] }) {
  const [text, setText] = useState(intro.stored ?? intro.default);
  const [notice, setNotice] = useState<Notice>(null);

  async function save(value: string | null, done: string) {
    try {
      const saved = await api<{ stored: string | null; default: string }>(
        "/api/admin/registration-intro",
        { method: "PUT", json: { text: value } },
      );
      setText(saved.stored ?? saved.default);
      setNotice({ ok: true, text: done });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error) });
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void save(text, "Testo salvato.");
  }

  return (
    <form onSubmit={submit} aria-labelledby="intro-title">
      <h2 id="intro-title">Modulo di iscrizione</h2>
      <p>
        Il paragrafo che compare sopra il modulo. Il riquadro con i giorni di blocco e i tre passi
        resta automatico.
      </p>
      <label>
        Testo sopra il modulo
        <textarea
          rows={4}
          value={text}
          maxLength={4000}
          onChange={(e) => setText(e.target.value)}
        />
      </label>
      <div className="actions">
        <button type="submit">Salva il testo</button>
        <button
          type="button"
          className="secondary"
          onClick={() => void save(null, "Ripristinato il testo predefinito.")}
        >
          Ripristina il predefinito
        </button>
      </div>
      <NoticeLine notice={notice} />
    </form>
  );
}

function EmailSection({ email }: { email: EmailText }) {
  const [parts, setParts] = useState<Parts>({
    subject: email.stored.subject ?? email.defaults.subject,
    intro: email.stored.intro ?? email.defaults.intro,
    closing: email.stored.closing ?? email.defaults.closing,
  });
  const [notice, setNotice] = useState<Notice>(null);
  const id = `email-${email.kind}`;

  async function save(body: Stored, done: string) {
    try {
      const saved = await api<EmailText>(`/api/admin/email-texts/${email.kind}`, {
        method: "PUT",
        json: body,
      });
      setParts({
        subject: saved.stored.subject ?? saved.defaults.subject,
        intro: saved.stored.intro ?? saved.defaults.intro,
        closing: saved.stored.closing ?? saved.defaults.closing,
      });
      setNotice({ ok: true, text: done });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error) });
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void save(parts, "Testo salvato.");
  }

  const set = (field: keyof Parts) => (value: string) => setParts({ ...parts, [field]: value });

  return (
    <details>
      <summary>{email.label}</summary>
      <form onSubmit={submit} aria-labelledby={`${id}-title`}>
        <h3 id={`${id}-title`}>Email «{email.label}»</h3>
        <label>
          Oggetto
          <input
            value={parts.subject}
            maxLength={200}
            onChange={(e) => set("subject")(e.target.value)}
          />
        </label>
        <label>
          Testo prima dei dati
          <textarea
            rows={3}
            value={parts.intro}
            maxLength={4000}
            onChange={(e) => set("intro")(e.target.value)}
          />
        </label>
        <div className="auto-block">
          <p className="auto-title">Parte automatica (non modificabile)</p>
          <p>{email.automatic}</p>
        </div>
        <label>
          Testo dopo i dati
          <textarea
            rows={3}
            value={parts.closing}
            maxLength={4000}
            onChange={(e) => set("closing")(e.target.value)}
          />
        </label>
        <div className="actions">
          <button type="submit">Salva</button>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              void save(
                { subject: null, intro: null, closing: null },
                "Ripristinati i testi predefiniti.",
              )
            }
          >
            Ripristina i predefiniti
          </button>
        </div>
        <NoticeLine notice={notice} />
      </form>
    </details>
  );
}

export function AdminTexts() {
  const [texts, setTexts] = useState<Texts | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "missing" | "error">("loading");

  useEffect(() => {
    api<Texts>("/api/admin/email-texts")
      .then((loaded) => {
        setTexts(loaded);
        setState("ready");
      })
      .catch((error) =>
        setState(error instanceof ApiError && error.status === 404 ? "missing" : "error"),
      );
  }, []);

  if (state === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state === "error") return <main role="alert">Non riesco a caricare i testi.</main>;
  if (state === "missing" || !texts) {
    return (
      <main>
        <h1>Testi</h1>
        <p>Salva prima l&apos;edizione dalle Impostazioni: i testi si modificano per edizione.</p>
      </main>
    );
  }

  return (
    <main>
      <h1>Testi</h1>
      <p>
        Qui cambi le parole del modulo e delle email. I dati della prenotazione (slot, quota,
        causale, scadenza, istruzioni di pagamento, link) si inseriscono da soli.
      </p>
      <p>
        Nel testo puoi scrivere <code>{"{nome}"}</code> per il nome della persona e{" "}
        <code>{"{evento}"}</code> per il nome dell&apos;edizione. Un campo vuoto usa il testo
        predefinito.
      </p>
      <IntroSection intro={texts.registration_intro} />
      <section aria-labelledby="emails-title">
        <h2 id="emails-title">Email</h2>
        {texts.emails.map((email) => (
          <EmailSection key={email.kind} email={email} />
        ))}
      </section>
    </main>
  );
}
