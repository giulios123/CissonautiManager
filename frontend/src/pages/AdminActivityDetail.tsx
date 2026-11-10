import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { StatusBadge } from "../StatusBadge";
import { useI18n } from "../i18n";
import { adminGuestPath, adminRegistrationPath, ROUTES } from "../routes";
import { CsvButton } from "./CsvButton";
import { CollectionDetails } from "../collection";
import { ApiError } from "../api";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  status: string;
};
type GuestPerson = {
  guest_id: number;
  first_name: string;
  last_name: string;
  phone: string | null;
  payer: "paying" | "non_paying";
};
type Detail = Activity & {
  people: Person[];
  guests?: GuestPerson[];
  internal_note: string | null;
  note_history: { note: string | null; author: string; created_at: string }[];
};

export function AdminActivityDetail() {
  const { t, tn } = useI18n();
  const { id } = useParams();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failed, setFailed] = useState(false);
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState("");

  useEffect(() => {
    api<Detail>(`/api/admin/activities/${id}`)
      .then((loaded) => {
        setDetail(loaded);
        setNote(loaded.internal_note ?? "");
      })
      .catch(() => setFailed(true));
  }, [id]);

  if (failed) return <main role="alert">{t("aact.notFound")}</main>;
  if (!detail) return <main aria-busy="true">{t("common.loading")}</main>;

  async function saveNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNoteError("");
    try {
      await api(`/api/admin/activities/${id}/note`, { method: "PUT", json: { note } });
      const loaded = await api<Detail>(`/api/admin/activities/${id}`);
      setDetail(loaded);
      setNote(loaded.internal_note ?? "");
    } catch (error) {
      setNoteError(error instanceof ApiError ? error.message : t("common.somethingWrong"));
    }
  }

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
      <p>
        <CsvButton path={`/api/admin/activities/${detail.id}`} />
      </p>
      <form onSubmit={saveNote}>
        <label>
          {t("aact.internalNote")}
          <textarea
            value={note}
            maxLength={5000}
            rows={4}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
        {noteError && <p role="alert">{noteError}</p>}
        <button type="submit">{t("aact.saveNote")}</button>
      </form>
      {(detail.note_history ?? []).length > 0 && (
        <section aria-labelledby="activity-note-history">
          <h2 id="activity-note-history">{t("aact.noteHistory")}</h2>
          <ul>
            {(detail.note_history ?? []).map((revision, index) => (
              <li key={`${revision.created_at}-${index}`}>
                {revision.created_at} · {revision.author} · {revision.note || t("aact.noteCleared")}
              </li>
            ))}
          </ul>
        </section>
      )}
      {detail.people.length === 0 && (detail.guests ?? []).length === 0 && (
        <p>{t("aact.noneSignedUp")}</p>
      )}
      {(detail.guests ?? []).length > 0 && (
        <div className="table-wrap">
          <table>
            <caption>{t("aact.guestsCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("people.colPerson")}</th>
                <th scope="col">{t("people.colPhone")}</th>
                <th scope="col">{t("guests.colPayer")}</th>
              </tr>
            </thead>
            <tbody>
              {(detail.guests ?? []).map((guest) => (
                <tr key={guest.guest_id}>
                  <th scope="row">
                    <Link to={adminGuestPath(guest.guest_id)}>
                      {guest.first_name} {guest.last_name}
                    </Link>{" "}
                    <small>({t("guests.badge")})</small>
                  </th>
                  <td>{guest.phone ?? "-"}</td>
                  <td>
                    {guest.payer === "paying" ? t("guests.payerPaying") : t("guests.payerNon")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {detail.people.length > 0 && (
        <>
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
