/** What the day picker needs to know about a slot: already resolved by the page that uses it. */
export type PickerSlot = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  /** Short text under the time: free seats, "giorno passato", ... */
  hint: string;
  /** Cannot be toggled at all (past day, full with no waitlist, ...). */
  disabled: boolean;
  /** Full: a bulk action does not add it by surprise, only a direct click does. */
  full: boolean;
};
export type PickerDay = { date: string; slots: PickerSlot[] };

/** Slots a bulk action may touch: the enabled ones, minus the full ones not yet chosen. */
export function bulkTargets(slots: PickerSlot[], selected: Set<number>): PickerSlot[] {
  return slots.filter((slot) => !slot.disabled && (!slot.full || selected.has(slot.id)));
}

/** True when there is something to bulk-select and all of it is already selected. */
export function isFullySelected(slots: PickerSlot[], selected: Set<number>): boolean {
  const targets = bulkTargets(slots, selected);
  return targets.length > 0 && targets.every((slot) => selected.has(slot.id));
}

/** Select every target, or deselect them all when they were all selected already. */
export function toggleBulk(slots: PickerSlot[], selected: Set<number>): Set<number> {
  const targets = bulkTargets(slots, selected);
  if (targets.length === 0) return selected;
  const next = new Set(selected);
  const remove = isFullySelected(slots, selected);
  for (const slot of targets) {
    if (remove) next.delete(slot.id);
    else next.add(slot.id);
  }
  return next;
}

export const slotsOfPeriod = (days: PickerDay[], period: string): PickerSlot[] =>
  days.flatMap((day) => day.slots.filter((slot) => slot.period === period));

export const allSlots = (days: PickerDay[]): PickerSlot[] => days.flatMap((day) => day.slots);

/** Deselect every slot that can be changed; the disabled ones keep their state. */
export function clearAll(days: PickerDay[], selected: Set<number>): Set<number> {
  const next = new Set(selected);
  for (const slot of allSlots(days)) if (!slot.disabled) next.delete(slot.id);
  return next;
}

/** Add every slot a bulk action may touch. */
export function selectAll(days: PickerDay[], selected: Set<number>): Set<number> {
  const next = new Set(selected);
  for (const slot of bulkTargets(allSlots(days), selected)) next.add(slot.id);
  return next;
}
