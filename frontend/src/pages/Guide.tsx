import { marked } from "marked";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";
import { intlTag } from "../i18n/locale";
import { loadAdminGuide, participantGuide, type GuideSection } from "../guide/content";
import { useI18n, type MessageKey } from "../i18n";
import { ROUTES } from "../routes";

type Release = { version: string; date: string | null; features: string[]; fixes: string[] };
type Version = { version: string; built_at: string | null };

const TABS: readonly { id: "organizers" | "participants" | "news"; label: MessageKey }[] = [
  { id: "organizers", label: "guide.tabOrganizers" },
  { id: "participants", label: "guide.tabParticipants" },
  { id: "news", label: "guide.tabNews" },
];
type TabId = (typeof TABS)[number]["id"];

function formatDate(iso: string | null): string {
  return iso
    ? new Intl.DateTimeFormat(intlTag(), { dateStyle: "long", timeZone: "Europe/Rome" }).format(
        new Date(iso),
      )
    : "";
}

/** The guide files are written in the repository, so their Markdown is trusted. */
function Markdown({ source }: { source: string }) {
  const html = useMemo(() => marked.parse(source, { async: false }), [source]);
  return <div className="guide-body" dangerouslySetInnerHTML={{ __html: html }} />;
}

function Sections({ sections }: { sections: GuideSection[] }) {
  return (
    <>
      <nav aria-label="Indice della guida" className="guide-index">
        <ul>
          {sections.map((section) => (
            <li key={section.slug}>
              <a href={`#${section.slug}`}>{section.title}</a>
            </li>
          ))}
        </ul>
      </nav>
      {sections.map((section) => (
        <section
          key={section.slug}
          id={section.slug}
          aria-labelledby={`${section.slug}-title`}
          className="card guide-section"
        >
          <h2 id={`${section.slug}-title`}>{section.title}</h2>
          <Markdown source={section.body} />
        </section>
      ))}
    </>
  );
}

function ReleaseList({ items, title }: { items: string[]; title: string }) {
  if (items.length === 0) return null;
  return (
    <>
      <h4>{title}</h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </>
  );
}

function ReleaseNotes() {
  const { t } = useI18n();
  const [releases, setReleases] = useState<Release[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<{ releases: Release[] }>("/api/admin/release-notes")
      .then((data) => setReleases(data.releases))
      .catch(() => setFailed(true));
  }, []);

  if (failed) return <p className="notice error">{t("guide.newsFailed")}</p>;
  if (releases === null) return <p aria-busy="true">{t("common.loading")}</p>;
  if (releases.length === 0) {
    return <p>{t("guide.newsEmpty")}</p>;
  }
  return (
    <>
      <p className="legal">{t("guide.newsNote")}</p>
      {releases.map((release) => (
        <article key={release.version} className="card">
          <h3>
            {t("guide.release")} <span className="mono">{release.version}</span>
            {release.date && <> · {formatDate(release.date)}</>}
          </h3>
          <ReleaseList items={release.features} title={t("guide.features")} />
          <ReleaseList items={release.fixes} title={t("guide.fixes")} />
        </article>
      ))}
    </>
  );
}

function VersionLine() {
  const { t } = useI18n();
  const [version, setVersion] = useState<Version | null>(null);
  useEffect(() => {
    api<Version>("/api/version")
      .then(setVersion)
      .catch(() => setVersion(null));
  }, []);
  if (!version) return null;
  if (version.version === "dev") return <p className="legal">{t("guide.devVersion")}</p>;
  return (
    <p className="legal">
      {t("guide.version")} <span className="mono">{version.version.slice(0, 7)}</span>
      {version.built_at && <> {t("guide.builtOn", { date: formatDate(version.built_at) })}</>}
    </p>
  );
}

function AdminGuide({ initial }: { initial: TabId }) {
  const { t, locale } = useI18n();
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab");
  const tab: TabId = TABS.some((item) => item.id === requested) ? (requested as TabId) : initial;
  const [adminSections, setAdminSections] = useState<GuideSection[] | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const { hash } = useLocation();

  useEffect(() => {
    void loadAdminGuide(locale).then(setAdminSections);
  }, [locale]);

  // The sections appear after the page has loaded, so the browser cannot scroll to the anchor.
  const ready = tab === "organizers" ? adminSections !== null : true;
  useEffect(() => {
    if (ready && hash) document.getElementById(hash.slice(1))?.scrollIntoView?.();
  }, [ready, hash, tab]);

  function select(id: TabId) {
    setParams({ tab: id }, { replace: true });
  }

  function onKeyDown(event: KeyboardEvent, index: number) {
    const last = TABS.length - 1;
    const next =
      event.key === "ArrowRight"
        ? (index + 1) % TABS.length
        : event.key === "ArrowLeft"
          ? (index - 1 + TABS.length) % TABS.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? last
              : null;
    if (next === null) return;
    event.preventDefault();
    select(TABS[next].id);
    tabRefs.current[TABS[next].id]?.focus();
  }

  return (
    <>
      <div role="tablist" aria-label={t("guide.tablist")} className="guide-tabs">
        {TABS.map((tabItem, index) => (
          <button
            key={tabItem.id}
            ref={(element) => {
              tabRefs.current[tabItem.id] = element;
            }}
            type="button"
            role="tab"
            id={`tab-${tabItem.id}`}
            aria-selected={tab === tabItem.id}
            aria-controls={`panel-${tabItem.id}`}
            tabIndex={tab === tabItem.id ? 0 : -1}
            onClick={() => select(tabItem.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
          >
            {t(tabItem.label)}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === "organizers" &&
          (adminSections ? (
            <Sections sections={adminSections} />
          ) : (
            <p aria-busy="true">{t("common.loading")}</p>
          ))}
        {tab === "participants" && (
          <>
            <p className="lead">{t("guide.participantsIntro")}</p>
            <Sections sections={participantGuide(locale)} />
          </>
        )}
        {tab === "news" && <ReleaseNotes />}
      </div>
    </>
  );
}

export function Guide() {
  const { t, locale } = useI18n();
  const state = useMe();
  const { hash } = useLocation();

  useEffect(() => {
    if (state.status === "user" && state.me.role !== "admin" && hash) {
      document.getElementById(hash.slice(1))?.scrollIntoView?.();
    }
  }, [state, hash]);

  if (state.status === "loading") return <main aria-busy="true">{t("common.loading")}</main>;
  if (state.status === "anonymous") return <Navigate to={ROUTES.login} replace />;
  const isAdmin = state.me.role === "admin";

  return (
    <main className={isAdmin ? "wide" : undefined}>
      <h1>{t("title.guide")}</h1>
      <p>
        <Link to={isAdmin ? ROUTES.admin : ROUTES.me}>
          {isAdmin ? t("guide.backAdmin") : t("guide.backParticipant")}
        </Link>
      </p>
      {isAdmin ? (
        <AdminGuide initial="organizers" />
      ) : (
        <Sections sections={participantGuide(locale)} />
      )}
      <VersionLine />
    </main>
  );
}
