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

type Page = { items: Entry[]; has_more: boolean };
type Cursor = { at: string; id: number };

export function AdminCancellations() {
  const t = useT();
  const [query, setQuery] = useState("");
  const [cursors, setCursors] = useState<(Cursor | null)[]>([null]);
  const [pageIndex, setPageIndex] = useState(0);
  const [page, setPage] = useState<Page | null>(null);
  const [failed, setFailed] = useState(false);
  const cursor = cursors[pageIndex] ?? null;

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ q: query, limit: "50" });
    if (cursor) {
      params.set("before_at", cursor.at);
      params.set("before_id", String(cursor.id));
    }
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
  }, [query, cursor]);

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
            setCursors([null]);
            setPageIndex(0);
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
              disabled={pageIndex === 0}
              onClick={() => setPageIndex((current) => Math.max(0, current - 1))}
            >
              {t("cancellations.previous")}
            </button>
            <button
              type="button"
              disabled={!page.has_more || page.items.length === 0}
              onClick={() => {
                const last = page.items.at(-1);
                if (!last) return;
                setCursors((current) => [
                  ...current.slice(0, pageIndex + 1),
                  { at: last.at, id: last.id },
                ]);
                setPageIndex((current) => current + 1);
              }}
            >
              {t("cancellations.next")}
            </button>
          </nav>
        </>
      ) : null}
    </main>
  );
}
