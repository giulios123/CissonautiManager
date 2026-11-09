import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useI18n } from "./i18n";
import { translate, type MessageKey } from "./i18n/messages";
import { getLocale, type Locale } from "./i18n/locale";
import { EVENT_NAME, useEventName } from "./eventName";

const TITLES: Record<string, MessageKey> = {
  "/register": "title.register",
  "/login": "title.login",
  "/login/verify": "title.verify",
  "/me": "title.me",
  "/guide": "title.guide",
  "/admin": "title.people",
  "/admin/days": "title.days",
  "/admin/week": "title.week",
  "/admin/meals": "title.meals",
  "/admin/activities": "title.activities",
  "/admin/guests": "title.guests",
  "/admin/contributions": "title.contributions",
  "/admin/report": "title.report",
  "/admin/to-collect": "title.toCollect",
  "/admin/to-review": "title.toReview",
  "/admin/admins": "title.admins",
  "/admin/settings": "title.settings",
};

/** The title of the page at a path, so that tabs, history and screen readers tell pages apart. */
export function titleFor(
  pathname: string,
  locale: Locale = getLocale(),
  eventName: string = EVENT_NAME,
): string {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (path === "/") return eventName;
  let key = TITLES[path];
  if (!key && /^\/admin\/registrations\/[^/]+$/.test(path)) key = "title.registrationDetail";
  if (!key && /^\/admin\/activities\/[^/]+$/.test(path)) key = "title.activities";
  if (!key && /^\/admin\/guests\/[^/]+$/.test(path)) key = "title.guests";
  return `${translate(locale, key ?? "notFound.title")} · ${eventName}`;
}

export function usePageTitle(): void {
  const { pathname } = useLocation();
  const { locale } = useI18n();
  const eventName = useEventName();
  useEffect(() => {
    document.title = titleFor(pathname, locale, eventName);
  }, [pathname, locale, eventName]);
}
