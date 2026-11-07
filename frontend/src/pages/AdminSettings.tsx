import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useRefreshEventName } from "../eventName";
import { useT } from "../i18n";
import { hasMessage, tNow } from "../i18n/messages";
import { AdminEmailTexts } from "./AdminEmailTexts";
import { AdminRegistrationEmail } from "./AdminRegistrationEmail";
import { centsToInput, formatEuro, parseEuroToCents } from "../money";
import { AdminEditionLogo } from "./AdminEditionLogo";

type Channel = { code: string; label: string; instructions: string; enabled: boolean };
type Legal = {
  id: number;
  kind: string;
  version: number;
  body: string;
  body_it: string | null;
  body_en: string | null;
  is_legacy: boolean;
} | null;
type Edition = {
  id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  morning_start: string;
  morning_end: string;
  afternoon_start: string;
  afternoon_end: string;
  evening_start: string;
  evening_end: string;
  default_capacity: number;
  hold_days: number;
  waitlist_percent?: number;
  base_fee_cents: number;
  per_day_fee_cents: number;
  lunch_price_cents?: number;
  dinner_price_cents?: number;
  slots: unknown[];
  logo_url: string | null;
  payment_channels: Channel[];
  privacy: Legal;
  disclaimer: Legal;
  health?: Legal;
  attendance?: Legal;
  media?: Legal;
};

type Notice = { kind: "ok" | "error"; text: string } | null;

type ConfirmationPolicyRow = {
  booking_id: number;
  name: string;
  email: string;
  status_before: string;
  status_after: string;
  registration_fee_cents: number;
  amount_due_cents: number;
  paid_cents: number;
  balance_before_cents: number;
  balance_after_cents: number;
  confirmation_balance_after_cents: number;
  sends_confirmation: boolean;
};

type ConfirmationPolicyPreview = {
  current_policy: "legacy_total" | "registration_fee";
  proposed_policy: "legacy_total" | "registration_fee";
  ready: boolean;
  already_active: boolean;
  preview_token: string | null;
  eligible_count: number;
  excluded_expired_count: number;
  excluded_closed_count: number;
  waitlist_only_count: number;
  new_confirmation_count: number;
  blockers: { booking_id: number; name: string; reason: string }[];
  rows: ConfirmationPolicyRow[];
};

type ConfirmationPolicyActivation = {
  already_applied: boolean;
  activated_at: string;
  updated_bookings: number;
  new_confirmations: number;
  transferred_notices: number;
};

const hhmm = (value: string) => value.slice(0, 5);

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : tNow("common.somethingWrong");
}

/** Name of a payment channel in the current language; unknown codes keep their stored label. */
function channelName(code: string, label: string): string {
  const key = `channel.${code}`;
  return hasMessage(key) ? tNow(key) : label;
}

function NoticeLine({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.kind === "error" ? "alert" : "status"} className={`notice ${notice.kind}`}>
      {notice.text}
    </p>
  );
}

function confirmationStatus(status: string, t: ReturnType<typeof useT>): string {
  const key = `status.${status}`;
  return hasMessage(key) ? t(key) : status;
}

function policyBalance(cents: number, t: ReturnType<typeof useT>): string {
  return cents < 0
    ? t("set.policyCredit", { amount: formatEuro(Math.abs(cents)) })
    : formatEuro(cents);
}

