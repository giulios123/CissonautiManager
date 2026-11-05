import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
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

const DIET_LABELS: Record<string, string> = {
  omnivore: "Onnivoro",
  vegetarian: "Vegetariano",
  vegan: "Vegano",
  none: "Non indicato",
};
const CONTRIBUTION_LABELS: Record<string, string> = {
  talk: "Talk",
  topic: "Temi per l'unconference",
  skill: "Competenze",
};
const CHANNEL_LABELS: Record<string, string> = {
  revolut: "Revolut",
  satispay: "Satispay",
  paypal: "PayPal",
  iban: "Bonifico (IBAN)",
};
const decimal = (value: number) =>
  value.toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

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
  return (
    <div className="table-wrap">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{first}</th>
            <th scope="col">Confermate</th>
            <th scope="col">In attesa di pagamento</th>
            <th scope="col">Totale</th>
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
  const [report, setReport] = useState<Report | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Report>("/api/admin/views/report")
      .then(setReport)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="wide report">
      <h1>Report</h1>
      {failed && <p role="alert">Non riesco a caricare il report.</p>}
      {report === null ? (
        !failed && <p aria-busy="true">Caricamento…</p>
      ) : report.edition === null ? (
        <p>Nessuna edizione configurata: crea prima l&apos;edizione nelle Impostazioni.</p>
      ) : (
        <ReportBody report={report} edition={report.edition.name} />
      )}
    </main>
  );
}

