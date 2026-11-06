import { en } from "./en";
import { it, type MessageKey } from "./it";
import { getLocale, intlTag, type Locale } from "./locale";

export type { MessageKey };
export type Params = Record<string, string | number>;

const catalogs: Record<Locale, Record<MessageKey, string>> = { it, en };

function fill(text: string, params?: Params): string {
  if (!params) return text;
  return text.replace(/\{(\w+)\}/g, (whole, name: string) =>
    name in params ? String(params[name]) : whole,
  );
}

export const hasMessage = (key: string): key is MessageKey => key in it;

/** The text of a key in a language, with `{name}` placeholders replaced. */
export function translate(locale: Locale, key: MessageKey, params?: Params): string {
  return fill(catalogs[locale][key], params);
}

/** Same as `translate`, in the current language: for code outside React components. */
export function tNow(key: MessageKey, params?: Params): string {
  return translate(getLocale(), key, params);
}

type PluralBase<K extends string> = K extends `${infer B}.one` ? B : never;
export type PluralKey = PluralBase<MessageKey>;

/** Picks `<key>.one` or `<key>.other` by the plural rules of the language; `{n}` is the count. */
export function translatePlural(
  locale: Locale,
  key: PluralKey,
  count: number,
  params?: Params,
): string {
  const form = new Intl.PluralRules(intlTag(locale)).select(count) === "one" ? "one" : "other";
  return translate(locale, `${key}.${form}` as MessageKey, { n: count, ...params });
}
