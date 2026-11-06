import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { useT } from "../i18n";
import { ROUTES } from "../routes";

/**
 * The token is consumed only when the person presses the button, never on page load, so email
 * clients and security scanners that pre-open links cannot burn the single-use token.
 */
export function Verify() {
  const t = useT();
  const [params] = useSearchParams();
  const token = params.get("token");
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function enter() {
    setBusy(true);
    setError(null);
    try {
      const result = await api<{ redirect: string }>("/api/auth/verify", {
        method: "POST",
        json: { token },
      });
      navigate(result.redirect);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <main>
        <h1>{t("verify.invalidTitle")}</h1>
        <p>
          <Link to={ROUTES.login}>{t("verify.requestNew")}</Link>
        </p>
      </main>
    );
  }

  return (
    <main>
      <h1>{t("verify.title")}</h1>
      <button type="button" onClick={enter} disabled={busy}>
        {t("verify.enter")}
      </button>
      {error && (
        <>
          <p role="alert" className="notice error">
            {error}
          </p>
          <p>
            <Link to={ROUTES.login}>{t("verify.requestNew")}</Link>
          </p>
        </>
      )}
    </main>
  );
}
