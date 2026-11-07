import { intlTag } from "./i18n/locale";
import { tNow, translatePlural } from "./i18n/messages";
import { getLocale } from "./i18n/locale";
import { computeFee } from "./money";
import { collectableCents, type CollectionTerms } from "./collection";

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
export const periodLabel = (period: string) =>
  period === "morning" || period === "afternoon" || period === "evening"
    ? tNow(`period.${period}` as const)
    : period;
export const isFull = (slot: SlotInfo) => slot.available !== null && slot.available < 1;
export const seatsLabel = (slot: SlotInfo) =>
  slot.available === null
    ? tNow("seats.unlimited")
    : slot.available < 1
      ? tNow("seats.full")
      : translatePlural(getLocale(), "seats.free", slot.available);
export const canJoinWaitlist = (slot: SlotInfo) =>
  isFull(slot) && slot.waitlist_free != null && slot.waitlist_free > 0;
export const hhmm = (time: string) => time.slice(0, 5);

const STATUSES = [
  "in_attesa_pagamento",
  "confermata",
  "scaduta",
  "disdetta_richiesta",
  "rimborsata",
  "in_lista",
] as const;
export const statusLabel = (status: string) =>
  (STATUSES as readonly string[]).includes(status)
    ? tNow(`status.${status as (typeof STATUSES)[number]}` as const)
    : status;

/** Present in that part of the day: the evening also counts for whoever has morning and
 * afternoon (D-009). */
export function isPresent(periods: Set<string>, period: string): boolean {
  if (period === "evening")
    return periods.has("evening") || (periods.has("morning") && periods.has("afternoon"));
  return periods.has(period);
}

export type PricedExtras = {
  meals: ({ date: string; kind: string } & CollectionTerms)[];
  activities: ({ date: string; period: string } & CollectionTerms)[];
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
    const defaultPrice = meal.kind === "lunch" ? extras.lunchCents : extras.dinnerCents;
    const hasCollectionTerms =
      meal.payment_mode !== undefined ||
      meal.price_cents !== undefined ||
      meal.collectable_cents !== undefined;
    return sum + (hasCollectionTerms ? collectableCents(meal) : defaultPrice);
  }, 0);
  const activities = extras.activities.reduce(
    (sum, activity) =>
      isPresent(at(activity.date), activity.period) ? sum + collectableCents(activity) : sum,
    0,
  );
  return meals + activities;
}
