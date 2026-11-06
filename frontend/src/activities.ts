import { tNow } from "./i18n/messages";
import { formatEuro } from "./money";

export type Activity = {
  id: number;
  title: string;
  description: string | null;
  date: string;
  period: "morning" | "afternoon" | "evening";
  time_label: string | null;
  price_cents: number;
  capacity: number | null;
  joined: number;
  free: number | null;
};

export const priceLabel = (cents: number) =>
  cents === 0 ? tNow("activity.free") : formatEuro(cents);

export function seatsLabel(activity: { capacity: number | null; joined: number }) {
  return activity.capacity === null
    ? tNow("activity.signedUpNoLimit", { joined: activity.joined })
    : `${activity.joined} / ${activity.capacity}`;
}

/** Every day from start to end, as YYYY-MM-DD. */
export function editionDays(start: string | null, end: string | null): string[] {
  if (!start || !end) return [];
  const days: string[] = [];
  for (let d = new Date(`${start}T00:00:00Z`); d <= new Date(`${end}T00:00:00Z`);) {
    days.push(d.toISOString().slice(0, 10));
    d = new Date(d.getTime() + 86_400_000);
  }
  return days;
}
