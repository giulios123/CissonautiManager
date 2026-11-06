import { getLocale, intlTag } from "./i18n/locale";

const euroFormats = new Map<string, Intl.NumberFormat>();

export function formatEuro(cents: number): string {
  const tag = intlTag();
  let format = euroFormats.get(tag);
  if (!format) {
    format = new Intl.NumberFormat(tag, { style: "currency", currency: "EUR" });
    euroFormats.set(tag, format);
  }
  return format.format(cents / 100);
}

/** Parses "10", "10,5" or "10.50" into cents. Returns null when the text is not a valid amount. */
export function parseEuroToCents(text: string): number | null {
  const normalized = text.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  return Math.round(parseFloat(normalized) * 100);
}

export function centsToInput(cents: number): string {
  const text = (cents / 100).toFixed(2);
  return getLocale() === "it" ? text.replace(".", ",") : text;
}

/** Participation fee: base fee plus a per-day amount for each distinct day. Mirrors the backend. */
export function computeFee(dayCount: number, baseCents: number, perDayCents: number): number {
  return baseCents + perDayCents * dayCount;
}
