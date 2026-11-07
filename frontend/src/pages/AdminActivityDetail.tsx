import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { useI18n } from "../i18n";
import { adminRegistrationPath, ROUTES } from "../routes";
import { CsvButton } from "./CsvButton";
import { CollectionDetails } from "../collection";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  status: string;
};
type Detail = Activity & { people: Person[] };

export function AdminActivityDetail() {
  const { t, tn } = useI18n();
  const { id } = useParams();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Detail>(`/api/admin/activities/${id}`)
      .then(setDetail)
      .catch(() => setFailed(true));
  }, [id]);

  if (failed) return <main role="alert">{t("aact.notFound")}</main>;
  if (!detail) return <main aria-busy="true">{t("common.loading")}</main>;

  return (
    <main className="wide">
      <p>
        <Link to={ROUTES.adminActivities}>{t("aact.backAll")}</Link>
      </p>
      <h1>{detail.title}</h1>
      <p>
        {formatDay(detail.date)}, {periodLabel(detail.period).toLowerCase()}
        {detail.time_label && ` (${detail.time_label})`} · {priceLabel(detail.price_cents)} ·{" "}
        {seatsLabel(detail)}
        {detail.free !== null && tn("aact.freePlaces", detail.free)}
      </p>
      {detail.description && <p>{detail.description}</p>}
      <CollectionDetails terms={detail} />
      {detail.people.length === 0 ? (
        <p>{t("aact.noneSignedUp")}</p>
      ) : (
        <>
          <p>
            <CsvButton path={`/api/admin/activities/${detail.id}`} />
          </p>
          <div className="table-wrap">
            <table>
              <caption>{t("aact.signedUpCaption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("people.colPerson")}</th>
                  <th scope="col">{t("people.colPhone")}</th>
                  <th scope="col">{t("people.colStatus")}</th>
                </tr>
              </thead>
              <tbody>
                {detail.people.map((person) => (
                  <tr key={person.booking_id}>
                    <th scope="row">
                      <Link to={adminRegistrationPath(person.booking_id)}>
                        {person.first_name} {person.last_name}
                      </Link>
                      <br />
                      <small>{person.email}</small>
                    </th>
                    <td>{person.phone ?? "-"}</td>
                    <td>
                      <StatusBadge status={person.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
