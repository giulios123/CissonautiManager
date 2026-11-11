import { tNow } from "./i18n/messages";
import { formatEuro } from "./money";
import type { CollectionTerms } from "./collection";

export type Activity = CollectionTerms & {
  id: number;
  title: string;
  description: string | null;
  title_it?: string | null;
  title_en?: string | null;
  description_it?: string | null;
  description_en?: string | null;
  translation_missing?: boolean;
  internal_note?: string | null;
  /** Admin only: the proposal it came from; `contribution_id` is empty once the proposal is gone. */
  source?: { contribution_id: number | null; title: string } | null;
  date: string;
  period: "morning" | "afternoon" | "evening";
  time_label: string | null;
  start_time?: string | null;
  end_time?: string | null;
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
