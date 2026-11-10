import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
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
};

export function AdminContributions() {
  const t = useT();
  const [kind, setKind] = useState("");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [failed, setFailed] = useState(false);
  const params = new URLSearchParams(kind ? { kind } : {});

  useEffect(() => {
    const query = new URLSearchParams(kind ? { kind } : {});
    api<Row[]>(`/api/admin/views/contributions?${query}`)
      .then(setRows)
      .catch(() => setFailed(true));
  }, [kind]);

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
