import { distinctDays, feePreview, formatDeadline, formatDay, type Day } from "./booking";

const slot = (id: number, period = "morning") => ({
  id,
  period,
  start_time: "09:00:00",
  end_time: "13:00:00",
  capacity: 25,
  available: 25,
});
const days: Day[] = [
  { date: "2026-07-13", slots: [slot(1), slot(2, "afternoon")] },
  { date: "2026-07-14", slots: [slot(3), slot(4, "afternoon")] },
  { date: "2026-07-15", slots: [slot(5), slot(6, "afternoon")] },
];

describe("fee preview", () => {
  it("counts a day once even with morning and afternoon", () => {
    expect(distinctDays(days, new Set([1, 2]))).toBe(1);
    expect(feePreview(days, new Set([1, 2]), 1000, 100)).toBe(1100);
  });

  it("counts non contiguous days", () => {
    expect(feePreview(days, new Set([1, 5]), 1000, 100)).toBe(1200);
  });

  it("is only the base fee with nothing selected", () => {
    expect(feePreview(days, new Set(), 1000, 100)).toBe(1000);
  });

  it("matches the backend rule for three days", () => {
    expect(feePreview(days, new Set([1, 3, 6]), 1000, 100)).toBe(1300);
  });
});

describe("date formatting", () => {
  it("shows the day name in Italian without timezone shifts", () => {
    expect(formatDay("2026-07-13")).toBe("lunedì 13 luglio");
  });

  it("shows deadlines in Rome time", () => {
    expect(formatDeadline("2026-07-04T10:00:00Z")).toContain("12:00");
  });
});
