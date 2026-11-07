import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import {
  canJoinWaitlist,
  feePreview,
  formatDayShort,
  formatDeadline,
  isFull,
  periodLabel,
  seatsLabel,
  type Day,
} from "../booking";
import type { PickerDay } from "../daySelection";
import { useI18n } from "../i18n";
import { isInFrame } from "../frame";
import { tNow } from "../i18n/messages";
import { EVENT_NAME } from "../eventName";
import { formatEuro } from "../money";
import { PresenceSummary } from "../PresenceSummary";
import { ROUTES } from "../routes";
import { legalTextForLocale, type LegalDocumentText } from "../legalText";
import { DayPicker } from "./DayPicker";

type Channel = { code: string; label: string; instructions: string };
type Legal = LegalDocumentText & { version: number };
type OptionalConsentText = { id: number; version: number; texts: Record<"it" | "en", string> };
type OptionalConsentKind = "attendance" | "media";
type PublicEdition = {
  registration_open: boolean;
  name: string | null;
  registration_intro?: Record<string, string> | null;
  base_fee_cents: number | null;
  per_day_fee_cents: number | null;
  hold_days: number | null;
  days: Day[];
  payment_channels: Channel[];
  privacy: Legal | null;
  disclaimer: Legal | null;
  attendance_consent: OptionalConsentText | null;
  media_consent: OptionalConsentText | null;
};
type Summary = {
  personal_code: string | null;
  amount_due_cents: number;
  hold_expires_at: string;
  slots: { date: string; period: string; label: string }[];
  schedule: { date: string; period: string; start_time: string; end_time: string }[];
  payment_channels: Channel[];
};
type Waitlisted = { label: string; position: number };
type Outcome =
  | { kind: "created"; booking: Summary; waitlist: Waitlisted[]; message?: string }
  | { kind: "waitlisted"; personalCode: string | null; waitlist: Waitlisted[]; message?: string }
  | { kind: "already"; message: string };

/** Label of a full slot: whether its waitlist can still be joined. */
function fullSlotLabel(slot: Day["slots"][number]) {
  if (canJoinWaitlist(slot)) return tNow("reg.fullJoinable");
  if (slot.waitlist_free === 0) return tNow("reg.fullWaitlistFull");
  return seatsLabel(slot);
}

const fetchEdition = () => api<PublicEdition>("/api/public/edition");

