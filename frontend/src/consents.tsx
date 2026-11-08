import { useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { useI18n, useT } from "./i18n";

type Document = {
  id: number;
  version: number;
  body: string;
  body_it: string | null;
  body_en: string | null;
  is_legacy: boolean;
};
type ConsentEvent = {
  id: number;
  action: string;
  locale: string;
  recorded_at: string;
  source: string;
  document: Document;
};
type Consent = {
  kind: "attendance" | "media";
  action: string;
  event_id: number | null;
  authorized_for_current_document: boolean;
  needs_renewal: boolean;
  current_document: Document | null;
  events: ConsentEvent[];
};
export type ConsentCollection = {
  edition_id: number | null;
  associated: boolean;
  consents: Consent[];
  privacy_current_version?: number | null;
  privacy_accepted_version?: number | null;
  privacy_acceptance_required?: boolean;
  privacy_history?: {
    id: number;
    locale: string | null;
    recorded_at: string;
    source: string;
    document: Document;
  }[];
};

function available(document: Document | null): document is Document {
  return Boolean(document?.body_it?.trim() && document.body_en?.trim());
}

function textFor(document: Document, locale: string) {
  return (locale === "en" ? document.body_en : document.body_it) ?? document.body;
}

function initialChoice(item: Consent): boolean | null {
  if (item.event_id === null || item.current_document === null) return null;
  const last = item.events.at(-1);
  if (!last || last.document.id !== item.current_document.id) return null;
  if (item.action === "granted") return item.authorized_for_current_document ? true : null;
  if (item.action === "declined" || item.action === "withdrawn") return false;
  return null;
}

function actionLabel(action: string, t: ReturnType<typeof useT>) {
  if (action === "granted") return t("consent.granted");
  if (action === "declined") return t("consent.declined");
  if (action === "withdrawn") return t("consent.withdrawn");
  return t("consent.notExpressed");
}

function dateLabel(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Rome",
  }).format(new Date(value));
}

export function ConsentPanel() {
  const t = useT();
  const { locale } = useI18n();
  const [data, setData] = useState<ConsentCollection | null>(null);
  const [choice, setChoice] = useState<Record<string, boolean | null>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function load(resetKind?: string) {
    const snapshot = await api<ConsentCollection>("/api/me/consents");
    setData(snapshot);
    setChoice((previous) => {
      const next = { ...previous };
      for (const item of snapshot.consents ?? []) {
        if (item.kind === resetKind || !(item.kind in next)) next[item.kind] = initialChoice(item);
      }
      return next;
    });
  }

  useEffect(() => {
    void api<ConsentCollection>("/api/me/consents")
      .then((snapshot) => {
        setData(snapshot);
        setChoice((previous) => {
          const next = { ...previous };
          for (const item of snapshot.consents ?? []) {
            if (!(item.kind in next)) next[item.kind] = initialChoice(item);
          }
          return next;
        });
      })
      .catch(() => setMessage({ ok: false, text: t("consent.loadError") }));
    // The legal body is bilingual in one response; changing the interface language does not
    // reload or reset an in-progress choice.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save(item: Consent) {
    const selected = choice[item.kind];
    if (selected === null || selected === undefined) return;
    const doc = item.current_document;
    const withdrawing = !selected && item.action === "granted";
    if (!withdrawing && !available(doc)) return;
    setBusy(item.kind);
    setMessage(null);
    try {
      const snapshot = await api<ConsentCollection>(`/api/me/consents/${item.kind}`, {
        method: "PUT",
        json: {
          granted: selected,
          document_id: withdrawing ? null : doc!.id,
          version: withdrawing ? null : doc!.version,
          locale,
          expected_event_id: item.event_id,
        },
      });
      setData(snapshot);
      setMessage({ ok: true, text: t("consent.saved") });
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : t("consent.saveError"),
      });
      if (error instanceof ApiError && error.status === 409) {
        void load(item.kind).catch(() => undefined);
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <section aria-labelledby="optional-consents-title" className="card">
      <h2 id="optional-consents-title">{t("consent.title")}</h2>
      <p>{t("consent.intro")}</p>
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`notice ${message.ok ? "ok" : "error"}`}
        >
          {message.text}
        </p>
      )}
      {data === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : !data.associated ? (
        <p>{t("consent.notAssociated")}</p>
      ) : (
        data.consents.map((item) => {
          const document = item.current_document;
          const canWithdraw = item.action === "granted";
          const canSubmit = available(document) || canWithdraw;
          const selected = choice[item.kind] ?? null;
          const selectedChoiceAvailable =
            available(document) || (selected === false && canWithdraw);
          const title = t(item.kind === "attendance" ? "consent.attendance" : "consent.media");
          return (
            <section key={item.kind} aria-labelledby={`consent-${item.kind}`}>
              <h3 id={`consent-${item.kind}`}>{title}</h3>
              <p>{t("consent.currentStatus", { status: actionLabel(item.action, t) })}</p>
              {item.needs_renewal && <p className="notice">{t("consent.renewal")}</p>}
              {available(document) ? (
                <details>
                  <summary>{t("consent.readCurrent", { version: document.version })}</summary>
                  <div className="legal">{textFor(document, locale)}</div>
                </details>
              ) : (
                <p>{t("consent.unavailable")}</p>
              )}
              <fieldset disabled={!canSubmit || busy === item.kind}>
                <legend>{t("consent.choice")}</legend>
                <label>
                  <input
                    type="radio"
                    name={`consent-${item.kind}-choice`}
                    checked={selected === true}
                    disabled={!available(document)}
                    onChange={() => setChoice((value) => ({ ...value, [item.kind]: true }))}
                  />
                  {t("consent.yes")}
                </label>
                <label>
                  <input
                    type="radio"
                    name={`consent-${item.kind}-choice`}
                    checked={selected === false}
                    onChange={() => setChoice((value) => ({ ...value, [item.kind]: false }))}
                  />
                  {t("consent.no")}
                </label>
              </fieldset>
              <button
                type="button"
                disabled={
                  !canSubmit || selected === null || !selectedChoiceAvailable || busy === item.kind
                }
                onClick={() => void save(item)}
              >
                {busy === item.kind ? t("consent.saving") : t("consent.save")}
              </button>
              {item.events.length > 0 && (
                <details>
                  <summary>{t("consent.history")}</summary>
                  <ol>
                    {item.events.map((event) => (
                      <li key={event.id}>
                        {actionLabel(event.action, t)} · {dateLabel(event.recorded_at, locale)} ·{" "}
                        {t("consent.version", { version: event.document.version })}
                        <details>
                          <summary>{t("consent.readHistoryText")}</summary>
                          <div className="legal">{textFor(event.document, event.locale)}</div>
                        </details>
                      </li>
                    ))}
                  </ol>
                </details>
              )}
            </section>
          );
        })
      )}
    </section>
  );
}

