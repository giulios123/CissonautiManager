import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { EVENT_NAME, useEventName } from "./eventName";

const TITLES: Record<string, string> = {
  "/iscrizione": "Iscrizione",
  "/accedi": "Accedi",
  "/accedi/verifica": "Accesso",
  "/io": "La tua iscrizione",
  "/guida": "Guida",
  "/admin": "Persone",
  "/admin/giorni": "Giorni e slot",
  "/admin/settimana": "Settimana",
  "/admin/pasti": "Pasti",
  "/admin/attivita": "Attività",
  "/admin/contributi": "Contributi",
  "/admin/report": "Report",
  "/admin/da-incassare": "Da incassare",
  "/admin/da-verificare": "Pagamenti da verificare",
  "/admin/amministratori": "Admin",
  "/admin/testi": "Testi",
  "/admin/impostazioni": "Impostazioni",
};

/** The title of the page at a path, so that tabs, history and screen readers tell pages apart. */
export function titleFor(pathname: string, eventName: string = EVENT_NAME): string {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (path === "/") return eventName;
  let page = TITLES[path];
  if (!page && /^\/admin\/iscrizioni\/[^/]+$/.test(path)) page = "Scheda iscrizione";
  if (!page && /^\/admin\/attivita\/[^/]+$/.test(path)) page = "Attività";
  return `${page ?? "Pagina non trovata"} · ${eventName}`;
}

export function usePageTitle(): void {
  const { pathname } = useLocation();
  const eventName = useEventName();
  useEffect(() => {
    document.title = titleFor(pathname, eventName);
  }, [pathname, eventName]);
}
