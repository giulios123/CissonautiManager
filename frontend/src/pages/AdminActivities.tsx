import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT } from "../i18n";
import { adminActivityPath } from "../routes";
import { CsvButton } from "./CsvButton";
import { CollectionDetails } from "../collection";
import { ActivityForm, useActivityFormSetup } from "./ActivityForm";

type Notice = { ok: boolean; text: string } | null;
function DeleteActivity({ activity, onDone }: { activity: Activity; onDone: (n: Notice) => void }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  async function confirm() {
    try {
      await api(`/api/admin/activities/${activity.id}`, { method: "DELETE" });
      setOpen(false);
      onDone({ ok: true, text: t("aact.deleted", { title: activity.title }) });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    }
  }

  return (
    <>
      <button
        type="button"
        className="danger"
        ref={trigger}
        disabled={activity.joined > 0}
        title={activity.joined > 0 ? t("aact.hasPeople") : undefined}
        onClick={() => setOpen(true)}
      >
        {t("aact.delete")}
      </button>
      {open && (
        <ConfirmDialog
          title={t("aact.deleteTitle", { title: activity.title })}
          confirmLabel={t("aact.deleteConfirm")}
          error={error}
          onConfirm={confirm}
          onCancel={() => setOpen(false)}
          returnFocusTo={trigger}
        >
          <p>{t("aact.deleteBody")}</p>
        </ConfirmDialog>
      )}
    </>
  );
}

export function AdminActivities() {
  const t = useT();
  const [activities, setActivities] = useState<Activity[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [editing, setEditing] = useState<Activity | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const { days, hours } = useActivityFormSetup();

  const load = useCallback(
    () =>
      api<Activity[]>("/api/admin/activities")
        .then(setActivities)
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  async function saved(text: string) {
    setEditing(null);
    setNotice({ ok: true, text });
    await load();
  }

  return (
    <main className="wide">
      <h1>{t("aact.title")}</h1>
      <p>{t("aact.intro")}</p>
      {failed && <p role="alert">{t("aact.loadError")}</p>}
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
      {activities === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : activities.length === 0 ? (
        <p>{t("aact.none")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/activities" />
          </p>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">{t("aact.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("aact.colActivity")}</th>
                  <th scope="col">{t("aact.colWhen")}</th>
                  <th scope="col">{t("aact.colPrice")}</th>
                  <th scope="col">{t("aact.colSignedUp")}</th>
                  <th scope="col">{t("aact.colActions")}</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((activity) => (
                  <tr key={activity.id}>
                    <th scope="row">
                      <Link to={adminActivityPath(activity.id)}>{activity.title}</Link>
                      {activity.translation_missing && (
                        <small className="legal">{t("aact.translationMissing")}</small>
                      )}
                    </th>
                    <td>
                      {formatDay(activity.date)}, {periodLabel(activity.period).toLowerCase()}
                      {activity.time_label && ` (${activity.time_label})`}
                    </td>
                    <td>
                      {priceLabel(activity.price_cents)}
                      <CollectionDetails terms={activity} />
                    </td>
                    <td>{seatsLabel(activity)}</td>
                    <td>
                      <div className="actions">
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => setEditing(activity)}
                        >
                          {t("contrib.edit")}
                        </button>
                        <DeleteActivity
                          activity={activity}
                          onDone={async (n) => {
                            setNotice(n);
                            await load();
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {days.length === 0 ? (
        <p>{t("aact.setDatesFirst")}</p>
      ) : (
        <ActivityForm
          key={editing?.id ?? "new"}
          hours={hours}
          days={days}
          initial={editing}
          onSaved={saved}
          onCancel={editing ? () => setEditing(null) : undefined}
        />
      )}
    </main>
  );
}