export function AdminConsentHistory({ participantId }: { participantId: number }) {
  const t = useT();
  const { locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ConsentCollection | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!open || data !== null) return;
    void api<ConsentCollection>(`/api/admin/participants/${participantId}/consents`)
      .then(setData)
      .catch(() => setFailed(true));
  }, [open, data, participantId]);
  return (
    <section>
      <button
        type="button"
        className="secondary"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open ? t("consent.hideAdmin") : t("consent.showAdmin")}
      </button>
      {open && (
        <div>
          {failed && <p role="alert">{t("consent.loadError")}</p>}
          {!failed && data === null && <p aria-busy="true">{t("common.loading")}</p>}
          {data?.privacy_current_version != null && (
            <section>
              <h3>{t("privacy.title")}</h3>
              <p>{t("privacy.current", { version: data.privacy_current_version })}</p>
              <p>
                {data.privacy_acceptance_required ? t("privacy.pending") : t("privacy.accepted")}
              </p>
              {data.privacy_accepted_version != null && (
                <p>{t("privacy.acceptedVersion", { version: data.privacy_accepted_version })}</p>
              )}
              {(data.privacy_history ?? []).length > 0 && (
                <details>
                  <summary>{t("privacy.history")}</summary>
                  <ol>
                    {data.privacy_history!.map((event) => (
                      <li key={event.id}>
                        {t("privacy.version", { version: event.document.version })} ·{" "}
                        {dateLabel(event.recorded_at, locale)} ·{" "}
                        {event.locale
                          ? t("privacy.recordedLanguage", { language: event.locale.toUpperCase() })
                          : t("privacy.languageNotRecorded")}{" "}
                        · {event.source}
                        <details>
                          <summary>{t("consent.readHistoryText")}</summary>
                          <div className="legal">
                            {event.locale
                              ? textFor(event.document, event.locale)
                              : event.document.body}
                          </div>
                        </details>
                      </li>
                    ))}
                  </ol>
                </details>
              )}
            </section>
          )}
          {data?.consents.map((item) => (
            <section key={item.kind}>
              <h3>{t(item.kind === "attendance" ? "consent.attendance" : "consent.media")}</h3>
              <p>{t("consent.currentStatus", { status: actionLabel(item.action, t) })}</p>
              {item.needs_renewal && <p>{t("consent.renewal")}</p>}
              <ol>
                {item.events.map((event) => (
                  <li key={event.id}>
                    {actionLabel(event.action, t)} · {dateLabel(event.recorded_at, locale)} ·{" "}
                    {event.source} · {t("consent.version", { version: event.document.version })}
                    <details>
                      <summary>{t("consent.readHistoryText")}</summary>
                      <div className="legal">{textFor(event.document, event.locale)}</div>
                    </details>
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
      )}
    </section>
  );
}
