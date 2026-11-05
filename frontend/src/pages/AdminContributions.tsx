import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { statusLabel } from "../booking";
import { KIND_LABELS } from "./Contributions";
import { CsvButton } from "./CsvButton";

type Row = {
  id: number;
  kind: "talk" | "topic" | "skill";
  title: string;
  description: string | null;
  booking_id: number;
  first_name: string;
  last_name: string;
  status: string;
  active: boolean;
};

export function AdminContributions() {
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
      <h1>Contributi</h1>
      <p>Talk, temi per l&apos;unconference e competenze proposti dai partecipanti.</p>
      <label>
        Tipo
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="">Tutti</option>
          {Object.entries(KIND_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {failed && <p role="alert">Non riesco a caricare i contributi.</p>}
      {rows === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : rows.length === 0 ? (
        <p>Nessun contributo per ora.</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/views/contributions" params={params} />
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Contributo</th>
                  <th scope="col">Tipo</th>
                  <th scope="col">Chi</th>
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
                    <td>{KIND_LABELS[row.kind]}</td>
                    <td>
                      <Link to={`/admin/iscrizioni/${row.booking_id}`}>
                        {row.first_name} {row.last_name}
                      </Link>
                      {!row.active && (
                        <>
                          <br />
                          <small>iscrizione {statusLabel(row.status).toLowerCase()}</small>
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