function ConfirmationPolicySection() {
  const t = useT();
  const [preview, setPreview] = useState<ConfirmationPolicyPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const actionInFlight = useRef(false);

  async function loadPreview() {
    if (actionInFlight.current) return;
    actionInFlight.current = true;
    setBusy(true);
    setNotice(null);
    setPreview(null);
    try {
      const next = await api<ConfirmationPolicyPreview>(
        "/api/admin/edition/confirmation-policy/preview",
        { cache: "no-store" },
      );
      setPreview(next);
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    } finally {
      actionInFlight.current = false;
      setBusy(false);
    }
  }

  async function activate() {
    if (actionInFlight.current || !preview?.ready || !preview.preview_token) return;
    actionInFlight.current = true;
    setBusy(true);
    setNotice(null);
    try {
      const result = await api<ConfirmationPolicyActivation>(
        "/api/admin/edition/confirmation-policy/activate",
        { method: "POST", json: { preview_token: preview.preview_token } },
      );
      setPreview((current) =>
        current
          ? {
              ...current,
              current_policy: "registration_fee",
              proposed_policy: "registration_fee",
              already_active: true,
              ready: false,
              preview_token: null,
            }
          : current,
      );
      setNotice({
        kind: "ok",
        text: t("set.policyActivated", {
          bookings: result.updated_bookings,
          confirmations: result.new_confirmations,
          emails: result.transferred_notices,
        }),
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) setPreview(null);
      setNotice({ kind: "error", text: errorText(error) });
    } finally {
      actionInFlight.current = false;
      setBusy(false);
    }
  }

  function cancelPreview() {
    if (busy) return;
    setPreview(null);
    setNotice(null);
  }

  return (
    <section aria-labelledby="confirmation-policy-title">
      <h2 id="confirmation-policy-title">{t("set.policyTitle")}</h2>
      <p>{t("set.policyIntro")}</p>
      <p>
        {t("set.policyCurrent")}{" "}
        <strong>
          {preview
            ? t(
                preview.current_policy === "registration_fee"
                  ? "set.policyActive"
                  : "set.policyLegacy",
              )
            : t("set.policyUnknown")}
        </strong>
      </p>
      {preview?.already_active ? (
        <p role="status">{t("set.policyAlreadyActive")}</p>
      ) : (
        <>
          {!preview && (
            <button type="button" onClick={loadPreview} disabled={busy}>
              {busy ? t("common.loading") : t("set.policyPreview")}
            </button>
          )}
          {preview && (
            <>
              <h3>{t("set.policyPreviewTitle")}</h3>
              <p>{t("set.policyPreviewRule")}</p>
              <ul>
                <li>{t("set.policyEligible", { n: preview.eligible_count })}</li>
                <li>{t("set.policyExcludedExpired", { n: preview.excluded_expired_count })}</li>
                <li>{t("set.policyExcludedClosed", { n: preview.excluded_closed_count })}</li>
                <li>{t("set.policyWaitlistOnly", { n: preview.waitlist_only_count })}</li>
                <li>{t("set.policyEmails", { n: preview.new_confirmation_count })}</li>
              </ul>
              {preview.blockers.length > 0 && (
                <div className="notice error" role="alert">
                  <p>{t("set.policyBlockers")}</p>
                  <ul>
                    {preview.blockers.map((blocker) => (
                      <li key={blocker.booking_id}>
                        {blocker.name}:{" "}
                        {t(
                          blocker.reason === "invalid_slots"
                            ? "set.policyInvalidSlots"
                            : "set.policyInvalidAmounts",
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {preview.rows.length > 0 && (
                <div className="table-wrap">
                  <table>
                    <caption>{t("set.policyRowsCaption")}</caption>
                    <thead>
                      <tr>
                        <th scope="col">{t("set.policyPerson")}</th>
                        <th scope="col">{t("set.policyStatusBefore")}</th>
                        <th scope="col">{t("set.policyStatusAfter")}</th>
                        <th scope="col">{t("money.registrationFee")}</th>
                        <th scope="col">{t("money.totalDue")}</th>
                        <th scope="col">{t("people.colPaid")}</th>
                        <th scope="col">{t("set.policyBalanceBefore")}</th>
                        <th scope="col">{t("set.policyBalanceAfter")}</th>
                        <th scope="col">{t("money.confirmationDue")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.map((row) => (
                        <tr key={row.booking_id}>
                          <th scope="row">
                            {row.name}
                            <br />
                            <span className="legal">{row.email}</span>
                          </th>
                          <td>{confirmationStatus(row.status_before, t)}</td>
                          <td>{confirmationStatus(row.status_after, t)}</td>
                          <td>{formatEuro(row.registration_fee_cents)}</td>
                          <td>{formatEuro(row.amount_due_cents)}</td>
                          <td>{formatEuro(row.paid_cents)}</td>
                          <td>{policyBalance(row.balance_before_cents, t)}</td>
                          <td>{policyBalance(row.balance_after_cents, t)}</td>
                          <td>{formatEuro(row.confirmation_balance_after_cents)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="row">
                <button
                  type="button"
                  onClick={activate}
                  disabled={busy || !preview.ready || !preview.preview_token}
                >
                  {busy ? t("common.loading") : t("set.policyApply")}
                </button>
                <button type="button" className="secondary" onClick={cancelPreview} disabled={busy}>
                  {t("set.policyCancelPreview")}
                </button>
              </div>
            </>
          )}
        </>
      )}
      <NoticeLine notice={notice} />
    </section>
  );
}

function EditionSection({
  edition,
  onSaved,
}: {
  edition: Edition | null;
  onSaved: (edition: Edition) => void;
}) {
  const t = useT();
  const [notice, setNotice] = useState<Notice>(null);
  const refreshEventName = useRefreshEventName();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "");
    const base = parseEuroToCents(text("base_fee"));
    const perDay = parseEuroToCents(text("per_day_fee"));
    const lunch = parseEuroToCents(text("lunch_price"));
    const dinner = parseEuroToCents(text("dinner_price"));
    if (base === null || perDay === null || lunch === null || dinner === null) {
      setNotice({ kind: "error", text: t("set.amountsInvalid") });
      return;
    }
    try {
      const saved = await api<Edition>("/api/admin/edition", {
        method: "PUT",
        json: {
          name: text("name"),
          start_date: text("start_date") || null,
          end_date: text("end_date") || null,
          morning_start: text("morning_start"),
          morning_end: text("morning_end"),
          afternoon_start: text("afternoon_start"),
          afternoon_end: text("afternoon_end"),
          evening_start: text("evening_start"),
          evening_end: text("evening_end"),
          default_capacity: Number(text("default_capacity")),
          hold_days: Number(text("hold_days")),
          waitlist_percent: Number(text("waitlist_percent")),
          base_fee_cents: base,
          per_day_fee_cents: perDay,
          lunch_price_cents: lunch,
          dinner_price_cents: dinner,
        },
      });
      onSaved(saved);
      refreshEventName();
      setNotice({ kind: "ok", text: t("set.saved", { n: saved.slots.length }) });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="edition-title" key={edition?.id ?? "new"}>
      <h2 id="edition-title">{t("set.edition")}</h2>
      <label>
        {t("set.name")}
        <input name="name" required defaultValue={edition?.name ?? ""} />
      </label>
      <div className="row">
        <label>
          {t("set.firstDay")}
          <input type="date" name="start_date" defaultValue={edition?.start_date ?? ""} />
        </label>
        <label>
          {t("set.lastDay")}
          <input type="date" name="end_date" defaultValue={edition?.end_date ?? ""} />
        </label>
      </div>
      <fieldset>
        <legend>{t("set.slotTimes")}</legend>
        <div className="row">
          <label>
            {t("set.morningFrom")}
            <input
              type="time"
              name="morning_start"
              required
              defaultValue={hhmm(edition?.morning_start ?? "09:00")}
            />
          </label>
          <label>
            {t("set.to")}
            <input
              type="time"
              name="morning_end"
              required
              defaultValue={hhmm(edition?.morning_end ?? "13:00")}
            />
          </label>
        </div>
        <div className="row">
          <label>
            {t("set.afternoonFrom")}
            <input
              type="time"
              name="afternoon_start"
              required
              defaultValue={hhmm(edition?.afternoon_start ?? "14:00")}
            />
          </label>
          <label>
            {t("set.to")}
            <input
              type="time"
              name="afternoon_end"
              required
              defaultValue={hhmm(edition?.afternoon_end ?? "18:00")}
            />
          </label>
        </div>
        <div className="row">
          <label>
            {t("set.eveningFrom")}
            <input
              type="time"
              name="evening_start"
              required
              defaultValue={hhmm(edition?.evening_start ?? "19:00")}
            />
          </label>
          <label>
            {t("set.toMidnight")}
            <input
              type="time"
              name="evening_end"
              required
              defaultValue={hhmm(edition?.evening_end ?? "00:00")}
            />
          </label>
        </div>
      </fieldset>
      <div className="row">
        <label>
          {t("set.capacity")}
          <input
            type="number"
            name="default_capacity"
            min={1}
            required
            defaultValue={edition?.default_capacity ?? 25}
          />
        </label>
        <label>
          {t("set.holdDays")}
          <input
            type="number"
            name="hold_days"
            min={1}
            required
            defaultValue={edition?.hold_days ?? 3}
          />
        </label>
        <label>
          {t("set.waitlistPercent")}
          <input
            type="number"
            name="waitlist_percent"
            min={0}
            max={100}
            required
            defaultValue={edition?.waitlist_percent ?? 20}
          />
        </label>
      </div>
      <div className="row">
        <label>
          {t("set.baseFee")}
          <input
            name="base_fee"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.base_fee_cents ?? 1000)}
          />
        </label>
        <label>
          {t("set.perDayFee")}
          <input
            name="per_day_fee"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.per_day_fee_cents ?? 100)}
          />
        </label>
      </div>
      <div className="row">
        <label>
          {t("set.lunchPrice")}
          <input
            name="lunch_price"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.lunch_price_cents ?? 800)}
          />
        </label>
        <label>
          {t("set.dinnerPrice")}
          <input
            name="dinner_price"
            inputMode="decimal"
            required
            defaultValue={centsToInput(edition?.dinner_price_cents ?? 1200)}
          />
        </label>
      </div>
      <button type="submit">{t("set.saveEdition")}</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

function ChannelsSection({ edition }: { edition: Edition }) {
  const t = useT();
  const [channels, setChannels] = useState(edition.payment_channels);
  const [notice, setNotice] = useState<Notice>(null);

  const update = (code: string, patch: Partial<Channel>) =>
    setChannels((current) => current.map((c) => (c.code === code ? { ...c, ...patch } : c)));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const saved = await api<Channel[]>("/api/admin/payment-channels", {
        method: "PUT",
        json: channels.map(({ code, instructions, enabled }) => ({ code, instructions, enabled })),
      });
      setChannels(saved);
      setNotice({ kind: "ok", text: t("set.channelsSaved") });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby="channels-title">
      <h2 id="channels-title">{t("set.channelsTitle")}</h2>
      {channels.map((channel) => (
        <fieldset key={channel.code}>
          <legend>{channelName(channel.code, channel.label)}</legend>
          <label className="check">
            <input
              type="checkbox"
              checked={channel.enabled}
              onChange={(e) => update(channel.code, { enabled: e.target.checked })}
            />
            {t("set.active")}
          </label>
          <label>
            {t("set.instructionsFor", { name: channelName(channel.code, channel.label) })}
            <textarea
              rows={3}
              value={channel.instructions}
              onChange={(e) => update(channel.code, { instructions: e.target.value })}
            />
          </label>
        </fieldset>
      ))}
      <button type="submit">{t("set.saveChannels")}</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

function LegalSection({
  kind,
  title,
  current,
}: {
  kind: "privacy" | "disclaimer" | "health" | "attendance" | "media";
  title: string;
  current: Legal;
}) {
  const t = useT();
  const [bodyIt, setBodyIt] = useState(current?.body_it ?? "");
  const [bodyEn, setBodyEn] = useState(current?.body_en ?? "");
  const [version, setVersion] = useState(current?.version ?? 0);
  const [legacy, setLegacy] = useState(current?.is_legacy ?? false);
  const [notice, setNotice] = useState<Notice>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const saved = await api<{ version: number }>("/api/admin/legal-documents", {
        method: "POST",
        json: { kind, body_it: bodyIt.trim(), body_en: bodyEn.trim() },
      });
      setVersion(saved.version);
      setLegacy(false);
      setNotice({ kind: "ok", text: t("set.published", { n: saved.version }) });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    }
  }

  return (
    <form onSubmit={submit} aria-labelledby={`${kind}-title`}>
      <h3 id={`${kind}-title`}>{title}</h3>
      <p>{version ? t("set.currentVersion", { n: version }) : t("set.noText")}</p>
      {legacy && current && (
        <div className="notice">
          <p>{t("set.legacyOriginal")}</p>
          <blockquote>{current.body}</blockquote>
        </div>
      )}
      <label>
        {t("set.textIt")}
        <textarea rows={8} value={bodyIt} onChange={(e) => setBodyIt(e.target.value)} required />
      </label>
      <label>
        {t("set.textEn")}
        <textarea rows={8} value={bodyEn} onChange={(e) => setBodyEn(e.target.value)} required />
      </label>
      <button type="submit">{t("set.publish")}</button>
      <NoticeLine notice={notice} />
    </form>
  );
}

export function AdminSettings() {
  const t = useT();
  const [edition, setEdition] = useState<Edition | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    api<Edition>("/api/admin/edition")
      .then((loaded) => {
        setEdition(loaded);
        setState("ready");
      })
      .catch((error) =>
        setState(error instanceof ApiError && error.status === 404 ? "ready" : "error"),
      );
  }, []);

  if (state === "loading") return <main aria-busy="true">{t("common.loading")}</main>;
  if (state === "error") return <main role="alert">{t("set.loadError")}</main>;

  return (
    <main>
      <h1>{t("set.title")}</h1>
      <EditionSection edition={edition} onSaved={setEdition} />
      {edition ? (
        <>
          <ConfirmationPolicySection />
          <AdminEditionLogo
            logoUrl={edition.logo_url}
            onSaved={(logoUrl) =>
              setEdition((current) => (current ? { ...current, logo_url: logoUrl } : current))
            }
          />
          <ChannelsSection edition={edition} />
          <AdminRegistrationEmail />
          <AdminEmailTexts />
          <section aria-labelledby="legal-title">
            <h2 id="legal-title">{t("set.legalTitle")}</h2>
            <p>{t("set.legalIntro")}</p>
            <LegalSection kind="privacy" title={t("set.privacyTitle")} current={edition.privacy} />
            <LegalSection
              kind="disclaimer"
              title={t("set.disclaimerTitle")}
              current={edition.disclaimer}
            />
            <LegalSection
              kind="health"
              title={t("set.healthTitle")}
              current={edition.health ?? null}
            />
            <LegalSection
              kind="attendance"
              title={t("set.attendanceTitle")}
              current={edition.attendance ?? null}
            />
            <LegalSection
              kind="media"
              title={t("set.mediaTitle")}
              current={edition.media ?? null}
            />
          </section>
        </>
      ) : (
        <p>{t("set.saveEditionFirst")}</p>
      )}
    </main>
  );
}
