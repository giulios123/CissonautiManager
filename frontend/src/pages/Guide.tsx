import { marked } from "marked";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";
import { intlTag } from "../i18n/locale";
import { loadAdminGuide, participantGuide, type GuideSection } from "../guide/content";

type Release = { version: string; date: string | null; features: string[]; fixes: string[] };
type Version = { version: string; built_at: string | null };

const TABS = [
  { id: "organizers", label: "Organizzatori" },
  { id: "participants", label: "Partecipanti" },
  { id: "news", label: "Novità" },
] as const;
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
  const [releases, setReleases] = useState<Release[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<{ releases: Release[] }>("/api/admin/release-notes")
      .then((data) => setReleases(data.releases))
      .catch(() => setFailed(true));
  }, []);

  if (failed) return <p className="notice error">Non riesco a caricare le novità. Riprova.</p>;
  if (releases === null) return <p aria-busy="true">Caricamento…</p>;
  if (releases.length === 0) {
    return <p>Le novità compaiono qui dopo il primo rilascio.</p>;
  }
  return (
    <>
      <p className="legal">
        Elenco generato in automatico dai messaggi di commit a ogni rilascio, per questo i testi
        sono in inglese.
      </p>
      {releases.map((release) => (
        <article key={release.version} className="card">
          <h3>
            Rilascio <span className="mono">{release.version}</span>
            {release.date && <> · {formatDate(release.date)}</>}
          </h3>
          <ReleaseList items={release.features} title="Novità" />
          <ReleaseList items={release.fixes} title="Correzioni" />
        </article>
      ))}
    </>
  );
}

function VersionLine() {
  const [version, setVersion] = useState<Version | null>(null);
  useEffect(() => {
    api<Version>("/api/version")
      .then(setVersion)
      .catch(() => setVersion(null));
  }, []);
  if (!version) return null;
  if (version.version === "dev") return <p className="legal">Versione di sviluppo.</p>;
  return (
    <p className="legal">
      Versione <span className="mono">{version.version.slice(0, 7)}</span>
      {version.built_at && <> del {formatDate(version.built_at)}</>}
    </p>
  );
}

function AdminGuide({ initial }: { initial: TabId }) {
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab");
  const tab: TabId = TABS.some((t) => t.id === requested) ? (requested as TabId) : initial;
  const [adminSections, setAdminSections] = useState<GuideSection[] | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const { hash } = useLocation();

  useEffect(() => {
    void loadAdminGuide().then(setAdminSections);
  }, []);

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
      <div role="tablist" aria-label="Sezioni della guida" className="guide-tabs">
        {TABS.map((t, index) => (
          <button
            key={t.id}
            ref={(element) => {
              tabRefs.current[t.id] = element;
            }}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`panel-${t.id}`}
            tabIndex={tab === t.id ? 0 : -1}
            onClick={() => select(t.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === "organizers" &&
          (adminSections ? (
            <Sections sections={adminSections} />
          ) : (
            <p aria-busy="true">Caricamento…</p>
          ))}
        {tab === "participants" && (
          <>
            <p className="lead">
              È la guida che vedono i partecipanti: utile per aiutare chi te la chiede.
            </p>
            <Sections sections={participantGuide} />
          </>
        )}
        {tab === "news" && <ReleaseNotes />}
      </div>
    </>
  );
}

export function Guide() {
  const state = useMe();
  const { hash } = useLocation();

  useEffect(() => {
    if (state.status === "user" && state.me.role !== "admin" && hash) {
      document.getElementById(hash.slice(1))?.scrollIntoView?.();
    }
  }, [state, hash]);

  if (state.status === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state.status === "anonymous") return <Navigate to="/login" replace />;
  const isAdmin = state.me.role === "admin";

  return (
    <main className={isAdmin ? "wide" : undefined}>
      <h1>Guida</h1>
      <p>
        <Link to={isAdmin ? "/admin" : "/me"}>
          {isAdmin ? "Torna al pannello organizzatori" : "Torna alla tua iscrizione"}
        </Link>
      </p>
      {isAdmin ? <AdminGuide initial="organizers" /> : <Sections sections={participantGuide} />}
      <VersionLine />
    </main>
  );
}
