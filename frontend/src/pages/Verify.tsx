import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";

/**
 * The token is consumed only when the person presses the button, never on page load, so email
 * clients and security scanners that pre-open links cannot burn the single-use token.
 */
export function Verify() {
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
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
      setBusy(false);
    }
  }

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

  return (
    <main>
      <h1>Entra nella tua pagina</h1>
      <button type="button" onClick={enter} disabled={busy}>
        Entra
      </button>
      {error && (
        <>
          <p role="alert" className="notice error">
            {error}
          </p>
          <p>
            <Link to="/accedi">Richiedi un nuovo link</Link>
          </p>
        </>
      )}
    </main>
  );
}
