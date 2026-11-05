import { computeFee } from "./money";

export type SlotInfo = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number | null;
  // null means no limit (the evening)
  available: number | null;
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
export const hhmm = (time: string) => time.slice(0, 5);

const STATUS_LABELS: Record<string, string> = {
  in_attesa_pagamento: "In attesa di pagamento",
  confermata: "Confermata",
  scaduta: "Scaduta",
  disdetta_richiesta: "Disdetta richiesta",
  rimborsata: "Rimborsata",
};
export const statusLabel = (status: string) => STATUS_LABELS[status] ?? status;
