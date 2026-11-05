import { useId, type ReactNode } from "react";
import { dayBadge, formatDay, formatWeekday, hhmm, periodLabel } from "../booking";
import { useT } from "../i18n";
import type { MessageKey } from "../i18n";
import {
  allSlots,
  clearAll,
  isFullySelected,
  selectAll,
  slotsOfPeriod,
  toggleBulk,
  type PickerDay,
  type PickerSlot,
} from "../daySelection";

const ICON_PROPS = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
} as const;

/** Line icons in the style of the sun mark: 1.75 px stroke, rounded caps. */
export function PeriodIcon({ period }: { period: string }) {
  if (period === "evening")
    return (
      <svg {...ICON_PROPS}>
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
      </svg>
    );
  if (period === "afternoon")
    return (
      <svg {...ICON_PROPS}>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
      </svg>
    );
  return (
    <svg {...ICON_PROPS}>
      <path d="M12 2v8M4.93 10.93l1.41 1.41M2 18h2M20 18h2M19.07 10.93l-1.41 1.41M22 22H2M8 6l4-4 4 4M16 18a4 4 0 0 0-8 0" />
    </svg>
  );
}

const QUICK: { period: string; label: MessageKey }[] = [
  { period: "morning", label: "picker.allMorning" },
  { period: "afternoon", label: "picker.allAfternoon" },
  { period: "evening", label: "picker.allEvening" },
];

/**
 * Day by day choice of slots. Each slot is a tile you click anywhere to select; a day has a
 * "Tutta la giornata" button and the top has quick choices by part of the day.
 */
export function DayPicker({
  days,
  selected,
  onChange,
  children,
}: {
  days: PickerDay[];
  selected: Set<number>;
  onChange: (next: Set<number>) => void;
  /** Shown above the days, next to the quick choices (e.g. a legend). */
  children?: ReactNode;
}) {
  const t = useT();
  const baseId = useId();
  const everything = allSlots(days);

  function toggleOne(slot: PickerSlot, checked: boolean) {
    const next = new Set(selected);
    if (checked) next.add(slot.id);
    else next.delete(slot.id);
    onChange(next);
  }

  return (
    <div className="day-picker">
      <div className="quick">
        <span className="quick-title" id={`${baseId}-quick`}>
          {t("picker.quickTitle")}
        </span>
        <div className="quick-actions" aria-labelledby={`${baseId}-quick`}>
          {QUICK.map(({ period, label }) => {
            const slots = slotsOfPeriod(days, period);
            return (
              <button
                key={period}
                type="button"
                className="chip"
                aria-pressed={isFullySelected(slots, selected)}
                onClick={() => onChange(toggleBulk(slots, selected))}
              >
                <PeriodIcon period={period} />
                {t(label)}
              </button>
            );
          })}
          <button
            type="button"
            className="chip"
            onClick={() => onChange(selectAll(days, selected))}
          >
            {t("picker.selectAll")}
          </button>
          <button
            type="button"
            className="chip"
            onClick={() => onChange(clearAll(days, selected))}
            disabled={everything.every((slot) => slot.disabled || !selected.has(slot.id))}
          >
            {t("picker.clearAll")}
          </button>
        </div>
      </div>
      {children}
      {days.map((day) => {
        const labelId = `${baseId}-${day.date}`;
        const badge = dayBadge(day.date);
        const whole = isFullySelected(day.slots, selected);
        return (
          <div className="day" role="group" aria-labelledby={labelId} key={day.date}>
            <div className="day-head">
              <span className="day-badge" aria-hidden="true">
                <span>{badge.month}</span>
                <strong>{badge.day}</strong>
              </span>
              <span className="day-name" id={labelId}>
                {formatWeekday(day.date)}
                <span className="sr-only"> {formatDay(day.date)}</span>
              </span>
            </div>
            <div className="tiles">
              {day.slots.map((slot) => {
                const checked = selected.has(slot.id);
                const name = `${periodLabel(slot.period)} ${hhmm(slot.start_time)}-${hhmm(slot.end_time)} · ${slot.hint}`;
                return (
                  <label
                    className={`tile${checked ? " is-on" : ""}${slot.disabled ? " is-off" : ""}`}
                    key={slot.id}
                  >
                    <input
                      type="checkbox"
                      aria-label={name}
                      checked={checked}
                      disabled={slot.disabled}
                      onChange={(e) => toggleOne(slot, e.target.checked)}
                    />
                    <span className="tile-icon">
                      <PeriodIcon period={slot.period} />
                    </span>
                    <span className="tile-body" aria-hidden="true">
                      <span className="tile-title">{periodLabel(slot.period)}</span>
                      <span className="tile-time mono">
                        {hhmm(slot.start_time)} – {hhmm(slot.end_time)}
                      </span>
                      <span className="tile-hint">{slot.hint}</span>
                    </span>
                  </label>
                );
              })}
            </div>
            <button
              type="button"
              className="secondary day-all"
              aria-pressed={whole}
              disabled={!day.slots.some((slot) => !slot.disabled)}
              onClick={() => onChange(toggleBulk(day.slots, selected))}
            >
              {t("picker.wholeDay")}
              <span className="sr-only">
                {t("picker.wholeDayOf", { day: formatDay(day.date) })}
              </span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
