import { computeFee } from "./money";

export type SlotInfo = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number;
  available: number;
};
export type Day = { date: string; slots: SlotInfo[] };

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

const dayFormat = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "UTC",
});
const deadlineFormat = new Intl.DateTimeFormat("it-IT", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "Europe/Rome",
});

export const formatDay = (isoDate: string) => dayFormat.format(new Date(`${isoDate}T00:00:00Z`));
export const formatDeadline = (isoDateTime: string) => deadlineFormat.format(new Date(isoDateTime));
export const periodLabel = (period: string) => (period === "morning" ? "Mattina" : "Pomeriggio");
export const hhmm = (time: string) => time.slice(0, 5);
