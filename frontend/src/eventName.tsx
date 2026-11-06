import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

/** Used until the edition is known, and when there is no active edition. */
export const EVENT_NAME = "Cissonauti Summer Camp";

type EventNameState = { name: string; logoUrl: string | null; refresh: () => void };

const EventNameContext = createContext<EventNameState>({
  name: EVENT_NAME,
  logoUrl: null,
  refresh: () => {},
});

/** The name of the active edition, for the header, the tab title and the home page. */
export function EventNameProvider({ children }: { children: ReactNode }) {
  const [name, setName] = useState(EVENT_NAME);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api<{ name?: string | null; logo_url?: string | null }>("/api/public/edition")
      .then((edition) => {
        setName(edition?.name?.trim() || EVENT_NAME);
        setLogoUrl(edition?.logo_url ?? null);
      })
      .catch(() => {
        setName(EVENT_NAME);
        setLogoUrl(null);
      });
  }, []);

  useEffect(refresh, [refresh]);

  return (
    <EventNameContext.Provider value={{ name, logoUrl, refresh }}>
      {children}
    </EventNameContext.Provider>
  );
}

export function useEventName(): string {
  return useContext(EventNameContext).name;
}

export function useEventLogo(): string | null {
  return useContext(EventNameContext).logoUrl;
}

/** Re-reads the edition name and logo after an admin changes either one. */
export function useRefreshEventName(): () => void {
  return useContext(EventNameContext).refresh;
}
