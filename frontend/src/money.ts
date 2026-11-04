const euroFormat = new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" });

export function formatEuro(cents: number): string {
  return euroFormat.format(cents / 100);
}

/** Parses "10", "10,5" or "10.50" into cents. Returns null when the text is not a valid amount. */
export function parseEuroToCents(text: string): number | null {
  const normalized = text.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  return Math.round(parseFloat(normalized) * 100);
}

export function centsToInput(cents: number): string {
  return (cents / 100).toFixed(2).replace(".", ",");
}

/** Participation fee: base fee plus a per-day amount for each distinct day. Mirrors the backend. */
export function computeFee(dayCount: number, baseCents: number, perDayCents: number): number {
  return baseCents + perDayCents * dayCount;
}
