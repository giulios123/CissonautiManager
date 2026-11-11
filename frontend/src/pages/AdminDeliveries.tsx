import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { useI18n } from "../i18n";
import { adminRegistrationPath } from "../routes";
import { CsvButton } from "./CsvButton";

type Benefit = { id: number; name: string; retired: boolean; delivered: number; entitled: number };
type Annulled = {
  id: number;
  delivered_at: string;
  annulled_at: string;
  annulled_by: string;
  reason: string;
};
type Row = {
  participant_id: number;
  first_name: string;
  last_name: string;
  booking_id: number | null;
  category: "ordinary" | "internal_non_paying" | null;
  entitled: boolean;
  state: "to_deliver" | "delivered" | "delivered_without_entitlement";
  delivery: { id: number; delivered_at: string; delivered_by: string } | null;
  annulled: Annulled[];
};
type Filter = "all" | "pending" | "delivered";
type Notice = { ok: boolean; text: string } | null;

export function AdminDeliveries() {
  const { t, locale } = useI18n();
  const [benefits, setBenefits] = useState<Benefit[] | null>(null);
  const [benefitId, setBenefitId] = useState<number | null>(null);
  const [rows, setRows] = useState<Row[] | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [failed, setFailed] = useState(false);
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const [annulling, setAnnulling] = useState<Row | null>(null);
  const [reason, setReason] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const clickedRef = useRef<HTMLButtonElement | null>(null);
  // Read synchronously: a second click can arrive before the page has re-rendered.
  const busy = useRef(false);
  const benefit = benefits?.find((item) => item.id === benefitId) ?? null;

  const when = (value: string) =>
    new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "it-IT", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Europe/Rome",
    }).format(new Date(value));

  const loadBenefits = useCallback(
    () =>
      api<Benefit[]>("/api/admin/deliveries/benefits")
        .then((loaded) => {
          setBenefits(loaded);
          setBenefitId((current) =>
            loaded.some((item) => item.id === current) ? current : (loaded[0]?.id ?? null),
          );
        })
        .catch(() => setFailed(true)),
    [],
  );

  const loadRows = useCallback(() => {
    if (benefitId === null) return Promise.resolve();
    const params = new URLSearchParams({ benefit_id: String(benefitId), state: filter });
    if (query.trim()) params.set("q", query.trim());
    return api<Row[]>(`/api/admin/deliveries?${params}`)
      .then((loaded) => {
        setRows(loaded);
        setFailed(false);
      })
      .catch(() => setFailed(true));
  }, [benefitId, filter, query]);

  useEffect(() => {
    void loadBenefits();
  }, [loadBenefits]);
  useEffect(() => {
    void loadRows();
  }, [loadRows]);

  async function change(run: () => Promise<unknown>, done: string) {
    if (busy.current) return false;
    busy.current = true;
    setWorking(true);
    setProblem(null);
    try {
      await run();
      setNotice({ ok: true, text: done });
      await Promise.all([loadBenefits(), loadRows()]);
      return true;
    } catch (caught) {
      const text = caught instanceof ApiError ? caught.message : t("deliveries.actionError");
      setProblem(text);
      setNotice({ ok: false, text });
      return false;
    } finally {
      busy.current = false;
      setWorking(false);
    }
  }

  const deliver = (row: Row) =>
    change(
      () =>
        api("/api/admin/deliveries", {
          method: "POST",
          json: {
            participant_id: row.participant_id,
            benefit_id: benefitId,
            request_key: crypto.randomUUID(),
          },
        }),
      t("deliveries.delivered"),
    );

  async function annul(row: Row) {
    if (!row.delivery) return;
    const ok = await change(
      () =>
        api(`/api/admin/deliveries/${row.delivery!.id}/annul`, {
          method: "POST",
          json: { reason: reason.trim() },
        }),
      t("deliveries.annulled"),
    );
    if (ok) {
      setAnnulling(null);
      setReason("");
    }
  }

  const name = (row: Row) => `${row.first_name} ${row.last_name}`;
  const category = (row: Row) =>
    row.category === "internal_non_paying"
      ? t("exempt.categoryInternal")
      : row.category === "ordinary"
        ? t("exempt.categoryOrdinary")
        : "";

  return (
    <main className="wide">
      <h1>{t("deliveries.title")}</h1>
      <p>{t("deliveries.intro")}</p>
      {failed && <p role="alert">{t("deliveries.loadError")}</p>}
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
      {benefits === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : benefits.length === 0 ? (
        <p>{t("deliveries.noCatalogue")}</p>
      ) : (
        <>
          <label>
            {t("deliveries.benefit")}
            <select
              value={benefitId ?? ""}
              onChange={(event) => {
                setRows(null);
                setBenefitId(Number(event.target.value));
              }}
            >
              {benefits.map((item) => (
                <option key={item.id} value={item.id}>
                  {t("deliveries.benefitOption", {
                    name: item.name,
                    delivered: item.delivered,
                    entitled: item.entitled,
                  })}
                </option>
              ))}
            </select>
          </label>
          <div className="row">
            <label>
              {t("deliveries.search")}
              <input
                type="search"
                value={query}
                maxLength={100}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <label>
              {t("deliveries.filter")}
              <select value={filter} onChange={(event) => setFilter(event.target.value as Filter)}>
                <option value="all">{t("deliveries.filterAll")}</option>
                <option value="pending">{t("deliveries.filterPending")}</option>
                <option value="delivered">{t("deliveries.filterDelivered")}</option>
              </select>
            </label>
          </div>
          {rows === null ? (
            <p aria-busy="true">{t("common.loading")}</p>
          ) : rows.length === 0 ? (
            <p>{t("deliveries.none")}</p>
          ) : (
            <>
              <p>
                <CsvButton
                  path="/api/admin/deliveries"
                  params={new URLSearchParams({ benefit_id: String(benefitId), state: filter })}
                />
              </p>
              <div className="table-wrap">
                <table>
                  <caption className="sr-only">{t("deliveries.caption")}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t("deliveries.colPerson")}</th>
                      <th scope="col">{t("deliveries.colCategory")}</th>
                      <th scope="col">{t("deliveries.colState")}</th>
                      <th scope="col">{t("deliveries.colActions")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.participant_id}>
                        <th scope="row">
                          {row.booking_id ? (
                            <Link to={adminRegistrationPath(row.booking_id)}>{name(row)}</Link>
                          ) : (
                            name(row)
                          )}
                        </th>
                        <td>{category(row)}</td>
                        <td>
                          {row.delivery ? (
                            <>
                              <strong>
                                {t("deliveries.stateDelivered", {
                                  when: when(row.delivery.delivered_at),
                                  by: row.delivery.delivered_by,
                                })}
                              </strong>
                              {row.state === "delivered_without_entitlement" && (
                                <p className="legal">
                                  <strong>{t("deliveries.stateNoEntitlement")}</strong>
                                  {" · "}
                                  {t("deliveries.noEntitlementNote")}
                                </p>
                              )}
                            </>
                          ) : (
                            <strong>{t("deliveries.stateToDeliver")}</strong>
                          )}
                          {row.annulled.map((entry) => (
                            <small key={entry.id} className="legal">
                              <br />
                              {t("deliveries.annulledEntry", {
                                when: when(entry.annulled_at),
                                by: entry.annulled_by,
                                reason: entry.reason,
                              })}
                            </small>
                          ))}
                        </td>
                        <td>
                          {row.delivery ? (
                            <button
                              type="button"
                              className="secondary"
                              disabled={working}
                              aria-label={t("deliveries.annulLabel", {
                                benefit: benefit?.name ?? "",
                                name: name(row),
                              })}
                              onClick={(event) => {
                                clickedRef.current = event.currentTarget;
                                setProblem(null);
                                setReason("");
                                setAnnulling(row);
                              }}
                            >
                              {t("deliveries.annul")}
                            </button>
                          ) : (
                            <button
                              type="button"
                              disabled={working || !row.entitled || benefit?.retired}
                              aria-label={t("deliveries.deliverLabel", {
                                benefit: benefit?.name ?? "",
                                name: name(row),
                              })}
                              onClick={() => void deliver(row)}
                            >
                              {t("deliveries.deliver")}
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
        </>
      )}
      {annulling && (
        <ConfirmDialog
          title={t("deliveries.annulTitle", {
            benefit: benefit?.name ?? "",
            name: name(annulling),
          })}
          confirmLabel={t("deliveries.annulConfirm")}
          confirmDisabled={!reason.trim()}
          working={working}
          cancelDisabled={working}
          error={problem}
          onConfirm={() => void annul(annulling)}
          onCancel={() => {
            setAnnulling(null);
            setReason("");
          }}
          returnFocusTo={clickedRef}
        >
          <p>{t("deliveries.annulText")}</p>
          <label>
            {t("deliveries.annulReason")}
            <input
              value={reason}
              maxLength={200}
              required
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
        </ConfirmDialog>
      )}
    </main>
  );
}