function ReportBody({ report, edition }: { report: Report; edition: string }) {
  const { enrollment, presence, meals, revenue, waitlist } = report;
  const money = (label: string, cents: number, sub = false) => ({
    key: label,
    label: sub ? <span className="indent">{label}</span> : label,
    value: formatEuro(cents),
  });

  return (
    <>
      <p>
        {edition}. I numeri dell&apos;edizione in una pagina: guardala qui, stampala o scarica il
        CSV. Presenze, pasti e attività contano chi ha un posto, con le prenotazioni confermate
        separate da quelle ancora in attesa di pagamento.
      </p>
      <p className="no-print">
        <CsvButton path="/api/admin/views/report" />
      </p>

      <Section id="sec-enrollment" title="Iscrizioni">
        <CountTable
          caption="Prenotazioni per stato"
          first="Stato"
          second="Prenotazioni"
          rows={[
            ...Object.entries(enrollment.by_status).map(([status, count]) => ({
              key: status,
              label: <StatusBadge status={status} />,
              value: count,
            })),
            {
              key: "people",
              label: "Persone con un posto",
              value: enrollment.people_with_seat,
            },
          ]}
        />
      </Section>

      <Section id="sec-presence" title="Presenze">
        <SplitTable
          caption="Presenti per giorno e slot"
          first="Giorno e slot"
          rows={presence.slots.map((slot) => ({
            key: `${slot.day}-${slot.period}`,
            label: (
              <>
                {formatDay(slot.day)}, {periodLabel(slot.period).toLowerCase()}
                {slot.derived > 0 && (
                  <small> (di cui {slot.derived} per l&apos;intero giorno)</small>
                )}
              </>
            ),
            split: slot.present,
          }))}
          footer={{ label: "Giorni-persona", split: presence.person_days }}
        />
        <dl>
          <dt>Picco di presenti in uno slot</dt>
          <dd>{presence.peak}</dd>
          <dt>Media di presenti per slot di mattina e pomeriggio</dt>
          <dd>{decimal(presence.average_per_daytime_slot)}</dd>
        </dl>
      </Section>

      <Section id="sec-meals" title="Pasti">
        <SplitTable
          caption="Pranzi e cene per giorno"
          first="Giorno e pasto"
          rows={meals.days.flatMap((day) => [
            { key: `${day.day}-l`, label: `${formatDay(day.day)}, pranzo`, split: day.lunches },
            { key: `${day.day}-d`, label: `${formatDay(day.day)}, cena`, split: day.dinners },
          ])}
        />
        <p>
          Pranzi in totale: <strong>{meals.lunches.total}</strong> ({meals.lunches.confirmed}{" "}
          confermati, {meals.lunches.pending} in attesa). Cene in totale:{" "}
          <strong>{meals.dinners.total}</strong> ({meals.dinners.confirmed} confermate,{" "}
          {meals.dinners.pending} in attesa).
        </p>
        <div className="table-wrap">
          <table>
            <caption>Persone per regime alimentare</caption>
            <thead>
              <tr>
                <th scope="col">Regime</th>
                <th scope="col">A pranzo</th>
                <th scope="col">A cena</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(DIET_LABELS).map((key) => (
                <tr key={key}>
                  <th scope="row">{DIET_LABELS[key]}</th>
                  <td>{meals.lunch_diets[key] ?? 0}</td>
                  <td>{meals.dinner_diets[key] ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          Persone con allergie o intolleranze: <strong>{meals.people_with_allergies}</strong>. Chi
          sono e cosa hanno lo trovi solo in «Pasti», perché sono dati sanitari.
        </p>
      </Section>

      <Section id="sec-activities" title="Attività">
        {report.activities.length === 0 ? (
          <p>Nessuna attività.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <caption>Adesioni e incasso atteso per attività</caption>
              <thead>
                <tr>
                  <th scope="col">Attività</th>
                  <th scope="col">Prezzo</th>
                  <th scope="col">Capienza</th>
                  <th scope="col">Confermate</th>
                  <th scope="col">In attesa di pagamento</th>
                  <th scope="col">Totale</th>
                  <th scope="col">Incasso atteso</th>
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
                      {activity.price_cents === 0 ? "gratuita" : formatEuro(activity.price_cents)}
                    </td>
                    <td>{activity.capacity ?? "senza limite"}</td>
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

      <Section id="sec-contributions" title="Contributi">
        <CountTable
          caption="Contributi offerti"
          first="Tipo"
          second="Numero"
          rows={Object.entries(report.contributions).map(([kind, count]) => ({
            key: kind,
            label: CONTRIBUTION_LABELS[kind] ?? kind,
            value: count,
          }))}
        />
      </Section>

      <Section id="sec-waitlist" title="Lista d'attesa">
        <CountTable
          caption="Voci delle liste d'attesa (una per slot)"
          first="Voce"
          second="Numero"
          rows={[
            { key: "waiting", label: "Ancora in lista", value: waitlist.waiting },
            { key: "promoted", label: "Promossi", value: waitlist.promoted },
            {
              key: "plus",
              label: <span className="indent">di cui +1 verificati</span>,
              value: waitlist.promoted_plus_one,
            },
            { key: "left", label: "Usciti da soli", value: waitlist.left },
            { key: "removed", label: "Tolti da un admin", value: waitlist.removed },
            { key: "cancelled", label: "Annullati per disdetta", value: waitlist.cancelled },
            { key: "booked", label: "Prenotati per altra via", value: waitlist.booked },
          ]}
        />
      </Section>

      <Section id="sec-revenue" title="Incassi">
        <CountTable
          caption="Quanto è dovuto, versato e ancora da incassare"
          first="Voce"
          second="Importo"
          rows={[
            money("Totale dovuto", revenue.due_cents),
            money("quota di partecipazione", revenue.due_fee_cents, true),
            money("pasti", revenue.due_meals_cents, true),
            money("attività", revenue.due_activities_cents, true),
            ...(revenue.due_difference_cents !== 0
              ? [
                  money(
                    "differenza di prezzi cambiati dopo le iscrizioni",
                    revenue.due_difference_cents,
                    true,
                  ),
                ]
              : []),
            money("Versato", revenue.paid_cents),
            ...Object.entries(revenue.paid_by_channel).map(([channel, cents]) =>
              money(CHANNEL_LABELS[channel] ?? channel, cents, true),
            ),
            money("Rimborsato", revenue.refunded_cents),
            money("Netto (versato meno rimborsato)", revenue.net_cents),
            money("Ancora da incassare", revenue.to_collect_cents),
            money("Crediti da restituire", revenue.credits_cents),
            money("Disdette da rimborsare", revenue.to_refund_cents),
          ]}
        />
      </Section>
    </>
  );
}
