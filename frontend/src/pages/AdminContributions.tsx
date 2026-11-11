import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { statusLabel } from "../booking";
import { KIND_KEYS, kindLabel } from "./Contributions";
import { useI18n, useT } from "../i18n";
import { InfoDialog } from "../InfoDialog";
import { adminActivityPath, adminRegistrationPath } from "../routes";
import { formatDay, periodLabel } from "../booking";
import { ActivityForm, useActivityFormSetup } from "./ActivityForm";
import { CsvButton } from "./CsvButton";

type Row = {
  id: number;
  kind: "talk" | "topic" | "skill" | "wanted_skill";
  title: string;
  description: string | null;
  booking_id: number;
  first_name: string;
  last_name: string;
  status: string;
  active: boolean;
  hidden: boolean;
  activities: { id: number; title: string; date: string; period: string }[];
};

/** The activity form for one proposal: starts from its text, in the language in use. */
function CreateActivityDialog({
  row,
  onSaved,
  onClose,
  returnFocusTo,
}: {
  row: Row;
  onSaved: () => Promise<void>;
  onClose: () => void;
  returnFocusTo: React.RefObject<HTMLElement | null>;
}) {
  const t = useT();
  const { locale } = useI18n();
  const { days, hours } = useActivityFormSetup();
  const text = { title: row.title, description: row.description ?? "" };
  return (
    <InfoDialog
      title={t("contrib.createActivityTitle", { title: row.title })}
      onClose={onClose}
      returnFocusTo={returnFocusTo}
    >
      {days.length === 0 ? (
        <p>{t("aact.setDatesFirst")}</p>
      ) : (
        <ActivityForm
          hideHeading
          days={days}
          hours={hours}
          initial={null}
          source={{ contributionId: row.id, title: row.title }}
          prefill={
            locale === "it"
              ? { title_it: text.title, description_it: text.description }
              : { title_en: text.title, description_en: text.description }
          }
          onSaved={async () => {
            await onSaved();
          }}
          onCancel={onClose}
        />
      )}
    </InfoDialog>
  );
}

export function AdminContributions() {
  const t = useT();
  const [kind, setKind] = useState("");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);
  const params = new URLSearchParams(kind ? { kind } : {});
  const [hiding, setHiding] = useState<Row | null>(null);
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const clickedRef = useRef<HTMLButtonElement | null>(null);
  const [converting, setConverting] = useState<Row | null>(null);
  const [created, setCreated] = useState(false);

  const load = useCallback(() => {
    const query = new URLSearchParams(kind ? { kind } : {});
    api<Row[]>(`/api/admin/views/contributions?${query}`)
      .then(setRows)
      .catch(() => setFailed(true));
  }, [kind]);

  useEffect(load, [load]);

  async function setHidden(row: Row, hidden: boolean) {
    if (working) return;
    setWorking(true);
    setProblem(null);
    try {
      await api(`/api/admin/contributions/${row.id}/${hidden ? "hide" : "unhide"}`, {
        method: "POST",
        json: hidden ? { reason: reason.trim() || null } : undefined,
      });
      setHiding(null);
      setReason("");
      load();
    } catch (caught) {
      setProblem(caught instanceof ApiError ? caught.message : t("contrib.hideError"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <main className="wide">
      <h1>{t("contrib.adminTitle")}</h1>
      <p>{t("contrib.adminIntro")}</p>
      <label>
        {t("contrib.type")}
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="">{t("adm.all")}</option>
          {Object.keys(KIND_KEYS).map((value) => (
            <option key={value} value={value}>
              {kindLabel(value as keyof typeof KIND_KEYS)}
            </option>
          ))}
        </select>
      </label>
      {failed && <p role="alert">{t("contrib.loadError")}</p>}
      {rows === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : rows.length === 0 ? (
        <p>{t("contrib.none")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/contributions" params={params} />
          </p>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">{t("contrib.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("contrib.colContribution")}</th>
                  <th scope="col">{t("contrib.type")}</th>
                  <th scope="col">{t("contrib.colWho")}</th>
                  <th scope="col">{t("contrib.colVisibility")}</th>
                  <th scope="col">{t("contrib.colActivities")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <th scope="row">
                      {row.title}
                      {row.description && (
                        <>
                          <br />
                          <small>{row.description}</small>
                        </>
                      )}
                    </th>
                    <td>{kindLabel(row.kind)}</td>
                    <td>
                      <Link to={adminRegistrationPath(row.booking_id)}>
                        {row.first_name} {row.last_name}
                      </Link>
                      {!row.active && (
                        <>
                          <br />
                          <small>
                            {t("contrib.registrationStatus", {
                              status: statusLabel(row.status).toLowerCase(),
                            })}
                          </small>
                        </>
                      )}
                    </td>
                    <td>
                      {row.hidden ? (
                        <strong>{t("contrib.hiddenBadge")}</strong>
                      ) : (
                        t("contrib.visible")
                      )}{" "}
                      {row.hidden ? (
                        <button
                          type="button"
                          className="secondary"
                          disabled={working}
                          onClick={() => setHidden(row, false)}
                        >
                          {t("contrib.show")}
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary"
                          disabled={working}
                          onClick={(event) => {
                            clickedRef.current = event.currentTarget;
                            setProblem(null);
                            setHiding(row);
                          }}
                        >
                          {t("contrib.hide")}
                        </button>
                      )}
                    </td>
                    <td>
                      {row.activities.length > 0 && (
                        <>
                          <strong>{t("contrib.activitiesCreated")}</strong>
                          <ul>
                            {row.activities.map((activity) => (
                              <li key={activity.id}>
                                <Link to={adminActivityPath(activity.id)}>{activity.title}</Link>{" "}
                                <small>
                                  {formatDay(activity.date)},{" "}
                                  {periodLabel(activity.period).toLowerCase()}
                                </small>
                              </li>
                            ))}
                          </ul>
                        </>
                      )}
                      <button
                        type="button"
                        className="secondary"
                        aria-label={t("contrib.createActivityFor", { title: row.title })}
                        onClick={(event) => {
                          clickedRef.current = event.currentTarget;
                          setCreated(false);
                          setConverting(row);
                        }}
                      >
                        {t("contrib.createActivity")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {created && (
        <p role="status" className="notice ok">
          {t("aact.created")}
        </p>
      )}
      {converting && (
        <CreateActivityDialog
          row={converting}
          returnFocusTo={clickedRef}
          onClose={() => setConverting(null)}
          onSaved={async () => {
            setConverting(null);
            setCreated(true);
            load();
          }}
        />
      )}
      {hiding && (
        <ConfirmDialog
          title={t("contrib.hideTitle", { title: hiding.title })}
          confirmLabel={t("contrib.hideConfirm")}
          working={working}
          cancelDisabled={working}
          error={problem}
          onConfirm={() => setHidden(hiding, true)}
          onCancel={() => {
            setHiding(null);
            setReason("");
          }}
          returnFocusTo={clickedRef}
        >
          <p>{t("contrib.hideText")}</p>
          <label>
            {t("contrib.hideReason")}
            <input
              value={reason}
              maxLength={200}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
        </ConfirmDialog>
      )}
      {!hiding && problem && (
        <p role="alert" className="notice error">
          {problem}
        </p>
      )}
    </main>
  );
}
