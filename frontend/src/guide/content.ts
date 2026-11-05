export type GuideSection = { slug: string; title: string; body: string };

/**
 * Turns the Markdown files of a guide into sections. File names carry the order and the anchor:
 * `./admin/03-giorni-e-slot.md` becomes the section `giorni-e-slot`. The first `# Title` line is
 * the section title and is not repeated in the body.
 */
export function parseSections(files: Record<string, string>): GuideSection[] {
  return Object.keys(files)
    .sort()
    .map((path) => {
      const slug = (path.split("/").pop() ?? path).replace(/\.md$/, "").replace(/^\d+-/, "");
      const source = files[path].trim();
      const heading = source.match(/^#\s+(.+)\n?/);
      return {
        slug,
        title: heading ? heading[1].trim() : slug.replace(/-/g, " "),
        body: heading ? source.slice(heading[0].length).trim() : source,
      };
    });
}

const participantFiles = import.meta.glob("./partecipante/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

// Only admins open this guide: loaded on demand, so the chunk is not downloaded by participants.
const adminFiles = import.meta.glob("./admin/*.md", {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;

export const participantGuide: GuideSection[] = parseSections(participantFiles);

export async function loadAdminGuide(): Promise<GuideSection[]> {
  const entries = await Promise.all(
    Object.entries(adminFiles).map(async ([path, load]) => [path, await load()] as const),
  );
  return parseSections(Object.fromEntries(entries));
}

const ADMIN_PAGES: Record<string, string> = {
  "/admin": "persone",
  "/admin/giorni": "giorni-e-slot",
  "/admin/settimana": "settimana",
  "/admin/pasti": "pasti",
  "/admin/attivita": "attivita",
  "/admin/contributi": "contributi",
  "/admin/report": "report",
  "/admin/da-incassare": "da-incassare",
  "/admin/da-verificare": "da-verificare",
  "/admin/amministratori": "amministratori",
  "/admin/impostazioni": "impostazioni",
};

/** The guide section that explains an admin page, so the help link opens the right place. */
export function adminGuideSlug(pathname: string): string | undefined {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (/^\/admin\/iscrizioni\/[^/]+$/.test(path)) return "persone";
  if (/^\/admin\/attivita\/[^/]+$/.test(path)) return "attivita";
  return ADMIN_PAGES[path];
}

/** Link to the admin guide, at the section of the current page when there is one. */
export function adminGuideLink(pathname: string): string {
  const slug = adminGuideSlug(pathname);
  return `/guida?scheda=organizzatori${slug ? `#${slug}` : ""}`;
}
