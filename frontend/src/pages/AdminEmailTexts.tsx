import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useI18n, type Locale, type MessageKey } from "../i18n";

type Lang = Locale;
type Template = { subject: string; body: string };
type Email = {
  templates: Record<Lang, Template>;
  defaults: Record<Lang, Template>;
};
type Texts = {
  emails: Record<string, Email>;
  form_intro: Record<Lang, string> & { defaults: Record<Lang, string> };
};
type Notice = { ok: boolean; text: string } | null;

const URL = "/api/admin/email";
const PLACEHOLDERS = ["first_name", "last_name", "event", "start_date", "end_date"];

function errorText(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

function NoticeLine({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
      {notice.text}
    </p>
  );
}

function FormIntro({ texts, lang }: { texts: Texts["form_intro"]; lang: Lang }) {
  const { t } = useI18n();
  const [values, setValues] = useState<Record<Lang, string>>({ it: texts.it, en: texts.en });
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const saved = await api<Texts>(`${URL}/form-intro`, { method: "PUT", json: values });
      setValues({ it: saved.form_intro.it, en: saved.form_intro.en });
      setNotice({ ok: true, text: t("emx.formSaved") });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="formintro-title">
      <h2 id="formintro-title">{t("emx.formTitle")}</h2>
      <p>{t("emx.formIntro")}</p>
      <label>
        {t("emx.formText")}
        <textarea
          rows={3}
          value={values[lang]}
          maxLength={2000}
          placeholder={texts.defaults[lang]}
          onChange={(e) => setValues({ ...values, [lang]: e.target.value })}
        />
      </label>
      <button type="submit" disabled={busy}>
        {t("emx.formSave")}
      </button>
      <NoticeLine notice={notice} />
    </form>
  );
}

function EmailEditor({ kind, email, lang }: { kind: string; email: Email; lang: Lang }) {
  const { t } = useI18n();
  const [templates, setTemplates] = useState(email.templates);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState(false);
  const label = t(`emx.kind.${kind}` as MessageKey);
  const defaults = email.defaults[lang];
  const current = templates[lang];

  function change(patch: Partial<Template>) {
    setTemplates({ ...templates, [lang]: { ...current, ...patch } });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const saved = await api<Texts>(`${URL}/texts/${kind}`, {
        method: "PUT",
        json: { templates },
      });
      setTemplates(saved.emails[kind].templates);
      setNotice({ ok: true, text: t("emx.saved") });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <details>
      <summary>{label}</summary>
      <form onSubmit={submit} aria-label={t("emx.perEmail", { label })}>
        <label>
          {t("emt.subject")}
          <input
            value={current.subject}
            maxLength={200}
            placeholder={defaults.subject}
            onChange={(e) => change({ subject: e.target.value })}
          />
        </label>
        <label>
          {t("emt.body")}
          <textarea
            rows={4}
            value={current.body}
            maxLength={5000}
            placeholder={defaults.body}
            onChange={(e) => change({ body: e.target.value })}
          />
        </label>
        <div className="auto-block">
          <p className="auto-title">{t("emx.automatic")}</p>
          <p>{t(`emx.auto.${kind}` as MessageKey)}</p>
        </div>
        <button type="submit" disabled={busy}>
          {t("emx.save")}
        </button>
        <NoticeLine notice={notice} />
      </form>
    </details>
  );
}

/** The paragraph above the sign-up form and the text of every other email, per language. */
export function AdminEmailTexts() {
  const { t } = useI18n();
  const [texts, setTexts] = useState<Texts | null>(null);
  const [failed, setFailed] = useState(false);
  const [lang, setLang] = useState<Lang>("it");

  useEffect(() => {
    api<Texts>(`${URL}/texts`)
      .then((loaded) => (loaded?.emails && loaded.form_intro ? setTexts(loaded) : setFailed(true)))
      .catch(() => setFailed(true));
  }, []);

  if (failed) return <p role="alert">{t("emx.loadError")}</p>;
  if (!texts) return <p aria-busy="true">{t("common.loading")}</p>;

  const names = PLACEHOLDERS.map((name) => `{${name}}`).join(", ");

  return (
    <section aria-labelledby="emails-title">
      <div role="group" aria-label={t("emt.languageTab")} className="lang-tabs">
        {(["it", "en"] as const).map((code) => (
          <button
            key={code}
            type="button"
            className="secondary"
            aria-pressed={lang === code}
            onClick={() => setLang(code)}
          >
            {t(code === "it" ? "lang.it" : "lang.en")}
          </button>
        ))}
      </div>
      <FormIntro texts={texts.form_intro} lang={lang} />
      <h2 id="emails-title">{t("emx.title")}</h2>
      <p>{t("emx.intro", { names })}</p>
      {Object.entries(texts.emails).map(([kind, email]) => (
        <EmailEditor key={kind} kind={kind} email={email} lang={lang} />
      ))}
    </section>
  );
}
