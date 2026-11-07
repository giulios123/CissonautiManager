import { periodLabel } from "./booking";
import type { Locale } from "./i18n";
import { translatePlural } from "./i18n/messages";

export type PresenceSlot = { date: string; period: string };
export type ScheduleSlot = {
  date: string;
  period: string;
  start_time: string;
  end_time: string;
};

const PERIOD_ORDER = ["morning", "afternoon", "evening"];

export function summarizePresences(slots: PresenceSlot[]) {
  const days = new Map<string, Set<string>>();
  for (const slot of slots) {
    const periods = days.get(slot.date) ?? new Set<string>();
    periods.add(slot.period);
    days.set(slot.date, periods);
  }
  return [...days.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, periods]) => {
      const ordered = PERIOD_ORDER.filter((period) => periods.has(period));
      return {
        date,
        periods: ordered,
        complete: periods.has("morning") && periods.has("afternoon"),
      };
    });
}

export function presenceCount(locale: Locale, count: number) {
  return translatePlural(locale, "presence.days", count);
}

export function scheduleForPresences(slots: PresenceSlot[], schedule: ScheduleSlot[]) {
  const days = summarizePresences(slots);
  const periodsByDate = new Map(
    days.map((day) => [day.date, new Set([...day.periods, ...(day.complete ? ["evening"] : [])])]),
  );
  return schedule.filter((slot) => periodsByDate.get(slot.date)?.has(slot.period));
}

export function formatScheduleLegend(schedule: ScheduleSlot[], locale: Locale): string[] {
  const dates = [...new Set(schedule.map((slot) => slot.date))].sort();
  const lines: string[] = [];
  for (const period of PERIOD_ORDER) {
    const groups = new Map<string, string[]>();
    for (const slot of schedule.filter((item) => item.period === period)) {
      const time = `${slot.start_time.slice(0, 5)}–${slot.end_time.slice(0, 5)}`;
      groups.set(time, [...(groups.get(time) ?? []), slot.date]);
    }
    for (const [time, periodDates] of groups) {
      const showDates = groups.size > 1 || periodDates.length < dates.length;
      const formattedDates = periodDates
        .map((date) =>
          new Intl.DateTimeFormat(locale === "it" ? "it-IT" : "en-GB", {
            day: "numeric",
            month: "short",
            timeZone: "UTC",
          })
            .format(new Date(`${date}T00:00:00Z`))
            .replace(/\./g, ""),
        )
        .join(", ");
      lines.push(`${periodLabel(period)} ${time}${showDates ? ` (${formattedDates})` : ""}`);
    }
  }
  return lines;
}
