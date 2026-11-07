import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
import { useT, type MessageKey } from "../i18n";
import { intlTag } from "../i18n/locale";
import { formatDay, periodLabel } from "../booking";
import { formatEuro } from "../money";
import { StatusBadge } from "../StatusBadge";
import { CsvButton } from "./CsvButton";

type Split = { confirmed: number; pending: number; total: number };
type Report = {
  edition: { name: string; start_date: string | null; end_date: string | null } | null;
  enrollment: { by_status: Record<string, number>; people_with_seat: number };
  presence: {
    slots: { day: string; period: string; present: Split; derived: number }[];
    peak: number;
    average_per_daytime_slot: number;
    person_days: Split;
  };
  meals: {
    days: { day: string; lunches: Split; dinners: Split }[];
    lunches: Split;
    dinners: Split;
    lunch_diets: Record<string, number>;
    dinner_diets: Record<string, number>;
    people_with_allergies: number;
  };
  activities: {
    id: number;
    title: string;
    day: string;
    period: string;
    price_cents: number;
    capacity: number | null;
    joined: Split;
    expected_cents: number;
    payment_mode?: string;
  }[];
  contributions: Record<string, number>;
  waitlist: {
    waiting: number;
    promoted: number;
    promoted_plus_one: number;
    left: number;
    removed: number;
    cancelled: number;
    booked: number;
  };
  revenue: {
    due_cents: number;
    due_fee_cents: number;
    due_meals_cents: number;
    due_activities_cents: number;
    due_difference_cents: number;
    paid_cents: number;
    paid_by_channel: Record<string, number>;
    refunded_cents: number;
    net_cents: number;
    to_collect_cents: number;
    credits_cents: number;
    to_refund_cents: number;
  };
};

const DIET_LABELS: Record<string, MessageKey> = {
  omnivore: "rep.dietOmnivore",
  vegetarian: "rep.dietVegetarian",
  vegan: "rep.dietVegan",
  none: "rep.dietNone",
};
const CONTRIBUTION_LABELS: Record<string, MessageKey> = {
  talk: "rep.contribTalk",
  topic: "rep.contribTopic",
  skill: "rep.contribSkill",
};
const CHANNEL_LABELS: Record<string, MessageKey> = {
  revolut: "channel.revolut",
  satispay: "channel.satispay",
  paypal: "channel.paypal",
  iban: "channel.iban",
};
const decimal = (value: number) =>
  value.toLocaleString(intlTag(), { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section aria-labelledby={id} className="report-section">
      <h2 id={id}>{title}</h2>
      {children}
    </section>
  );
}

