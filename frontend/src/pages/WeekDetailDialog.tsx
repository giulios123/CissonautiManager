import { useEffect, useState, type RefObject } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";
import { formatDay, formatDayShort } from "../booking";
import { InfoDialog } from "../InfoDialog";
import { useT, type MessageKey } from "../i18n";
import { adminGuestPath, adminRegistrationPath } from "../routes";
import { StatusBadge } from "../StatusBadge";

export type WeekMetric =
  "morning" | "afternoon" | "evening" | "people" | "lunch" | "dinner" | "activities";

export const METRIC_LABELS: Record<WeekMetric, MessageKey> = {
  morning: "week.colMorning",
  afternoon: "week.colAfternoon",
  evening: "week.colEvening",
  people: "slots.colPeople",
  lunch: "week.colLunches",
  dinner: "week.colDinners",
  activities: "week.colActivities",
};

type DetailRow = {
  date: string | null;
  booking_id: number | null;
  guest_id: number | null;
  external: boolean;
  name: string;
  status: string | null;
  derived: boolean;
  activity_id: number | null;
  activity_title: string | null;
};
type Detail = {
  metric: WeekMetric;
  date: string | null;
  count: number;
  distinct_people: number | null;
  rows: DetailRow[];
};

/** The people or sign-ups behind one number of the week table. Read-only. */
export function WeekDetailDialog({
  metric,
  date,
  shown,
  onClose,
  onStale,
  returnFocusTo,
}: {
  metric: WeekMetric;
  date: string | null;
  /** The number that was in the table cell when the dialog was opened. */
  shown: number;
  onClose: () => void;
  /** Called when the list does not match the cell: the table must be reloaded. */
  onStale: () => void;
  returnFocusTo: RefObject<HTMLElement | null>;
}) {
  const t = useT();
  const [attempt, setAttempt] = useState(0);
  const key = `${metric}|${date ?? ""}|${attempt}`;
  // The answer is kept with the request it belongs to: a new request shows "loading" again.
  const [answer, setAnswer] = useState<{ key: string; detail: Detail | null } | null>(null);
  const current = answer?.key === key ? answer : null;
  const detail = current?.detail ?? null;
  const failed = current !== null && current.detail === null;

  useEffect(() => {
    let live = true;
    const query = new URLSearchParams({ metric });
    if (date) query.set("date", date);
    api<Detail>(`/api/admin/views/week/detail?${query}`)
      .then((result) => {
        if (!live) return;
        setAnswer({ key, detail: result });
        if (result.count !== shown) onStale();
      })
      .catch(() => live && setAnswer({ key, detail: null }));
    return () => {
      live = false;
    };
  }, [key, metric, date, shown, onStale]);

  const what = t(METRIC_LABELS[metric]);
  const title = date
    ? t("week.detailTitle", { metric: what, day: formatDay(date) })
    : t("week.detailTitleWeek", { metric: what });

  return (
    <InfoDialog title={title} onClose={onClose} returnFocusTo={returnFocusTo}>
      {failed ? (
        <>
          <p role="alert" className="notice error">
            {t("week.detailError")}
          </p>
          <p>
            <button type="button" className="secondary" onClick={() => setAttempt(attempt + 1)}>
              {t("week.detailRetry")}
            </button>
          </p>
        </>
      ) : detail === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : (
        <>
          {detail.count !== shown && (
            <p role="status" className="notice hold">
              {t("week.detailChanged", { from: shown, to: detail.count })}
            </p>
          )}
          <p>
            <strong>
              {detail.distinct_people === null
                ? t("week.detailCount", { n: detail.count })
                : t("week.detailAdhesions", { n: detail.count, m: detail.distinct_people })}
            </strong>
          </p>
          {detail.rows.length === 0 ? (
            <p>{t("week.detailEmpty")}</p>
          ) : (
            <ul>
              {detail.rows.map((row, index) => (
                <li
                  key={`${row.date}-${row.booking_id}-${row.guest_id}-${row.activity_id}-${index}`}
                >
                  {date === null && row.date && <>{formatDayShort(row.date)} · </>}
                  {row.booking_id !== null ? (
                    <Link to={adminRegistrationPath(row.booking_id)}>{row.name}</Link>
                  ) : row.guest_id !== null ? (
                    <Link to={adminGuestPath(row.guest_id)}>{row.name}</Link>
                  ) : (
                    row.name
                  )}
                  {row.activity_title && <> — {row.activity_title}</>}
                  {row.external && <small> ({t("week.detailExternal")})</small>}
                  {row.derived && <small> ({t("week.detailDerived")})</small>}{" "}
                  {row.status && <StatusBadge status={row.status} />}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </InfoDialog>
  );
}
