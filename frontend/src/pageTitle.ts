import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { EVENT_NAME } from "./SiteHeader";

const TITLES: Record<string, string> = {
  "/register": "Iscrizione",
  "/login": "Accedi",
  "/login/verify": "Entra nella tua pagina",
  "/me": "La tua iscrizione",
  "/guide": "Guida",
  "/admin": "Persone",
  "/admin/days": "Giorni e slot",
  "/admin/week": "Settimana",
  "/admin/meals": "Pasti",
  "/admin/activities": "Attività",
  "/admin/contributions": "Contributi",
  "/admin/report": "Report",
  "/admin/to-collect": "Da incassare",
  "/admin/to-review": "Pagamenti da verificare",
  "/admin/admins": "Admin",
  "/admin/settings": "Impostazioni",
};

/** The title of the page at a path, so that tabs, history and screen readers tell pages apart. */
export function titleFor(pathname: string): string {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (path === "/") return EVENT_NAME;
  let page = TITLES[path];
  if (!page && /^\/admin\/registrations\/[^/]+$/.test(path)) page = "Scheda iscrizione";
  if (!page && /^\/admin\/activities\/[^/]+$/.test(path)) page = "Attività";
  return `${page ?? "Pagina non trovata"} · ${EVENT_NAME}`;
}

export function usePageTitle(): void {
  const { pathname } = useLocation();
  useEffect(() => {
    document.title = titleFor(pathname);
  }, [pathname]);
}
