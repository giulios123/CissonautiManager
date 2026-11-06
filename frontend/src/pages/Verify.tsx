import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { useT } from "../i18n";
import { ROUTES } from "../routes";

/**
 * Opening the link signs the person in, with no extra click. The link stays valid for a few
 * minutes, so mail scanners that open it first do not burn it.
 */
export function Verify() {
  const t = useT();
  const [params] = useSearchParams();
  const token = params.get("token");
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    api<{ redirect: string }>("/api/auth/verify", { method: "POST", json: { token } })
      .then((result) => navigate(result.redirect, { replace: true }))
      .catch((caught) =>
        setError(caught instanceof ApiError ? caught.message : t("common.retryShortly")),
      );
  }, [token, navigate, t]);

  if (!token || error) {
    return (
      <main>
        <h1>{t("verify.invalidTitle")}</h1>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
        <p>
          <Link to={ROUTES.login}>{t("verify.requestNew")}</Link>
        </p>
      </main>
    );
  }

  return (
    <main aria-busy="true">
      <h1>{t("verify.title")}</h1>
    </main>
  );
}
