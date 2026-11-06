import { useEffect, useState } from "react";
import { api } from "../api";
import { formatDay } from "../booking";
import { useT } from "../i18n";
import { CsvButton } from "./CsvButton";

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
};

export function AdminWeek() {
  const t = useT();
  const [week, setWeek] = useState<Week | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Week>("/api/admin/views/week")
      .then(setWeek)
      .catch(() => setFailed(true));
  }, []);

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
                    <th scope="row">{formatDay(day.date)}</th>
                    <td>{day.morning}</td>
                    <td>{day.afternoon}</td>
                    <td>
                      {day.evening}
                      {day.evening_derived > 0 && (
                        <small>{t("week.derived", { n: day.evening_derived })}</small>
                      )}
                    </td>
                    <td>{day.people}</td>
                    <td>{day.lunches ?? 0}</td>
                    <td>{day.dinners ?? 0}</td>
                    <td>{day.activities ?? 0}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colSpan={4}>
                    {t("week.totals")}
                  </th>
                  <td>{week.total_people}</td>
                  <td>{week.total_lunches ?? 0}</td>
                  <td>{week.total_dinners ?? 0}</td>
                  <td>{week.total_activities ?? 0}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
