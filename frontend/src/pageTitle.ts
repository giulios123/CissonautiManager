import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { EVENT_NAME } from "./SiteHeader";

const TITLES: Record<string, string> = {
  "/iscrizione": "Iscrizione",
  "/accedi": "Accedi",
  "/accedi/verifica": "Entra nella tua pagina",
  "/io": "La tua iscrizione",
  "/guida": "Guida",
  "/admin": "Persone",
  "/admin/giorni": "Giorni e slot",
  "/admin/settimana": "Settimana",
  "/admin/pasti": "Pasti",
  "/admin/attivita": "Attività",
  "/admin/contributi": "Contributi",
  "/admin/report": "Report",
  "/admin/da-verificare": "Pagamenti da verificare",
  "/admin/amministratori": "Admin",
  "/admin/impostazioni": "Impostazioni",
};

/** The title of the page at a path, so that tabs, history and screen readers tell pages apart. */
export function titleFor(pathname: string): string {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (path === "/") return EVENT_NAME;
  let page = TITLES[path];
  if (!page && /^\/admin\/iscrizioni\/[^/]+$/.test(path)) page = "Scheda iscrizione";
  if (!page && /^\/admin\/attivita\/[^/]+$/.test(path)) page = "Attività";
  return `${page ?? "Pagina non trovata"} · ${EVENT_NAME}`;
}

export function usePageTitle(): void {
  const { pathname } = useLocation();
  useEffect(() => {
    document.title = titleFor(pathname);
  }, [pathname]);
}
