import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { formatDay } from "../booking";
import { useT } from "../i18n";
import { useRefreshOnReturn } from "../useRefreshOnReturn";
import { CsvButton } from "./CsvButton";
import { METRIC_LABELS, WeekDetailDialog, type WeekMetric } from "./WeekDetailDialog";

type DayRow = {
  date: string;
  morning: number;
  afternoon: number;
  evening: number;
  evening_derived: number;
  people: number;
  lunches?: number;
  dinners?: number;
  activities?: number;
};
type Week = {
  days: DayRow[];
  total_people: number;
  total_lunches?: number;
  total_dinners?: number;
  total_activities?: number;
  today?: string | null;
};

export function AdminWeek() {
  const t = useT();
  const [week, setWeek] = useState<Week | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<{ metric: WeekMetric; date: string | null; n: number } | null>(
    null,
  );
  const clickedRef = useRef<HTMLButtonElement | null>(null);

  const load = useCallback(() => {
    api<Week>("/api/admin/views/week")
      .then(setWeek)
      .catch(() => setFailed(true));
  }, []);

  useEffect(load, [load]);
  // A dialog open on a number is never closed or reloaded under the organiser.
  useRefreshOnReturn(load, () => open !== null);

  /** A number of the table: a real button that opens the list behind it. */
  function number(metric: WeekMetric, date: string | null, n: number) {
    const what = t(METRIC_LABELS[metric]);
    const label = date
      ? t("week.detailLabel", { metric: what, day: formatDay(date), n })
      : t("week.detailLabelWeek", { metric: what, n });
    return (
      <button
        type="button"
        className="number"
        aria-label={label}
        onClick={(event) => {
          clickedRef.current = event.currentTarget;
          setOpen({ metric, date, n });
        }}
      >
        {n}
      </button>
    );
  }

  return (
    <main className="wide">
      <h1>{t("week.title")}</h1>
      <p>{t("week.intro")}</p>
      {failed && <p role="alert">{t("slots.loadError")}</p>}
      {week === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : week.days.length === 0 ? (
        <p>{t("week.noDays")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/week" />
          </p>
          <div className="table-wrap">
            <table>
              <caption>{t("week.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("week.colDay")}</th>
                  <th scope="col">{t("week.colMorning")}</th>
                  <th scope="col">{t("week.colAfternoon")}</th>
                  <th scope="col">{t("week.colEvening")}</th>
                  <th scope="col">{t("slots.colPeople")}</th>
                  <th scope="col">{t("week.colLunches")}</th>
                  <th scope="col">{t("week.colDinners")}</th>
                  <th scope="col">{t("week.colActivities")}</th>
                </tr>
              </thead>
              <tbody>
                {week.days.map((day) => (
                  <tr key={day.date}>
                    <th scope="row">
                      {formatDay(day.date)}
                      {day.date === week.today && (
                        <>
                          {" "}
                          <span className="tag">{t("views.today")}</span>
                        </>
                      )}
                    </th>
                    <td>{number("morning", day.date, day.morning)}</td>
                    <td>{number("afternoon", day.date, day.afternoon)}</td>
                    <td>
                      {number("evening", day.date, day.evening)}
                      {day.evening_derived > 0 && (
                        <small>{t("week.derived", { n: day.evening_derived })}</small>
                      )}
                    </td>
                    <td>{number("people", day.date, day.people)}</td>
                    <td>{number("lunch", day.date, day.lunches ?? 0)}</td>
                    <td>{number("dinner", day.date, day.dinners ?? 0)}</td>
                    <td>{number("activities", day.date, day.activities ?? 0)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colSpan={4}>
                    {t("week.totals")}
                  </th>
                  <td>{number("people", null, week.total_people)}</td>
                  <td>{number("lunch", null, week.total_lunches ?? 0)}</td>
                  <td>{number("dinner", null, week.total_dinners ?? 0)}</td>
                  <td>{number("activities", null, week.total_activities ?? 0)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </>
      )}
      {open && (
        <WeekDetailDialog
          metric={open.metric}
          date={open.date}
          shown={open.n}
          onClose={() => setOpen(null)}
          onStale={load}
          returnFocusTo={clickedRef}
        />
      )}
    </main>
  );
}
