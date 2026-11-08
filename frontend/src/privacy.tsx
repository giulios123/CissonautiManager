import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "./api";
import { useI18n, useT } from "./i18n";

type PrivacyDocument = {
  id: number;
  version: number;
  body: string;
  body_it: string | null;
  body_en: string | null;
  is_legacy: boolean;
};

type PrivacyAcceptance = {
  id: number;
  locale: string | null;
  recorded_at: string;
  source: string;
  document: PrivacyDocument;
};

type PrivacyState = {
  edition_id: number | null;
  associated: boolean;
  required: boolean;
  current_document: PrivacyDocument | null;
  accepted_document_id: number | null;
  history: PrivacyAcceptance[];
};

function localizedText(document: PrivacyDocument, locale: string) {
  return (locale === "en" ? document.body_en : document.body_it) ?? document.body;
}

function dateLabel(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Rome",
  }).format(new Date(value));
}

export function PrivacyAcceptancePanel({ onRefresh }: { onRefresh: () => Promise<void> }) {
  const t = useT();
  const { locale } = useI18n();
  const [data, setData] = useState<PrivacyState | null>(null);
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const currentDocumentId = useRef<number | null>(null);

  const load = useCallback(async () => {
    const snapshot = await api<PrivacyState>("/api/me/privacy");
    setData(snapshot);
    if (snapshot.current_document?.id !== currentDocumentId.current) setChecked(false);
    currentDocumentId.current = snapshot.current_document?.id ?? null;
    setError(null);
    await onRefresh();
  }, [onRefresh]);

  useEffect(() => {
    const refresh = () => {
      void load()
        .then(() => setLoadFailed(false))
        .catch(() => setLoadFailed(true));
    };
    void Promise.resolve().then(refresh);
    window.addEventListener("privacy-acceptance-required", refresh);
    window.addEventListener("focus", refresh);
    return () => {
      window.removeEventListener("privacy-acceptance-required", refresh);
      window.removeEventListener("focus", refresh);
    };
    // The response contains both languages; switching language must not reset an open choice.
  }, [load]);

  if (data === null) {
    if (loadFailed) {
      return (
        <section className="card" role="alert">
          <p>{t("privacy.loadError")}</p>
        </section>
      );
    }
    return null;
  }
  if (!data.associated || !data.current_document) return null;

  const document = data.current_document;
  const complete = Boolean(document.body_it?.trim() && document.body_en?.trim());
  const canRead = complete || document.is_legacy;

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!checked || !complete) return;
    setBusy(true);
    setError(null);
    try {
      const snapshot = await api<PrivacyState>("/api/me/privacy/accept", {
        method: "POST",
        json: {
          document_id: document.id,
          version: document.version,
          locale,
          accepted: true,
        },
      });
      setData(snapshot);
      setChecked(false);
      await onRefresh();
    } catch (caught) {
      setError(
        caught instanceof ApiError && caught.status === 409
          ? t("privacy.changed")
          : caught instanceof ApiError
            ? caught.message
            : t("privacy.error"),
      );
      if (caught instanceof ApiError && caught.status === 409) {
        void load().catch(() => undefined);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card" aria-labelledby="privacy-title">
      <h2 id="privacy-title">{t("privacy.title")}</h2>
      {data.required && <p className="notice">{t("privacy.required")}</p>}
      <h3>{t("privacy.current", { version: document.version })}</h3>
      {canRead ? (
        <div className="legal">{localizedText(document, locale)}</div>
      ) : (
        <p className="notice error">{t("privacy.notAvailable")}</p>
      )}
      {data.required && complete && (
        <form onSubmit={submit}>
          <label>
            <input
              type="checkbox"
              required
              checked={checked}
              onChange={(event) => setChecked(event.target.checked)}
            />
            {t("privacy.accept")}
          </label>
          <button type="submit" disabled={!checked || busy}>
            {busy ? t("privacy.saving") : t("privacy.submit")}
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {data.history.length > 0 && (
        <details>
          <summary>{t("privacy.history")}</summary>
          <ol>
            {data.history.map((item) => (
              <li key={item.id}>
                {t("privacy.version", { version: item.document.version })} ·{" "}
                {dateLabel(item.recorded_at, locale)} ·{" "}
                {item.locale ?? t("legal.originalLanguageFallback")}
                <details>
                  <summary>{t("consent.readHistoryText")}</summary>
                  <div className="legal">
                    {localizedText(item.document, item.locale ?? "original")}
                  </div>
                </details>
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