export function Registration() {
  const { t, tn, locale } = useI18n();
  const [edition, setEdition] = useState<PublicEdition | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [optionalChoices, setOptionalChoices] = useState<
    Record<OptionalConsentKind, boolean | null>
  >({ attendance: null, media: null });
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const toolbar = toolbarRef.current;
    const header = document.querySelector<HTMLElement>(".site-header");
    if (!toolbar || !header) return;

    const updateOffset = () => {
      const position = window.getComputedStyle(header).position;
      const offset = position === "sticky" || position === "fixed" ? header.offsetHeight : 0;
      toolbar.style.setProperty("--registration-sticky-offset", `${offset}px`);
    };

    updateOffset();
    window.addEventListener("resize", updateOffset);
    const observer =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(updateOffset);
    observer?.observe(header);
    return () => {
      window.removeEventListener("resize", updateOffset);
      observer?.disconnect();
    };
  }, [edition, outcome]);

  useEffect(() => {
    fetchEdition()
      .then(setEdition)
      .catch(() => setLoadError(true));
  }, []);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  if (loadError)
    return (
      <main role="alert">
        <p>{t("reg.loadError")}</p>
        <SignInPrompt />
      </main>
    );
  if (!edition)
    return (
      <main aria-busy="true">
        {t("common.loading")}
        <SignInPrompt />
      </main>
    );

  if (outcome?.kind === "already") {
    return (
      <main>
        <h1>{t("reg.alreadyTitle")}</h1>
        <p role="status">{outcome.message}</p>
        <SignInPrompt />
      </main>
    );
  }
  if (outcome?.kind === "created")
    return (
      <Confirmation
        booking={outcome.booking}
        waitlist={outcome.waitlist}
        message={outcome.message}
      />
    );
  if (outcome?.kind === "waitlisted")
    return (
      <WaitlistConfirmation
        personalCode={outcome.personalCode}
        waitlist={outcome.waitlist}
        message={outcome.message}
      />
    );

  if (!edition.registration_open || !edition.privacy || !edition.disclaimer) {
    return (
      <main>
        <h1>{edition.name ?? EVENT_NAME}</h1>
        <p>{t("reg.notOpen")}</p>
        <SignInPrompt />
      </main>
    );
  }

  const currentEdition = edition;
  const privacy = currentEdition.privacy!;
  const disclaimer = currentEdition.disclaimer!;
  const privacyCopy = legalTextForLocale(privacy, locale);
  const disclaimerCopy = legalTextForLocale(disclaimer, locale);
  const fullIds = new Set(
    edition.days.flatMap((day) => day.slots.filter((slot) => isFull(slot)).map((slot) => slot.id)),
  );
  const toBook = new Set([...selected].filter((id) => !fullIds.has(id)));
  const toWait = [...selected].filter((id) => fullIds.has(id));
  const fee = feePreview(
    edition.days,
    toBook,
    edition.base_fee_cents ?? 0,
    edition.per_day_fee_cents ?? 0,
  );

  const pickerDays: PickerDay[] = edition.days.map((day) => ({
    date: day.date,
    slots: day.slots.map((slot) => {
      const full = isFull(slot);
      return {
        id: slot.id,
        period: slot.period,
        start_time: slot.start_time,
        end_time: slot.end_time,
        full,
        disabled: full && !canJoinWaitlist(slot),
        hint: full ? fullSlotLabel(slot) : seatsLabel(slot),
      };
    }),
  }));
  const bookedSlots = edition.days.flatMap((day) =>
    day.slots
      .filter((slot) => toBook.has(slot.id))
      .map((slot) => ({ date: day.date, period: slot.period })),
  );
  const waitingSlots = edition.days.flatMap((day) =>
    day.slots
      .filter((slot) => toWait.includes(slot.id))
      .map((slot) => ({ date: day.date, period: periodLabel(slot.period) })),
  );
  const schedule = edition.days.flatMap((day) =>
    day.slots.map((slot) => ({
      date: day.date,
      period: slot.period,
      start_time: slot.start_time,
      end_time: slot.end_time,
    })),
  );
  const first = edition.days[0]?.date;
  const last = edition.days[edition.days.length - 1]?.date;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (selected.size === 0) {
      setError(t("reg.chooseSlot"));
      return;
    }
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "");
    const optionalConsents: Partial<
      Record<OptionalConsentKind, { granted: boolean; document_id: number; version: number }>
    > = {};
    for (const kind of ["attendance", "media"] as const) {
      const choice = optionalChoices[kind];
      const document = currentEdition[`${kind}_consent`];
      if (choice !== null && document) {
        optionalConsents[kind] = {
          granted: choice,
          document_id: document.id,
          version: document.version,
        };
      }
    }
    setSending(true);
    try {
      const result = await api<{
        result: string;
        message?: string;
        booking?: Summary;
        personal_code?: string;
        waitlist?: Waitlisted[];
      }>("/api/public/registrations", {
        method: "POST",
        json: {
          first_name: text("first_name"),
          last_name: text("last_name"),
          email: text("email"),
          phone: text("phone").trim(),
          invited_by: text("invited_by") || null,
          can_bring: text("can_bring"),
          locale,
          slot_ids: [...toBook],
          waitlist_slot_ids: toWait,
          accept_privacy: data.get("accept_privacy") === "on",
          accept_disclaimer: data.get("accept_disclaimer") === "on",
          privacy_version: privacy.version,
          disclaimer_version: disclaimer.version,
          optional_consents: optionalConsents,
          consent_locale: locale,
        },
      });
      if (result.result === "created" && result.booking) {
        setOutcome({
          kind: "created",
          booking: result.booking,
          waitlist: result.waitlist ?? [],
          message: result.message,
        });
      } else if (result.result === "waitlisted") {
        setOutcome({
          kind: "waitlisted",
          personalCode: result.personal_code ?? null,
          waitlist: result.waitlist ?? [],
          message: result.message,
        });
      } else {
        setOutcome({ kind: "already", message: result.message ?? t("reg.alreadyFallback") });
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
      if (caught instanceof ApiError && caught.status === 409) {
        setSelected(new Set());
        setEdition(await fetchEdition().catch(() => edition));
      }
    } finally {
      setSending(false);
    }
  }

  const renderOptionalConsent = (
    kind: OptionalConsentKind,
    document: OptionalConsentText | null,
  ) => {
    const choice = optionalChoices[kind];
    const setChoice = (granted: boolean) =>
      setOptionalChoices((current) => ({ ...current, [kind]: granted }));
    return (
      <fieldset key={kind}>
        <legend>{t(kind === "attendance" ? "consent.attendance" : "consent.media")}</legend>
        {document ? (
          <>
            <details>
              <summary>{t("consent.readCurrent", { version: document.version })}</summary>
              <p className="legal">{document.texts[locale]}</p>
            </details>
            <label className="check">
              <input
                type="radio"
                name={`optional_consent_${kind}`}
                checked={choice === true}
                onChange={() => setChoice(true)}
              />
              {t("consent.yes")}
            </label>
            <label className="check">
              <input
                type="radio"
                name={`optional_consent_${kind}`}
                checked={choice === false}
                onChange={() => setChoice(false)}
              />
              {t("consent.no")}
            </label>
          </>
        ) : (
          <p role="status">{t("reg.optionalConsentUnavailable")}</p>
        )}
      </fieldset>
    );
  };

  return (
    <main className="wide">
      <h1>{edition.name}</h1>
      <p className="lead intro-text">{edition.registration_intro?.[locale] ?? t("reg.lead")}</p>
      {first && last && (
        <p className="meta">
          <span className="chip static">
            {formatDayShort(first)} – {formatDayShort(last)}
          </span>
        </p>
      )}
      <div className="hold-banner">
        <p className="hold-title">{tn("reg.holdTitle", edition.hold_days ?? 0)}</p>
        <ol className="steps">
          <li>{t("reg.step1")}</li>
          <li>{t("reg.step2")}</li>
          <li>
            <strong>{t("reg.step3Strong")}</strong> {t("reg.step3Rest")}
          </li>
        </ol>
      </div>
      <SignInPrompt />
      <form id="registration" onSubmit={submit} noValidate={false} className="with-summary">
        <div ref={toolbarRef} className="registration-toolbar">
          <div className="summary-actions">
            <p aria-live="polite" className="fee">
              {toBook.size === 0 && toWait.length > 0 ? (
                t("reg.waitOnly")
              ) : (
                <>
                  {t("reg.fee")} <strong>{formatEuro(fee)}</strong>
                </>
              )}
              {toBook.size > 0 && toWait.length > 0 && (
                <>
                  <br />
                  {tn("reg.waitCount", toWait.length)}
                </>
              )}
            </p>
            <p className="summary-note">{t("reg.confirmedAfterPayment")}</p>
            <button type="submit" form="registration" disabled={sending}>
              {sending ? t("reg.sending") : t("reg.submit")}
            </button>
          </div>
        </div>
        <div className="form-main">
          <section aria-labelledby="when-title">
            <h2 id="when-title" tabIndex={-1}>
              {t("reg.whenTitle")}
            </h2>
            <DayPicker days={pickerDays} selected={selected} onChange={setSelected} />
          </section>

          <fieldset>
            <legend>{t("reg.detailsLegend")}</legend>
            <div className="row">
              <label>
                {t("reg.firstName")}
                <input name="first_name" autoComplete="given-name" required maxLength={100} />
              </label>
              <label>
                {t("reg.lastName")}
                <input name="last_name" autoComplete="family-name" required maxLength={100} />
              </label>
            </div>
            <label>
              {t("login.email")}
              <input type="email" name="email" autoComplete="email" required />
            </label>
            <label>
              {t("reg.phone")}
              <input
                type="tel"
                name="phone"
                autoComplete="tel"
                required
                pattern=".*\S.*"
                maxLength={50}
              />
            </label>
            <label>
              {t("reg.invitedBy")}
              <input name="invited_by" maxLength={200} />
            </label>
            <label>
              {t("reg.canBring")}
              <textarea name="can_bring" rows={3} required maxLength={2000} />
            </label>
          </fieldset>

          <fieldset>
            <legend>{t("reg.consentsLegend")}</legend>
            <details>
              <summary>{t("reg.readPrivacy")}</summary>
              <p className="legal">{privacyCopy.text}</p>
              {privacyCopy.usesOriginal && (
                <p className="legal notice">{t("legal.originalLanguageFallback")}</p>
              )}
            </details>
            <label className="check">
              <input type="checkbox" name="accept_privacy" required />
              {t("reg.acceptPrivacy")}
            </label>
            <details>
              <summary>{t("reg.readDisclaimer")}</summary>
              <p className="legal">{disclaimerCopy.text}</p>
              {disclaimerCopy.usesOriginal && (
                <p className="legal notice">{t("legal.originalLanguageFallback")}</p>
              )}
            </details>
            <label className="check">
              <input type="checkbox" name="accept_disclaimer" required />
              {t("reg.acceptDisclaimer")}
            </label>
            <fieldset>
              <legend>{t("consent.title")}</legend>
              <p>{t("consent.intro")}</p>
              {renderOptionalConsent("attendance", edition.attendance_consent)}
              {renderOptionalConsent("media", edition.media_consent)}
            </fieldset>
          </fieldset>

          {error && (
            <p role="alert" tabIndex={-1} ref={errorRef} className="notice error">
              {error}
            </p>
          )}
        </div>

        <aside className="summary" aria-label={t("reg.summary")}>
          <PresenceSummary
            slots={bookedSlots}
            schedule={schedule}
            className="registration-presences"
          />
          {waitingSlots.length > 0 && (
            <div className="waiting-summary">
              <h3>{t("presence.waitlist")}</h3>
              <ul className="plain">
                {waitingSlots.map((slot) => (
                  <li key={`${slot.date}:${slot.period}`}>
                    {formatDayShort(slot.date)} <span>{slot.period}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {selected.size > 0 && (
            <a
              className="summary-edit"
              href="#when-title"
              onClick={(event) => {
                event.preventDefault();
                const calendarHeading = document.getElementById("when-title");
                calendarHeading?.scrollIntoView?.({ block: "center" });
                calendarHeading?.focus({ preventScroll: true });
              }}
            >
              {t("reg.editPresences")}
            </a>
          )}
        </aside>
      </form>
    </main>
  );
}

function RegistrationAccessLink({ children }: { children: string }) {
  const { locale, t } = useI18n();
  const framed = isInFrame();
  return (
    <>
      <a
        href={`${ROUTES.login}?lang=${locale}`}
        target={framed ? "_blank" : undefined}
        rel={framed ? "noopener" : undefined}
      >
        {children}
      </a>
      {framed && <> {t("reg.opensNewWindow")}</>}
    </>
  );
}

function SignInPrompt() {
  const { t } = useI18n();
  return (
    <p>
      {t("reg.signInPrompt")} <RegistrationAccessLink>{t("reg.signIn")}</RegistrationAccessLink>
    </p>
  );
}

function WaitlistSummary({ waitlist }: { waitlist: Waitlisted[] }) {
  const { t } = useI18n();
  if (waitlist.length === 0) return null;
  return (
    <>
      <h2>{t("reg.waitlistHeading")}</h2>
      <ul>
        {waitlist.map((item) => (
          <li key={item.label}>
            {t("reg.position", { label: item.label, position: item.position })}
          </li>
        ))}
      </ul>
      <p>{t("reg.waitlistNote")}</p>
    </>
  );
}

function WaitlistConfirmation({
  personalCode,
  waitlist,
  message,
}: {
  personalCode: string | null;
  waitlist: Waitlisted[];
  message?: string;
}) {
  const { t } = useI18n();
  return (
    <main>
      <h1>{t("reg.waitConfTitle")}</h1>
      <p role="status">{t("reg.waitConfBody")}</p>
      <WaitlistSummary waitlist={waitlist} />
      {personalCode ? (
        <p>
          {t("reg.waitConfNothingToPay")} <strong>{personalCode}</strong>.
        </p>
      ) : (
        <p>{message ?? t("reg.checkEmailForReference")}</p>
      )}
      <p>
        <RegistrationAccessLink>{t("reg.goToPersonal")}</RegistrationAccessLink>
      </p>
    </main>
  );
}

function Confirmation({
  booking,
  waitlist,
  message,
}: {
  booking: Summary;
  waitlist: Waitlisted[];
  message?: string;
}) {
  const { t } = useI18n();
  return (
    <main>
      <h1>{t("reg.receivedTitle")}</h1>
      <p role="status">{t("reg.receivedBody")}</p>
      <p>
        <strong>
          {t("reg.amount")} {formatEuro(booking.amount_due_cents)}
        </strong>
      </p>
      <p>
        {t("reg.holdUntilBefore")} <strong>{formatDeadline(booking.hold_expires_at)}</strong>.{" "}
        {t("reg.holdUntilAfter")}
      </p>
      <PresenceSummary slots={booking.slots} schedule={booking.schedule} />
      <WaitlistSummary waitlist={waitlist} />
      <h2>{t("reg.howToPay")}</h2>
      {booking.personal_code ? (
        <p>
          {t("reg.reference")} <strong>{booking.personal_code}</strong>
        </p>
      ) : (
        <p>{message ?? t("reg.checkEmailForReference")}</p>
      )}
      {booking.payment_channels.length > 0 ? (
        <ul>
          {booking.payment_channels.map((channel) => (
            <li key={channel.code}>
              <strong>{channel.label}</strong>
              <br />
              <span className="legal">{channel.instructions}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>{t("reg.paymentSoon")}</p>
      )}
      <p>
        <RegistrationAccessLink>{t("reg.goToPersonal")}</RegistrationAccessLink>
      </p>
    </main>
  );
}
