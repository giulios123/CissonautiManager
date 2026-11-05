import { intlTag } from "./i18n/locale";
import { computeFee } from "./money";

export type SlotInfo = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number | null;
  // null means no limit (the evening)
  available: number | null;
  // Places left on the waitlist of a full slot; null when it is not full or has no list.
  waitlist_free?: number | null;
};
// `past` is sent by the API: the day is over (Europe/Rome) and its slots can no longer change.
export type Day = { date: string; past?: boolean; slots: SlotInfo[] };

export function distinctDays(days: Day[], selected: Set<number>): number {
  return days.filter((day) => day.slots.some((slot) => selected.has(slot.id))).length;
}

export function feePreview(
  days: Day[],
  selected: Set<number>,
  baseCents: number,
  perDayCents: number,
): number {
  return computeFee(distinctDays(days, selected), baseCents, perDayCents);
}

const cache = new Map<string, Intl.DateTimeFormat>();

/** A date formatter in the current language; built once per language and option set. */
function fmt(options: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const tag = intlTag();
  const key = `${tag}|${JSON.stringify(options)}`;
  let format = cache.get(key);
  if (!format) {
    format = new Intl.DateTimeFormat(tag, options);
    cache.set(key, format);
  }
  return format;
}

/** An ISO instant as "YYYY-MM-DDTHH:mm" in Europe/Rome time, the format of datetime-local inputs. */
export function toRomeLocalInput(iso: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Rome",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(iso));
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}

/** "sab 21 nov" / "Sat 21 Nov", for compact lists. */
export const formatDayShort = (isoDate: string) =>
  fmt({ weekday: "short", day: "numeric", month: "short", timeZone: "UTC" })
    .format(new Date(`${isoDate}T00:00:00Z`))
    .replace(/\./g, "");
/** Month and day number for the date badge: "nov", 21. */
export const dayBadge = (isoDate: string) => ({
  month: fmt({ month: "short", timeZone: "UTC" })
    .format(new Date(`${isoDate}T00:00:00Z`))
    .replace(/\./g, ""),
  day: Number(isoDate.slice(8, 10)),
});
/** "Venerdì", the weekday alone, for headings that already show the date in a badge. */
export const formatWeekday = (isoDate: string) => {
  const name = fmt({ weekday: "long", timeZone: "UTC" }).format(new Date(`${isoDate}T00:00:00Z`));
  return name.charAt(0).toUpperCase() + name.slice(1);
};
export const formatDay = (isoDate: string) =>
  fmt({ weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(
    new Date(`${isoDate}T00:00:00Z`),
  );
export const formatDeadline = (isoDateTime: string) =>
  fmt({ dateStyle: "long", timeStyle: "short", timeZone: "Europe/Rome" }).format(
    new Date(isoDateTime),
  );
const PERIOD_LABELS: Record<string, string> = {
  morning: "Mattina",
  afternoon: "Pomeriggio",
  evening: "Sera",
};
export const periodLabel = (period: string) => PERIOD_LABELS[period] ?? period;
export const isFull = (slot: SlotInfo) => slot.available !== null && slot.available < 1;
export const seatsLabel = (slot: SlotInfo) =>
  slot.available === null
    ? "senza limite di posti"
    : slot.available < 1
      ? "completo"
      : `${slot.available} posti liberi`;
export const canJoinWaitlist = (slot: SlotInfo) =>
  isFull(slot) && slot.waitlist_free != null && slot.waitlist_free > 0;
export const hhmm = (time: string) => time.slice(0, 5);

const STATUS_LABELS: Record<string, string> = {
  in_attesa_pagamento: "In attesa di pagamento",
  confermata: "Confermata",
  scaduta: "Scaduta",
  disdetta_richiesta: "Disdetta richiesta",
  rimborsata: "Rimborsata",
  in_lista: "Solo in lista d'attesa",
};
export const statusLabel = (status: string) => STATUS_LABELS[status] ?? status;

/** Present in that part of the day: the evening also counts for whoever has morning and
 * afternoon (D-009). */
export function isPresent(periods: Set<string>, period: string): boolean {
  if (period === "evening")
    return periods.has("evening") || (periods.has("morning") && periods.has("afternoon"));
  return periods.has(period);
}

export type PricedExtras = {
  meals: { date: string; kind: string }[];
  activities: { date: string; period: string; price_cents: number }[];
  lunchCents: number;
  dinnerCents: number;
};

/** Price of the meals and activities still allowed by the selected slots: the others go when
 * the slots are saved. */
export function extrasPreview(days: Day[], selected: Set<number>, extras: PricedExtras): number {
  const periods = new Map<string, Set<string>>();
  for (const day of days)
    for (const slot of day.slots)
      if (selected.has(slot.id)) {
        if (!periods.has(day.date)) periods.set(day.date, new Set());
        periods.get(day.date)?.add(slot.period);
      }
  const at = (date: string) => periods.get(date) ?? new Set<string>();
  const meals = extras.meals.reduce((sum, meal) => {
    const allowed =
      meal.kind === "lunch"
        ? isPresent(at(meal.date), "morning") || isPresent(at(meal.date), "afternoon")
        : isPresent(at(meal.date), "evening");
    if (!allowed) return sum;
    return sum + (meal.kind === "lunch" ? extras.lunchCents : extras.dinnerCents);
  }, 0);
  const activities = extras.activities.reduce(
    (sum, activity) =>
      isPresent(at(activity.date), activity.period) ? sum + activity.price_cents : sum,
    0,
  );
  return meals + activities;
}
