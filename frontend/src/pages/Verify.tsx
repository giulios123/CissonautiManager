import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";

/**
 * Opening the link signs the person in, with no extra click. The link stays valid for a few
 * minutes, so mail scanners that open it first do not burn it.
 */
export function Verify() {
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
        setError(caught instanceof ApiError ? caught.message : "Riprova tra poco."),
      );
  }, [token, navigate]);

  if (!token) {
    return (
      <main>
        <h1>Link non valido</h1>
        <p>
          <Link to="/accedi">Richiedi un nuovo link</Link>
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <h1>Link non valido</h1>
        <p role="alert" className="notice error">
          {error}
        </p>
        <p>
          <Link to="/accedi">Richiedi un nuovo link</Link>
        </p>
      </main>
    );
  }

  return (
    <main aria-busy="true">
      <h1>Accesso in corso…</h1>
    </main>
  );
}
