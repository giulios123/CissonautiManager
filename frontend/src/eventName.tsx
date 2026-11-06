import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

/** Used until the edition is known, and when there is no active edition. */
export const EVENT_NAME = "Cissonauti Summer Camp";

type EventNameState = { name: string; refresh: () => void };

const EventNameContext = createContext<EventNameState>({ name: EVENT_NAME, refresh: () => {} });

/** The name of the active edition, for the header, the tab title and the home page. */
export function EventNameProvider({ children }: { children: ReactNode }) {
  const [name, setName] = useState(EVENT_NAME);

  const refresh = useCallback(() => {
    api<{ name?: string | null }>("/api/public/edition")
      .then((edition) => setName(edition?.name?.trim() || EVENT_NAME))
      .catch(() => setName(EVENT_NAME));
  }, []);

  useEffect(refresh, [refresh]);

  return (
    <EventNameContext.Provider value={{ name, refresh }}>{children}</EventNameContext.Provider>
  );
}

export function useEventName(): string {
  return useContext(EventNameContext).name;
}

/** Re-reads the name after an admin renames the edition. */
export function useRefreshEventName(): () => void {
  return useContext(EventNameContext).refresh;
}
