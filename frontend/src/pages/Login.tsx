import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";

export function Login() {
  const navigate = useNavigate();
  const [linkMessage, setLinkMessage] = useState<string | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function requestLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLinkError(null);
    const email = String(new FormData(event.currentTarget).get("email") ?? "");
    try {
      const result = await api<{ message: string }>("/api/auth/magic-link", {
        method: "POST",
        json: { email },
      });
      setLinkMessage(result.message);
    } catch (error) {
      setLinkError(error instanceof ApiError ? error.message : "Riprova tra poco.");
    }
  }

  async function loginWithPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError(null);
    const data = new FormData(event.currentTarget);
    try {
      const result = await api<{ redirect: string }>("/api/auth/login", {
        method: "POST",
        json: {
          email: String(data.get("email") ?? ""),
          password: String(data.get("password") ?? ""),
        },
      });
      navigate(result.redirect);
    } catch (error) {
      setPasswordError(error instanceof ApiError ? error.message : "Riprova tra poco.");
    }
  }

  return (
    <main>
      <h1>Accedi</h1>
      <form onSubmit={requestLink} aria-labelledby="link-title">
        <h2 id="link-title">Ricevi un link via email</h2>
        <p>Niente password: ti mandiamo un link che vale 30 minuti.</p>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <button type="submit">Invia il link</button>
        {linkMessage && (
          <p role="status" className="notice ok">
            {linkMessage}
          </p>
        )}
        {linkError && (
          <p role="alert" className="notice error">
            {linkError}
          </p>
        )}
      </form>
      <form onSubmit={loginWithPassword} aria-labelledby="password-title">
        <h2 id="password-title">Oppure entra con la password</h2>
        <label>
          Email
          <input type="email" name="email" autoComplete="username" required />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        <button type="submit">Entra</button>
        {passwordError && (
          <p role="alert" className="notice error">
            {passwordError}
          </p>
        )}
      </form>
      <p>
        Non sei ancora iscritto? <Link to="/register">Iscriviti al camp</Link>
      </p>
    </main>
  );
}
