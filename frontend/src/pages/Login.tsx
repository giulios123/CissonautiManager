import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { useT } from "../i18n";
import { ROUTES } from "../routes";

export function Login() {
  const t = useT();
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
      setLinkError(error instanceof ApiError ? error.message : t("common.retryShortly"));
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
      setPasswordError(error instanceof ApiError ? error.message : t("common.retryShortly"));
    }
  }

  return (
    <main>
      <h1>{t("login.title")}</h1>
      <form onSubmit={requestLink} aria-labelledby="link-title">
        <h2 id="link-title">{t("login.linkTitle")}</h2>
        <p>{t("login.linkIntro")}</p>
        <label>
          {t("login.email")}
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <button type="submit">{t("login.sendLink")}</button>
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
        <h2 id="password-title">{t("login.passwordTitle")}</h2>
        <label>
          {t("login.email")}
          <input type="email" name="email" autoComplete="username" required />
        </label>
        <label>
          {t("login.password")}
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        <button type="submit">{t("login.enter")}</button>
        {passwordError && (
          <p role="alert" className="notice error">
            {passwordError}
          </p>
        )}
      </form>
      <p>
        {t("login.notRegistered")} <Link to={ROUTES.register}>{t("home.register")}</Link>
      </p>
    </main>
  );
}
