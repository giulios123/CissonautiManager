import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { formatDay, hhmm, periodLabel } from "../booking";
import { useT } from "../i18n";
import { adminRegistrationPath } from "../routes";
import { StatusBadge } from "../StatusBadge";
import { CsvButton } from "./CsvButton";
import { PlusOneToggle } from "./PlusOneToggle";

type Person = {
  booking_id: number;
  first_name: string;
  last_name: string;
  status: string;
  derived: boolean;
};
type Waiting = {
  entry_id: number;
  position: number;
  first_name: string;
  last_name: string;
  email: string;
  participant_id?: number;
  plus_one?: boolean;
  invited_by?: string | null;
};
type SlotRow = {
  id: number;
  period: string;
  start_time: string;
  end_time: string;
  capacity: number | null;
  present: number;
  free: number | null;
  people: Person[];
  waitlist?: Waiting[];
};
type DayRow = { date: string; slots: SlotRow[] };

export function AdminSlots() {
  const t = useT();
  const [days, setDays] = useState<DayRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(
    () =>
      api<{ days: DayRow[] }>("/api/admin/views/slots")
        .then((data) => setDays(data.days))
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  async function remove(person: Waiting) {
    setMessage(null);
    try {
      await api(`/api/admin/waitlist/${person.entry_id}`, { method: "DELETE" });
      setMessage({
        ok: true,
        text: t("slots.removed", { name: `${person.first_name} ${person.last_name}` }),
      });
      await load();
    } catch (error) {
      setMessage({
        ok: false,
        text: error instanceof ApiError ? error.message : t("common.retryShortly"),
      });
    }
  }

  return (
    <main className="wide">
      <h1>{t("slots.title")}</h1>
      <p>{t("slots.intro")}</p>
      {failed && <p role="alert">{t("slots.loadError")}</p>}
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`notice ${message.ok ? "ok" : "error"}`}
        >
          {message.text}
        </p>
      )}
      {days === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : days.length === 0 ? (
        <p>{t("slots.noDays")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/slots" />
          </p>
          {days.map((day) => (
            <div className="table-wrap" key={day.date}>
              <table>
                <caption>{formatDay(day.date)}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("slots.colSlot")}</th>
                    <th scope="col">{t("slots.colPresent")}</th>
                    <th scope="col">{t("slots.colFree")}</th>
                    <th scope="col">{t("slots.colPeople")}</th>
                    <th scope="col">{t("slots.colWaitlist")}</th>
                  </tr>
                </thead>
                <tbody>
                  {day.slots.map((slot) => (
                    <tr key={slot.id}>
                      <th scope="row">
                        {periodLabel(slot.period)}
                        <br />
                        <small>
                          {hhmm(slot.start_time)}-{hhmm(slot.end_time)}
                        </small>
                      </th>
                      <td>
                        {slot.present}
                        {slot.capacity !== null && ` / ${slot.capacity}`}
                      </td>
                      <td>{slot.free === null ? t("slots.unlimited") : slot.free}</td>
                      <td>
                        {slot.people.length === 0 ? (
                          "-"
                        ) : (
                          <ul className="plain">
                            {slot.people.map((person) => (
                              <li key={person.booking_id}>
                                <Link to={adminRegistrationPath(person.booking_id)}>
                                  {person.first_name} {person.last_name}
                                </Link>{" "}
                                <small>
                                  <StatusBadge status={person.status} />
                                  {person.derived && t("slots.derived")}
                                </small>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                      <td>
                        {(slot.waitlist ?? []).length === 0 ? (
                          "-"
                        ) : (
                          <ol className="plain">
                            {(slot.waitlist ?? []).map((person) => (
                              <li key={person.entry_id} className="item">
                                <span>
                                  {person.position}. {person.first_name} {person.last_name}
                                  {person.plus_one && (
                                    <>
                                      {" "}
                                      <span className="tag">+1</span>
                                    </>
                                  )}
                                  {person.invited_by && (
                                    <>
                                      <br />
                                      <small>
                                        {t("slots.invitedBy", { name: person.invited_by })}
                                        {!person.plus_one && t("slots.toVerify")}
                                      </small>
                                    </>
                                  )}
                                </span>
                                {person.participant_id !== undefined &&
                                  (person.invited_by || person.plus_one) && (
                                    <span className="item-actions">
                                      <PlusOneToggle
                                        compact
                                        participantId={person.participant_id}
                                        invitedBy={person.invited_by ?? null}
                                        verified={Boolean(person.plus_one)}
                                        onChanged={() => void load()}
                                      />
                                    </span>
                                  )}
                                <button
                                  type="button"
                                  className="secondary"
                                  onClick={() => remove(person)}
                                  aria-label={t("slots.removeAria", {
                                    name: `${person.first_name} ${person.last_name}`,
                                  })}
                                >
                                  {t("slots.remove")}
                                </button>
                              </li>
                            ))}
                          </ol>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </>
      )}
    </main>
  );
}
