import type { Locale } from "./i18n";

export type LegalDocumentText = {
  body: string;
  body_it?: string | null;
  body_en?: string | null;
};

export function legalTextForLocale(
  document: LegalDocumentText,
  locale: Locale,
): { text: string; usesOriginal: boolean } {
  const translated = locale === "it" ? document.body_it : document.body_en;
  return translated?.trim()
    ? { text: translated, usesOriginal: false }
    : { text: document.body, usesOriginal: true };
}
