/** Language detection and the current language, without React so that api.ts and formatters can use it. */
export type Locale = "it" | "en";
export const LOCALES: readonly Locale[] = ["it", "en"];
export const DEFAULT_LOCALE: Locale = "it";

const STORAGE_KEY = "cissonauti.locale";

export function isLocale(value: unknown): value is Locale {
  return value === "it" || value === "en";
}

type Detection = { search?: string; stored?: string | null; languages?: readonly string[] };

/** `?lang=` wins (the iframe in Google Sites), then the saved choice, then the browser language. */
export function detectLocale({ search = "", stored = null, languages = [] }: Detection): Locale {
  const fromUrl = new URLSearchParams(search).get("lang");
  if (isLocale(fromUrl)) return fromUrl;
  if (isLocale(stored)) return stored;
  const first = languages[0]?.toLowerCase();
  if (first === undefined) return DEFAULT_LOCALE;
  return first.startsWith("it") ? "it" : "en";
}

export function readStoredLocale(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function storeLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // Private mode or blocked storage: the choice just does not persist.
  }
}

export function detectFromBrowser(): Locale {
  return detectLocale({
    search: window.location.search,
    stored: readStoredLocale(),
    languages: navigator.languages?.length ? navigator.languages : [navigator.language ?? ""],
  });
}

let current: Locale = DEFAULT_LOCALE;

export function getLocale(): Locale {
  return current;
}

export function setCurrentLocale(locale: Locale): void {
  current = locale;
}

/** BCP 47 tag for Intl. */
export function intlTag(locale: Locale = current): string {
  return locale === "it" ? "it-IT" : "en-GB";
}
