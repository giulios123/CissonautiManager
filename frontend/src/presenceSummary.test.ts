import { describe, expect, it } from "vitest";
import {
  formatScheduleLegend,
  scheduleForPresences,
  summarizePresences,
  type ScheduleSlot,
} from "./presenceSummary";

describe("attendance summary", () => {
  it("uses one date row for morning and afternoon, and preserves non-consecutive dates", () => {
    expect(
      summarizePresences([
        { date: "2026-11-20", period: "morning" },
        { date: "2026-11-20", period: "afternoon" },
        { date: "2026-11-22", period: "evening" },
      ]),
    ).toEqual([
      { date: "2026-11-20", periods: ["morning", "afternoon"], complete: true },
      { date: "2026-11-22", periods: ["evening"], complete: false },
    ]);
  });

  it("keeps five complete days as five rows and treats all three periods like morning and afternoon", () => {
    const dates = ["2026-11-20", "2026-11-21", "2026-11-22", "2026-11-23", "2026-11-24"];
    const morningAndAfternoon = dates.flatMap((date) => [
      { date, period: "morning" },
      { date, period: "afternoon" },
    ]);
    const withEvenings = [
      ...morningAndAfternoon,
      ...dates.map((date) => ({ date, period: "evening" })),
    ];
    const days = summarizePresences(morningAndAfternoon);

    expect(days).toHaveLength(5);
    expect(days.map(({ date, complete }) => ({ date, complete }))).toEqual(
      dates.map((date) => ({ date, complete: true })),
    );
    expect(summarizePresences(withEvenings).every((day) => day.complete)).toBe(true);
  });

  it("lists each interval and the affected date when schedule times vary", () => {
    expect(
      formatScheduleLegend(
        [
          { date: "2026-11-20", period: "morning", start_time: "09:00", end_time: "13:00" },
          { date: "2026-11-21", period: "morning", start_time: "10:00", end_time: "14:00" },
          { date: "2026-11-20", period: "evening", start_time: "19:00", end_time: "00:00" },
          { date: "2026-11-21", period: "evening", start_time: "19:00", end_time: "00:00" },
        ],
        "it",
      ),
    ).toEqual(["Mattina 09:00–13:00 (20 nov)", "Mattina 10:00–14:00 (21 nov)", "Sera 19:00–00:00"]);
  });

  it("lists only booked periods, adding the derived evening for a full day", () => {
    const schedule: ScheduleSlot[] = ["morning", "afternoon", "evening"].map((period) => ({
      date: "2026-11-20",
      period,
      start_time: "09:00",
      end_time: "13:00",
    }));
    expect(scheduleForPresences([{ date: "2026-11-20", period: "morning" }], schedule)).toEqual([
      schedule[0],
    ]);
    expect(
      scheduleForPresences(
        [
          { date: "2026-11-20", period: "morning" },
          { date: "2026-11-20", period: "afternoon" },
        ],
        schedule,
      ),
    ).toEqual(schedule);
  });
});