/** Rows that carry a confirmed / pending / total count. */
function SplitTable({
  caption,
  first,
  rows,
  footer,
}: {
  caption: string;
  first: string;
  rows: { key: string; label: ReactNode; split: Split }[];
  footer?: { label: string; split: Split };
}) {
  const t = useT();
  return (
    <div className="table-wrap">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{first}</th>
            <th scope="col">{t("rep.confirmed")}</th>
            <th scope="col">{t("rep.pending")}</th>
            <th scope="col">{t("rep.total")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <th scope="row">{row.label}</th>
              <td>{row.split.confirmed}</td>
              <td>{row.split.pending}</td>
              <td>{row.split.total}</td>
            </tr>
          ))}
        </tbody>
        {footer && (
          <tfoot>
            <tr>
              <th scope="row">{footer.label}</th>
              <td>{footer.split.confirmed}</td>
              <td>{footer.split.pending}</td>
              <td>{footer.split.total}</td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

function CountTable({
  caption,
  first,
  second,
  rows,
}: {
  caption: string;
  first: string;
  second: string;
  rows: { key: string; label: ReactNode; value: ReactNode }[];
}) {
  return (
    <div className="table-wrap">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{first}</th>
            <th scope="col">{second}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <th scope="row">{row.label}</th>
              <td>{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminReport() {
  const t = useT();
  const [report, setReport] = useState<Report | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Report>("/api/admin/views/report")
      .then(setReport)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide report">
      <h1>{t("rep.title")}</h1>
      {failed && <p role="alert">{t("rep.loadError")}</p>}
      {report === null ? (
        !failed && <p aria-busy="true">{t("common.loading")}</p>
      ) : report.edition === null ? (
        <p>{t("rep.noEdition")}</p>
      ) : (
        <ReportBody report={report} edition={report.edition.name} />
      )}
    </main>
  );
}

function ReportBody({ report, edition }: { report: Report; edition: string }) {
  const t = useT();
  const { enrollment, presence, meals, revenue, waitlist } = report;
  const money = (label: string, cents: number, sub = false) => ({
    key: label,
    label: sub ? <span className="indent">{label}</span> : label,
    value: formatEuro(cents),
  });

  return (
    <>
      <p>{t("rep.intro", { edition })}</p>
      <p className="no-print">
        <CsvButton path="/api/admin/views/report" />
      </p>

      <Section id="sec-enrollment" title={t("rep.secEnrollment")}>
        <CountTable
          caption={t("rep.byStatusCaption")}
          first={t("rep.colStatus")}
          second={t("rep.colBookings")}
          rows={[
            ...Object.entries(enrollment.by_status).map(([status, count]) => ({
              key: status,
              label: <StatusBadge status={status} />,
              value: count,
            })),
            {
              key: "people",
              label: t("rep.peopleWithSeat"),
              value: enrollment.people_with_seat,
            },
          ]}
        />
      </Section>

      <Section id="sec-presence" title={t("rep.secPresence")}>
        <SplitTable
          caption={t("rep.presenceCaption")}
          first={t("rep.dayAndSlot")}
          rows={presence.slots.map((slot) => ({
            key: `${slot.day}-${slot.period}`,
            label: (
              <>
                {formatDay(slot.day)}, {periodLabel(slot.period).toLowerCase()}
                {slot.derived > 0 && <small>{t("week.derived", { n: slot.derived })}</small>}
              </>
            ),
            split: slot.present,
          }))}
          footer={{ label: t("rep.personDays"), split: presence.person_days }}
        />
        <dl>
          <dt>{t("rep.peak")}</dt>
          <dd>{presence.peak}</dd>
          <dt>{t("rep.average")}</dt>
          <dd>{decimal(presence.average_per_daytime_slot)}</dd>
        </dl>
      </Section>

      <Section id="sec-meals" title={t("rep.secMeals")}>
        <SplitTable
          caption={t("rep.mealsCaption")}
          first={t("rep.dayAndMeal")}
          rows={meals.days.flatMap((day) => [
            {
              key: `${day.day}-l`,
              label: t("rep.dayLunch", { day: formatDay(day.day) }),
              split: day.lunches,
            },
            {
              key: `${day.day}-d`,
              label: t("rep.dayDinner", { day: formatDay(day.day) }),
              split: day.dinners,
            },
          ])}
        />
        <p>
          {t("rep.mealTotals", {
            lunches: meals.lunches.total,
            lunchConfirmed: meals.lunches.confirmed,
            lunchPending: meals.lunches.pending,
            dinners: meals.dinners.total,
            dinnerConfirmed: meals.dinners.confirmed,
            dinnerPending: meals.dinners.pending,
          })}
        </p>
        <div className="table-wrap">
          <table>
            <caption>{t("rep.dietsCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("rep.colDiet")}</th>
                <th scope="col">{t("rep.atLunch")}</th>
                <th scope="col">{t("rep.atDinner")}</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(DIET_LABELS).map((key) => (
                <tr key={key}>
                  <th scope="row">{t(DIET_LABELS[key])}</th>
                  <td>{meals.lunch_diets[key] ?? 0}</td>
                  <td>{meals.dinner_diets[key] ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>{t("rep.allergies", { n: meals.people_with_allergies })}</p>
      </Section>

      <Section id="sec-activities" title={t("rep.secActivities")}>
        {report.activities.length === 0 ? (
          <p>{t("rep.noActivities")}</p>
        ) : (
          <div className="table-wrap">
            <table>
              <caption>{t("rep.activitiesCaption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("aact.colActivity")}</th>
                  <th scope="col">{t("aact.colPrice")}</th>
                  <th scope="col">{t("rep.colCapacity")}</th>
                  <th scope="col">{t("rep.confirmed")}</th>
                  <th scope="col">{t("rep.pending")}</th>
                  <th scope="col">{t("rep.total")}</th>
                  <th scope="col">{t("rep.colExpected")}</th>
                </tr>
              </thead>
              <tbody>
                {report.activities.map((activity) => (
                  <tr key={activity.id}>
                    <th scope="row">
                      {activity.title}
                      <br />
                      <small>
                        {formatDay(activity.day)}, {periodLabel(activity.period).toLowerCase()}
                      </small>
                    </th>
                    <td>
                      {activity.price_cents === 0
                        ? t("activity.free")
                        : formatEuro(activity.price_cents)}
                      {activity.payment_mode === "provider" && (
                        <>
                          <br />
                          <small>{t("collection.provider")}</small>
                        </>
                      )}
                    </td>
                    <td>{activity.capacity ?? t("slots.unlimited")}</td>
                    <td>{activity.joined.confirmed}</td>
                    <td>{activity.joined.pending}</td>
                    <td>{activity.joined.total}</td>
                    <td>{formatEuro(activity.expected_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section id="sec-contributions" title={t("rep.secContributions")}>
        <CountTable
          caption={t("rep.contribCaption")}
          first={t("contrib.type")}
          second={t("rep.colNumber")}
          rows={Object.entries(report.contributions).map(([kind, count]) => ({
            key: kind,
            label: CONTRIBUTION_LABELS[kind] ? t(CONTRIBUTION_LABELS[kind]) : kind,
            value: count,
          }))}
        />
      </Section>

      <Section id="sec-waitlist" title={t("rep.secWaitlist")}>
        <CountTable
          caption={t("rep.waitlistCaption")}
          first={t("rep.colEntry")}
          second={t("rep.colNumber")}
          rows={[
            { key: "waiting", label: t("rep.stillWaiting"), value: waitlist.waiting },
            { key: "promoted", label: t("rep.promoted"), value: waitlist.promoted },
            {
              key: "plus",
              label: <span className="indent">{t("rep.promotedPlusOne")}</span>,
              value: waitlist.promoted_plus_one,
            },
            { key: "left", label: t("rep.leftAlone"), value: waitlist.left },
            { key: "removed", label: t("rep.removedByAdmin"), value: waitlist.removed },
            { key: "cancelled", label: t("rep.cancelled"), value: waitlist.cancelled },
            { key: "booked", label: t("rep.booked"), value: waitlist.booked },
          ]}
        />
      </Section>

      <Section id="sec-revenue" title={t("rep.secRevenue")}>
        <CountTable
          caption={t("rep.revenueCaption")}
          first={t("rep.colEntry")}
          second={t("rep.colAmount")}
          rows={[
            money(t("rep.totalDue"), revenue.due_cents),
            money(t("rep.dueFee"), revenue.due_fee_cents, true),
            money(t("rep.dueMeals"), revenue.due_meals_cents, true),
            money(t("rep.dueActivities"), revenue.due_activities_cents, true),
            ...(revenue.due_difference_cents !== 0
              ? [money(t("rep.dueDifference"), revenue.due_difference_cents, true)]
              : []),
            money(t("rep.paidWord"), revenue.paid_cents),
            ...Object.entries(revenue.paid_by_channel).map(([channel, cents]) =>
              money(CHANNEL_LABELS[channel] ? t(CHANNEL_LABELS[channel]) : channel, cents, true),
            ),
            money(t("rep.refundedWord"), revenue.refunded_cents),
            money(t("rep.net"), revenue.net_cents),
            money(t("rep.toCollect"), revenue.to_collect_cents),
            money(t("rep.credits"), revenue.credits_cents),
            money(t("rep.toRefund"), revenue.to_refund_cents),
          ]}
        />
      </Section>
    </>
  );
}
