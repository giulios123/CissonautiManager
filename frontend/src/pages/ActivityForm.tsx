import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { editionDays, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { centsToInput, parseEuroToCents } from "../money";
import { useT } from "../i18n";
import { CollectionFields } from "../collection";
import { TimeSelect } from "../TimeSelect";

const PERIODS = ["morning", "afternoon", "evening"] as const;
export const DEFAULT_HOURS: Record<string, string> = {
  morning_start: "09:00",
  morning_end: "13:00",
  afternoon_start: "14:00",
  afternoon_end: "18:00",
  evening_start: "19:00",
  evening_end: "00:00",
};

export function ActivityForm({
  days,
  initial,
  onSaved,
  onCancel,
  hours,
  prefill,
  source,
  hideHeading = false,
}: {
  days: string[];
  initial: Activity | null;
  onSaved: (text: string) => Promise<void>;
  onCancel?: () => void;
  hours: Record<string, string>;
  /** A new activity that starts from the text of a proposal (MVP 29). */
  prefill?: Partial<Record<"title_it" | "title_en" | "description_it" | "description_en", string>>;
  source?: { contributionId: number; title: string };
  hideHeading?: boolean;
}) {
  const t = useT();
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  // One key per form: a repeated save (double click, retry) returns the activity already created.
  const [requestKey, setRequestKey] = useState(() => crypto.randomUUID());
  const [mode, setMode] = useState<"organizer" | "provider">(initial?.payment_mode ?? "organizer");
  const [period, setPeriod] = useState(initial?.period ?? "morning");
  const [start, setStart] = useState(initial ? (initial.start_time ?? "") : hours.morning_start);
  const [end, setEnd] = useState(initial ? (initial.end_time ?? "") : hours.morning_end);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const titleIt = text("title_it");
    const titleEn = text("title_en");
    const descriptionIt = text("description_it");
    const descriptionEn = text("description_en");
    const localizedChanged =
      !initial ||
      titleIt !== (initial.title_it ?? "") ||
      titleEn !== (initial.title_en ?? "") ||
      descriptionIt !== (initial.description_it ?? "") ||
      descriptionEn !== (initial.description_en ?? "");
    const price = parseEuroToCents(text("price") || "0");
    if (price === null) {
      setError(t("aact.priceInvalid"));
      return;
    }
    const body = {
      title: initial?.title ?? titleIt,
      description: initial?.description ?? descriptionIt,
      ...(localizedChanged
        ? {
            title_it: titleIt,
            title_en: titleEn,
            description_it: descriptionIt,
            description_en: descriptionEn,
          }
        : {}),
      date: text("date"),
      period: text("period"),
      start_time: start || null,
      end_time: end || null,
      payment_mode: mode,
      payment_instructions: mode === "provider" ? text("payment_instructions") : null,
      price_cents: price,
      capacity: text("capacity") ? Number(text("capacity")) : null,
      ...(initial
        ? {}
        : {
            request_key: requestKey,
            ...(source ? { source_contribution_id: source.contributionId } : {}),
          }),
    };
    setSaving(true);
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
        // The next new activity is a new command: a new key.
        setRequestKey(crypto.randomUUID());
      }
      await onSaved(initial ? t("aact.updated") : t("aact.created"));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setSaving(false);
    }
  }

  const title = initial ? t("aact.editTitle", { title: initial.title }) : t("aact.newTitle");
  return (
    <form onSubmit={submit} aria-label={title} key={initial?.id ?? "new"}>
      {hideHeading ? null : <h2>{title}</h2>}
      {source && <p className="legal">{t("aact.fromProposalHint", { title: source.title })}</p>}
      <label>
        {t("contrib.title")} · IT
        <input
          name="title_it"
          required={!initial || !initial.translation_missing}
          maxLength={200}
          defaultValue={initial?.title_it ?? prefill?.title_it ?? ""}
          placeholder={initial?.title}
        />
      </label>
      <label>
        {t("contrib.title")} · EN
        <input
          name="title_en"
          required={!initial || !initial.translation_missing}
          maxLength={200}
          defaultValue={initial?.title_en ?? prefill?.title_en ?? ""}
          placeholder={initial?.title}
        />
      </label>
      <label>
        {t("aact.description")} · IT
        <textarea
          name="description_it"
          required={!initial || !initial.translation_missing}
          rows={3}
          defaultValue={initial?.description_it ?? prefill?.description_it ?? ""}
          placeholder={initial?.description ?? undefined}
        />
      </label>
      <label>
        {t("aact.description")} · EN
        <textarea
          name="description_en"
          required={!initial || !initial.translation_missing}
          rows={3}
          defaultValue={initial?.description_en ?? prefill?.description_en ?? ""}
          placeholder={initial?.description ?? undefined}
        />
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
      {initial?.translation_missing && (
        <p className="notice" role="status">
          {t("aact.translationMissing")}
        </p>
      )}
      {initial && initial.joined > 0 && <p className="legal">{t("aact.locked")}</p>}
      {initial && initial.joined > 0 && <p className="legal">{t("collection.repriceWarning")}</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button type="submit" disabled={saving}>
          {initial ? t("aact.saveChanges") : t("aact.create")}
        </button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            {t("contrib.cancel")}
          </button>
        )}
      </div>
    </form>
  );
}

/** The days of the edition and the default hours of each part of the day, for a new activity. */
export function useActivityFormSetup() {
  const [days, setDays] = useState<string[]>([]);
  const [hours, setHours] = useState(DEFAULT_HOURS);
  useEffect(() => {
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
  }, []);
  return { days, hours };
}
