import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "./api";
import logoUrl from "./assets/logo-cissone.png";
import { isInFrame } from "./frame";
import { LOCALES, useI18n, type Locale } from "./i18n";

export const EVENT_NAME = "Cissonauti Summer Camp";

type Props = {
  /** Inside the event site's iframe: name only, no logo, so the site header is not repeated. */
  compact?: boolean;
};

function LanguageSwitch() {
  const { locale, setLocale, t } = useI18n();

  function choose(next: Locale) {
    if (next === locale) return;
    setLocale(next);
    // Saves the choice on the profile of a logged-in person, so that emails follow it.
    // Anonymous visitors get a 401 that is of no interest.
    void api("/api/me/locale", { method: "PUT", json: { locale: next } }).catch(() => {});
  }

  return (
    <div className="lang-switch" role="group" aria-label={t("lang.label")}>
      {LOCALES.map((code) => (
        <button
          key={code}
          type="button"
          lang={code}
          aria-pressed={code === locale}
          aria-label={t(code === "it" ? "lang.it" : "lang.en")}
          onClick={() => choose(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

export function SiteHeader({ compact = isInFrame() }: Props) {
  const { t } = useI18n();
  const [logoFailed, setLogoFailed] = useState(false);

  if (compact) {
    return (
      <header className="site-header compact">
        <div className="site-bar">
          <p className="site-name">{EVENT_NAME}</p>
          <LanguageSwitch />
        </div>
      </header>
    );
  }

  return (
    <header className="site-header">
      <div className="site-bar">
        <Link to="/" className="site-brand">
          {!logoFailed && (
            <img
              src={logoUrl}
              alt={t("header.logoAlt")}
              width={160}
              height={30}
              onError={() => setLogoFailed(true)}
            />
          )}
          <span className="site-name">{EVENT_NAME}</span>
        </Link>
        <LanguageSwitch />
      </div>
    </header>
  );
}
