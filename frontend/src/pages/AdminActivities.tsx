import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { editionDays, priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { centsToInput, parseEuroToCents } from "../money";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT } from "../i18n";
import { adminActivityPath } from "../routes";
import { CsvButton } from "./CsvButton";
import { CollectionDetails, CollectionFields } from "../collection";
import { TimeSelect } from "../TimeSelect";

type Notice = { ok: boolean; text: string } | null;
const PERIODS = ["morning", "afternoon", "evening"] as const;
const DEFAULT_HOURS: Record<string, string> = {
  morning_start: "09:00",
  morning_end: "13:00",
  afternoon_start: "14:00",
  afternoon_end: "18:00",
  evening_start: "19:00",
  evening_end: "00:00",
};

function ActivityForm({
  days,
  initial,
  onSaved,
  onCancel,
  hours,
}: {
  days: string[];
  initial: Activity | null;
  onSaved: (text: string) => Promise<void>;
  onCancel?: () => void;
  hours: Record<string, string>;
}) {
  const t = useT();
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"organizer" | "provider">(initial?.payment_mode ?? "organizer");
  const [period, setPeriod] = useState(initial?.period ?? "morning");
  const [start, setStart] = useState(initial ? (initial.start_time ?? "") : hours.morning_start);
  const [end, setEnd] = useState(initial ? (initial.end_time ?? "") : hours.morning_end);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const price = parseEuroToCents(text("price") || "0");
    if (price === null) {
      setError(t("aact.priceInvalid"));
      return;
    }
    const body = {
      title: text("title"),
      description: text("description") || null,
      date: text("date"),
      period: text("period"),
      start_time: start || null,
      end_time: end || null,
      payment_mode: mode,
      payment_instructions: mode === "provider" ? text("payment_instructions") : null,
      price_cents: price,
      capacity: text("capacity") ? Number(text("capacity")) : null,
    };
    try {
      await api(initial ? `/api/admin/activities/${initial.id}` : "/api/admin/activities", {
        method: initial ? "PATCH" : "POST",
        json: body,
      });
      if (!initial) {
        form.reset();
        setMode("organizer");
        setPeriod("morning");
        setStart(hours.morning_start);
        setEnd(hours.morning_end);
      }
      await onSaved(initial ? t("aact.updated") : t("aact.created"));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    }
  }

  const title = initial ? t("aact.editTitle", { title: initial.title }) : t("aact.newTitle");
  return (
    <form onSubmit={submit} aria-label={title} key={initial?.id ?? "new"}>
      <h2>{title}</h2>
      <label>
        {t("contrib.title")}
        <input name="title" required maxLength={200} defaultValue={initial?.title ?? ""} />
      </label>
      <label>
        {t("contrib.description")}
        <textarea name="description" rows={3} defaultValue={initial?.description ?? ""} />
      </label>
      <div className="row">
        <label>
          {t("aact.day")}
          <select name="date" required defaultValue={initial?.date ?? days[0]}>
            {days.map((day) => (
              <option key={day} value={day}>
                {formatDay(day)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("aact.period")}
          <select
            name="period"
            value={period}
            onChange={(e) => {
              const p = e.target.value as typeof period;
              setPeriod(p);
              setStart(hours[`${p}_start`]);
              setEnd(hours[`${p}_end`]);
            }}
          >
            {PERIODS.map((period) => (
              <option key={period} value={period}>
                {periodLabel(period)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="row">
        <TimeSelect
          label={t("time.start")}
          value={start}
          onChange={setStart}
          required={!initial || !!start || !!end}
        />
        <TimeSelect
          label={t("time.end")}
          value={end}
          onChange={setEnd}
          required={!initial || !!start || !!end}
          end
        />
      </div>
      {initial?.time_label && !initial.start_time && (
        <p>{t("time.previous", { time: initial.time_label })}</p>
      )}
      <div className="row">
        <label>
          {t("aact.price")}
          <input
            name="price"
            inputMode="decimal"
            defaultValue={centsToInput(initial?.price_cents ?? 0)}
          />
        </label>
        <label>
          {t("aact.capacity")}
          <input name="capacity" type="number" min={1} defaultValue={initial?.capacity ?? ""} />
        </label>
      </div>
      <CollectionFields
        mode={mode}
        onChange={setMode}
        instructions={initial?.payment_instructions}
      />
      {initial && initial.joined > 0 && <p className="legal">{t("aact.locked")}</p>}
      {initial && initial.joined > 0 && <p className="legal">{t("collection.repriceWarning")}</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button type="submit">{initial ? t("aact.saveChanges") : t("aact.create")}</button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            {t("contrib.cancel")}
          </button>
        )}
      </div>
    </form>
  );
}

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
  const [days, setDays] = useState<string[]>([]);
  const [failed, setFailed] = useState(false);
  const [editing, setEditing] = useState<Activity | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [hours, setHours] = useState(DEFAULT_HOURS);

  const load = useCallback(
    () =>
      api<Activity[]>("/api/admin/activities")
        .then(setActivities)
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
    api<{ start_date: string | null; end_date: string | null } & Record<string, string | null>>(
      "/api/admin/edition",
    )
      .then((edition) => {
        setDays(editionDays(edition.start_date, edition.end_date));
        setHours(
          Object.fromEntries(
            Object.entries(DEFAULT_HOURS).map(([key, fallback]) => [
              key,
              edition[key]?.slice(0, 5) ?? fallback,
            ]),
          ),
        );
      })
      .catch(() => setDays([]));
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
