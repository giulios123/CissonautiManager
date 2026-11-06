import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useI18n, type Locale, type MessageKey } from "../i18n";

type Lang = Locale;
type Template = { subject: string; body: string };
type Card = {
  has_image: boolean;
  text_it: string;
  text_en: string;
  text_color: string;
  text_position: "top" | "center" | "bottom";
};
type Settings = {
  templates: Record<Lang, Template>;
  defaults: Record<Lang, { subject: string; body: string; card_text: string }>;
  card: Card;
};
type Notice = { ok: boolean; text: string } | null;
type Field = "subject" | "body" | "card";

const PLACEHOLDERS = ["first_name", "last_name", "event", "start_date", "end_date"] as const;
const URL = "/api/admin/email/registration";
const POSITIONS: [Card["text_position"], MessageKey][] = [
  ["top", "emt.posTop"],
  ["center", "emt.posCenter"],
  ["bottom", "emt.posBottom"],
];

function errorText(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

/** The text and the picture of the email sent when somebody signs up. */
export function AdminRegistrationEmail() {
  const { t } = useI18n();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [failed, setFailed] = useState(false);
  const [lang, setLang] = useState<Lang>("it");
  const [templates, setTemplates] = useState<Record<Lang, Template> | null>(null);
  const [card, setCard] = useState<Card | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState(false);
  const [previewKey, setPreviewKey] = useState(0);
  const [previewQuery, setPreviewQuery] = useState("");
  const [previewFailed, setPreviewFailed] = useState(false);
  const focus = useRef<{ field: Field; start: number; end: number } | null>(null);

  function load(next: Settings) {
    setSettings(next);
    setTemplates(next.templates);
    setCard(next.card);
  }

  useEffect(() => {
    api<Settings>(URL)
      .then(load)
      .catch(() => setFailed(true));
  }, []);

  const cardText = card ? (lang === "en" ? card.text_en : card.text_it) : "";

  // The preview follows what is typed, a moment after the last key.
  useEffect(() => {
    if (!card) return;
    const timer = setTimeout(() => {
      const query = new URLSearchParams({
        locale: lang,
        color: card.text_color,
        position: card.text_position,
      });
      if (cardText.trim()) query.set("text", cardText);
      setPreviewFailed(false);
      setPreviewQuery(query.toString());
    }, 400);
    return () => clearTimeout(timer);
  }, [card, cardText, lang]);

  if (failed) return <p role="alert">{t("emt.loadError")}</p>;
  if (!settings || !templates || !card) return <p aria-busy="true">{t("common.loading")}</p>;

  const defaults = settings.defaults[lang];
  const template = templates[lang];

  function setTemplate(patch: Partial<Template>) {
    setTemplates((current) =>
      current ? { ...current, [lang]: { ...current[lang], ...patch } } : current,
    );
  }
  function setCardText(value: string) {
    setCard((current) =>
      current ? { ...current, [lang === "en" ? "text_en" : "text_it"]: value } : current,
    );
  }

  function remember(field: Field, element: HTMLInputElement | HTMLTextAreaElement) {
    focus.current = {
      field,
      start: element.selectionStart ?? 0,
      end: element.selectionEnd ?? 0,
    };
  }

  function insert(name: string) {
    const token = `{${name}}`;
    const target = focus.current ?? {
      field: "body" as Field,
      start: template.body.length,
      end: template.body.length,
    };
    const put = (text: string) => text.slice(0, target.start) + token + text.slice(target.end);
    if (target.field === "subject") setTemplate({ subject: put(template.subject) });
    else if (target.field === "body") setTemplate({ body: put(template.body) });
    else setCardText(put(cardText));
    focus.current = {
      ...target,
      start: target.start + token.length,
      end: target.start + token.length,
    };
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!card || !templates) return;
    setBusy(true);
    setNotice(null);
    try {
      const saved = await api<Settings>(URL, {
        method: "PUT",
        json: {
          templates,
          card: {
            text_it: card.text_it,
            text_en: card.text_en,
            text_color: card.text_color,
            text_position: card.text_position,
          },
        },
      });
      load(saved);
      setPreviewKey((n) => n + 1);
      setNotice({ ok: true, text: t("emt.saved") });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      setBusy(false);
    }
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;
    setBusy(true);
    setNotice(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const saved = await api<Settings>(`${URL}/image`, { method: "PUT", body: form });
      setSettings(saved);
      setCard((current) => (current ? { ...current, has_image: saved.card.has_image } : current));
      setPreviewKey((n) => n + 1);
      setNotice({ ok: true, text: t("emt.uploaded") });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      input.value = "";
      setBusy(false);
    }
  }

  async function removeImage() {
    setBusy(true);
    setNotice(null);
    try {
      const saved = await api<Settings>(`${URL}/image`, { method: "DELETE" });
      setSettings(saved);
      setCard((current) => (current ? { ...current, has_image: false } : current));
      setPreviewKey((n) => n + 1);
      setNotice({ ok: true, text: t("emt.removed") });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    setBusy(true);
    setNotice(null);
    try {
      const result = await api<{ message: string }>(`${URL}/test?locale=${lang}`, {
        method: "POST",
      });
      setNotice({ ok: true, text: result.message });
    } catch (error) {
      setNotice({ ok: false, text: errorText(error, t("common.somethingWrong")) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="regemail-title" className="regemail">
      <h2 id="regemail-title">{t("emt.title")}</h2>
      <p>{t("emt.intro")}</p>

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

      <label>
        {t("emt.subject")}
        <input
          value={template.subject}
          maxLength={200}
          placeholder={defaults.subject}
          onChange={(e) => setTemplate({ subject: e.target.value })}
          onSelect={(e) => remember("subject", e.currentTarget)}
          onBlur={(e) => remember("subject", e.currentTarget)}
        />
      </label>
      <label>
        {t("emt.body")}
        <textarea
          rows={5}
          value={template.body}
          maxLength={5000}
          placeholder={defaults.body}
          onChange={(e) => setTemplate({ body: e.target.value })}
          onSelect={(e) => remember("body", e.currentTarget)}
          onBlur={(e) => remember("body", e.currentTarget)}
        />
      </label>

      <div role="group" aria-label={t("emt.placeholders")} className="placeholders">
        <span className="legal">{t("emt.placeholders")}:</span>{" "}
        {PLACEHOLDERS.map((name) => (
          <button
            key={name}
            type="button"
            className="chip"
            title={`{${name}}`}
            aria-label={t("emt.insert", { name: t(`emt.ph.${name}` as const) })}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => insert(name)}
          >
            {t(`emt.ph.${name}` as const)}
          </button>
        ))}
      </div>

      <fieldset>
        <legend>{t("emt.imageLegend")}</legend>
        <p>{t("emt.imageIntro")}</p>
        <label>
          {t("emt.file")}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={upload}
            disabled={busy}
          />
        </label>
        {card.has_image && (
          <p>
            <button type="button" className="secondary" onClick={removeImage} disabled={busy}>
              {t("emt.removeImage")}
            </button>
          </p>
        )}
        <label>
          {t("emt.cardText")}
          <textarea
            rows={3}
            value={cardText}
            maxLength={500}
            placeholder={defaults.card_text}
            onChange={(e) => setCardText(e.target.value)}
            onSelect={(e) => remember("card", e.currentTarget)}
            onBlur={(e) => remember("card", e.currentTarget)}
          />
        </label>
        <div className="row">
          <label>
            {t("emt.color")}
            <input
              type="color"
              value={card.text_color}
              onChange={(e) => setCard({ ...card, text_color: e.target.value })}
            />
          </label>
          <label>
            {t("emt.position")}
            <select
              value={card.text_position}
              onChange={(e) =>
                setCard({ ...card, text_position: e.target.value as Card["text_position"] })
              }
            >
              {POSITIONS.map(([value, label]) => (
                <option key={value} value={value}>
                  {t(label)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <h3>{t("emt.previewTitle")}</h3>
        {previewQuery && (
          <img
            className="regemail-preview"
            key={`${previewKey}-${previewQuery}`}
            src={`${URL}/preview.png?${previewQuery}&v=${previewKey}`}
            alt={t("emt.previewAlt")}
            onError={() => setPreviewFailed(true)}
          />
        )}
        {previewFailed && (
          <p role="alert" className="notice error">
            {t("emt.previewFailed")}
          </p>
        )}
      </fieldset>

      <div className="actions">
        <button type="submit" disabled={busy}>
          {t("emt.save")}
        </button>
        <button type="button" className="secondary" onClick={sendTest} disabled={busy}>
          {t("emt.sendTest")}
        </button>
      </div>
      <p className="legal">{t("emt.testHint")}</p>
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
    </form>
  );
}
