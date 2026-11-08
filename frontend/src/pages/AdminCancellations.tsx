import { useEffect, useState } from "react";
import { api } from "../api";
import { formatDeadline } from "../booking";
import { useT } from "../i18n";

type Entry = {
  id: number;
  participant_id: number;
  first_name: string;
  last_name: string;
  email: string;
  edition_name: string;
  at: string;
  actor: string | null;
  outcome: "removed" | "requested";
};

type Page = { items: Entry[]; total: number };

export function AdminCancellations() {
  const t = useT();
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<Page | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ q: query, offset: String(offset), limit: "50" });
    api<Page>(`/api/admin/registrations/cancellations?${params}`)
      .then((result) => {
        if (!cancelled) {
          setPage(result);
          setFailed(false);
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [query, offset]);

  return (
    <main className="wide">
      <h1>{t("cancellations.title")}</h1>
      <label>
        {t("cancellations.search")}
        <input
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setOffset(0);
          }}
        />
      </label>
      {failed && <p role="alert">{t("cancellations.error")}</p>}
      {!failed && page === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : page?.items.length === 0 ? (
        <p>{t("cancellations.empty")}</p>
      ) : page ? (
        <>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">{t("cancellations.title")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("people.colPerson")}</th>
                  <th scope="col">{t("cancellations.edition")}</th>
                  <th scope="col">{t("cancellations.date")}</th>
                  <th scope="col">{t("cancellations.actor")}</th>
                  <th scope="col">{t("cancellations.outcome")}</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((entry) => (
                  <tr key={entry.id}>
                    <th scope="row">
                      {entry.first_name} {entry.last_name}
                      <br />
                      <small>{entry.email}</small>
                    </th>
                    <td>{entry.edition_name}</td>
                    <td>{formatDeadline(entry.at)}</td>
                    <td>{entry.actor ?? t("cancellations.participant")}</td>
                    <td>
                      {t(
                        entry.outcome === "removed"
                          ? "cancellations.removed"
                          : "cancellations.requested",
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav aria-label={t("cancellations.pagination")}>
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 50))}
            >
              {t("cancellations.previous")}
            </button>
            <button
              type="button"
              disabled={offset + page.items.length >= page.total}
              onClick={() => setOffset(offset + 50)}
            >
              {t("cancellations.next")}
            </button>
          </nav>
        </>
      ) : null}
    </main>
  );
}
