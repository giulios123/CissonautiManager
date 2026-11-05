import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { detectFromBrowser, getLocale, setCurrentLocale, storeLocale, type Locale } from "./locale";
import {
  translate,
  translatePlural,
  type MessageKey,
  type Params,
  type PluralKey,
} from "./messages";

export { LOCALES, type Locale } from "./locale";
export type { MessageKey } from "./messages";

type I18n = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey, params?: Params) => string;
  tn: (key: PluralKey, count: number, params?: Params) => string;
};

function build(locale: Locale, setLocale: (locale: Locale) => void): I18n {
  return {
    locale,
    setLocale,
    t: (key, params) => translate(locale, key, params),
    tn: (key, count, params) => translatePlural(locale, key, count, params),
  };
}

// Without a provider (small component tests) the app speaks Italian.
const I18nContext = createContext<I18n>(build("it", () => {}));

type ProviderProps = {
  /** Forces a language; used by tests. Without it the language is detected from the browser. */
  locale?: Locale;
  children: ReactNode;
};

export function I18nProvider({ locale: forced, children }: ProviderProps) {
  const [locale, setState] = useState<Locale>(() => forced ?? detectFromBrowser());
  setCurrentLocale(locale); // before children render, so that formatters see it

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setCurrentLocale(next);
    storeLocale(next);
    setState(next);
  }, []);

  const value = useMemo(() => build(locale, setLocale), [locale, setLocale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  return useContext(I18nContext);
}

export function useT(): I18n["t"] {
  return useContext(I18nContext).t;
}

export { getLocale };
