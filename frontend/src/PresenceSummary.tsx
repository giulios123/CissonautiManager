import { formatDayShort, periodLabel } from "./booking";
import { useI18n } from "./i18n";
import {
  formatScheduleLegend,
  presenceCount,
  scheduleForPresences,
  summarizePresences,
} from "./presence-summary";
import type { PresenceSlot, ScheduleSlot } from "./presence-summary";

export function PresenceSummary({
  slots,
  schedule,
  className = "",
}: {
  slots: PresenceSlot[];
  schedule: ScheduleSlot[];
  className?: string;
}) {
  const { t, locale } = useI18n();
  const days = summarizePresences(slots);
  if (days.length === 0) return null;
  const bookedSchedule = scheduleForPresences(slots, schedule);

  return (
    <section className={`presence-summary ${className}`} aria-label={t("presence.heading")}>
      <h2>
        {t("presence.heading")}{" "}
        <span aria-live="polite">· {presenceCount(locale, days.length)}</span>
      </h2>
      <p className="presence-note">{t("presence.note")}</p>
      <ul className="plain presence-days">
        {days.map((day) => (
          <li key={day.date}>
            <strong>{formatDayShort(day.date)}</strong>
            {!day.complete && (
              <span className="presence-periods">
                {day.periods.map((period) => periodLabel(period)).join(" · ")}
              </span>
            )}
            <span className="sr-only">
              {day.complete ? t("presence.fullDay") : t("presence.partialDay")}
            </span>
          </li>
        ))}
      </ul>
      <div className="presence-hours" aria-label={t("presence.hours")}>
        {formatScheduleLegend(bookedSchedule, locale).map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
    </section>
  );
}
