import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { statusLabel } from "../booking";
import { KIND_KEYS, kindLabel } from "./Contributions";
import { useT } from "../i18n";
import { adminRegistrationPath } from "../routes";
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
};

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

  const load = useCallback(() => {
    const query = new URLSearchParams(kind ? { kind } : {});
    api<Row[]>(`/api/admin/views/contributions?${query}`)
      .then(setRows)
      .catch(() => setFailed(true));
  }, [kind]);

  useEffect(load, [load]);

  async function setHidden(row: Row, hidden: boolean) {
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {hiding && (
        <ConfirmDialog
          title={t("contrib.hideTitle", { title: hiding.title })}
          confirmLabel={t("contrib.hideConfirm")}
          working={working}
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
