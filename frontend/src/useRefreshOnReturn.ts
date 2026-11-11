import { useEffect, useRef } from "react";

const OPEN_THINGS = '[role="dialog"], [aria-modal="true"], main details[open]';
const FIELDS = "input, select, textarea";

/** True while someone is working on the page: a dialog or an open editor, or a field in focus. */
function interacting(): boolean {
  if (document.querySelector(OPEN_THINGS)) return true;
  const active = document.activeElement;
  return active instanceof HTMLElement && active.matches(FIELDS);
}

/**
 * Reload a view when the browser tab becomes visible again, so a new day moves to the top without
 * a manual reload. Nothing is reloaded (nor reordered) while a dialog or editor is open, a field
 * has the focus, or `blocked()` says so: the refresh is skipped and the next return tries again.
 */
export function useRefreshOnReturn(load: () => unknown, blocked?: () => boolean): void {
  const latest = useRef({ load, blocked });
  useEffect(() => {
    latest.current = { load, blocked };
  });
  useEffect(() => {
    function onChange() {
      if (document.visibilityState !== "visible") return;
      const { load: reload, blocked: isBlocked } = latest.current;
      if (isBlocked?.() || interacting()) return;
      void reload();
    }
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);
}
