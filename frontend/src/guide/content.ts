import type { Locale } from "../i18n/locale";
import { ROUTES } from "../routes";
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

const participantFiles = import.meta.glob("./*/participant/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

// Only admins open this guide: loaded on demand, so the chunk is not downloaded by participants.
const adminFiles = import.meta.glob("./*/admin/*.md", {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;

/** The files of one language and audience: `./en/participant/*.md`. */
function inFolder<T>(
  files: Record<string, T>,
  locale: Locale,
  audience: string,
): Record<string, T> {
  const prefix = `./${locale}/${audience}/`;
  return Object.fromEntries(Object.entries(files).filter(([path]) => path.startsWith(prefix)));
}

export function participantGuide(locale: Locale): GuideSection[] {
  return parseSections(inFolder(participantFiles, locale, "participant"));
}

export async function loadAdminGuide(locale: Locale): Promise<GuideSection[]> {
  // The English organizers' guide arrives with the English panel (MVP 12): until then the
  // Italian one is shown to everybody.
  let loaders = inFolder(adminFiles, locale, "admin");
  if (Object.keys(loaders).length === 0) loaders = inFolder(adminFiles, "it", "admin");
  const entries = await Promise.all(
    Object.entries(loaders).map(async ([path, load]) => [path, await load()] as const),
  );
  return parseSections(Object.fromEntries(entries));
}

const ADMIN_PAGES: Record<string, string> = {
  "/admin": "people",
  "/admin/days": "days-and-slots",
  "/admin/week": "week",
  "/admin/meals": "meals",
  "/admin/activities": "activities",
  "/admin/contributions": "contributions",
  "/admin/report": "report",
  "/admin/to-collect": "to-collect",
  "/admin/to-review": "to-review",
  "/admin/admins": "admins",
  "/admin/settings": "settings",
};

/** The guide section that explains an admin page, so the help link opens the right place. */
export function adminGuideSlug(pathname: string): string | undefined {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (/^\/admin\/registrations\/[^/]+$/.test(path)) return "people";
  if (/^\/admin\/activities\/[^/]+$/.test(path)) return "activities";
  return ADMIN_PAGES[path];
}

/** Link to the admin guide, at the section of the current page when there is one. */
export function adminGuideLink(pathname: string): string {
  const slug = adminGuideSlug(pathname);
  return `${ROUTES.guide}?tab=organizers${slug ? `#${slug}` : ""}`;
}
