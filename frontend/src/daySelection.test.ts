import {
  bulkTargets,
  clearAll,
  isFullySelected,
  selectAll,
  slotsOfPeriod,
  toggleBulk,
  type PickerDay,
  type PickerSlot,
} from "./daySelection";

const slot = (id: number, period: string, extra: Partial<PickerSlot> = {}): PickerSlot => ({
  id,
  period,
  start_time: "09:00:00",
  end_time: "13:00:00",
  hint: "",
  disabled: false,
  full: false,
  ...extra,
});

const days: PickerDay[] = [
  { date: "2026-11-20", slots: [slot(1, "morning"), slot(2, "afternoon", { full: true })] },
  { date: "2026-11-21", slots: [slot(3, "morning", { disabled: true }), slot(4, "afternoon")] },
];

describe("day selection", () => {
  it("skips disabled slots and full slots not yet chosen", () => {
    const all = days.flatMap((d) => d.slots);
    expect(bulkTargets(all, new Set()).map((s) => s.id)).toEqual([1, 4]);
    expect(bulkTargets(all, new Set([2])).map((s) => s.id)).toEqual([1, 2, 4]);
  });

  it("selects all targets, then deselects them on the second click", () => {
    const day = days[0].slots;
    const once = toggleBulk(day, new Set());
    expect([...once]).toEqual([1]);
    expect(isFullySelected(day, once)).toBe(true);
    expect([...toggleBulk(day, once)]).toEqual([]);
  });

  it("completes a partial selection instead of clearing it", () => {
    const day = [slot(1, "morning"), slot(2, "afternoon"), slot(3, "evening")];
    expect([...toggleBulk(day, new Set([1]))].sort()).toEqual([1, 2, 3]);
  });

  it("does nothing when no slot can be toggled", () => {
    const blocked = [slot(1, "morning", { disabled: true })];
    const start = new Set([1]);
    expect(toggleBulk(blocked, start)).toBe(start);
    expect(isFullySelected(blocked, start)).toBe(false);
  });

  it("groups slots by period across days", () => {
    expect(slotsOfPeriod(days, "morning").map((s) => s.id)).toEqual([1, 3]);
  });

  it("clears everything that can change and keeps the locked slots", () => {
    expect([...clearAll(days, new Set([1, 2, 3, 4]))]).toEqual([3]);
  });

  it("selects everything available without pulling in full or locked slots", () => {
    expect([...selectAll(days, new Set())].sort()).toEqual([1, 4]);
  });
});
