/** Single source of the app addresses. They are in English; Italian ones are kept only as aliases. */
export const ROUTES = {
  home: "/",
  register: "/register",
  login: "/login",
  loginVerify: "/login/verify",
  me: "/me",
  guide: "/guide",
  admin: "/admin",
  adminDays: "/admin/days",
  adminWeek: "/admin/week",
  adminMeals: "/admin/meals",
  adminActivities: "/admin/activities",
  adminContributions: "/admin/contributions",
  adminReport: "/admin/report",
  adminToCollect: "/admin/to-collect",
  adminToReview: "/admin/to-review",
  adminAdmins: "/admin/admins",
  adminSettings: "/admin/settings",
} as const;

export function adminRegistrationPath(id: number | string): string {
  return `/admin/registrations/${id}`;
}

export function adminActivityPath(id: number | string): string {
  return `/admin/activities/${id}`;
}

/** Italian address (as someone may type it) -> English address. Only exact, fixed segments. */
const ALIASES: Record<string, string> = {
  "/iscrizione": ROUTES.register,
  "/accedi": ROUTES.login,
  "/accedi/verifica": ROUTES.loginVerify,
  "/io": ROUTES.me,
  "/guida": ROUTES.guide,
  "/admin/giorni": ROUTES.adminDays,
  "/admin/settimana": ROUTES.adminWeek,
  "/admin/pasti": ROUTES.adminMeals,
  "/admin/attivita": ROUTES.adminActivities,
  "/admin/contributi": ROUTES.adminContributions,
  "/admin/da-incassare": ROUTES.adminToCollect,
  "/admin/da-verificare": ROUTES.adminToReview,
  "/admin/amministratori": ROUTES.adminAdmins,
  "/admin/impostazioni": ROUTES.adminSettings,
};

/** Italian segments of the pages with an id: `/admin/iscrizioni/12`, `/admin/attivita/3`. */
const ID_ALIASES: [RegExp, (id: string) => string][] = [
  [/^\/admin\/iscrizioni\/([^/]+)$/, adminRegistrationPath],
  [/^\/admin\/attivita\/([^/]+)$/, adminActivityPath],
];

function trimmed(pathname: string): string {
  return pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
}

/** The English address of an Italian alias, or null when the path is not an alias. */
export function canonicalPath(pathname: string): string | null {
  const path = trimmed(pathname);
  if (ALIASES[path]) return ALIASES[path];
  for (const [pattern, build] of ID_ALIASES) {
    const match = pattern.exec(path);
    if (match) return build(match[1]);
  }
  return null;
}

/** Query parameter names and values of the guide page, in their old Italian form. */
const LEGACY_TAB_VALUES: Record<string, string> = {
  partecipanti: "participants",
  organizzatori: "organizers",
  novita: "news",
};

/** Rewrites the old Italian guide query (`?scheda=organizzatori`) to `?tab=organizers`. */
export function canonicalSearch(search: string): string {
  const params = new URLSearchParams(search);
  const legacy = params.get("scheda");
  if (legacy === null) return search;
  params.delete("scheda");
  if (!params.has("tab")) params.set("tab", LEGACY_TAB_VALUES[legacy] ?? legacy);
  const text = params.toString();
  return text ? `?${text}` : "";
}

/** Section anchors of the guide as they were when the files had Italian names. */
const LEGACY_GUIDE_ANCHORS: Record<string, string> = {
  // organizers
  persone: "people",
  "giorni-e-slot": "days-and-slots",
  settimana: "week",
  pasti: "meals",
  attivita: "activities",
  contributi: "contributions",
  "da-verificare": "to-review",
  amministratori: "admins",
  impostazioni: "settings",
  "lista-attesa-e-piu-uno": "waitlist-and-plus-one",
  "da-incassare": "to-collect",
  // participants
  iscriversi: "signing-up",
  accedere: "signing-in",
  pagare: "paying",
  "cambiare-slot": "changing-slots",
  "lista-attesa": "waitlist",
  disdetta: "cancelling",
};

/** The anchor to open on the English guide for an old Italian one (`#giorni-e-slot`).
 * Anchors that are not old ones, such as `#report`, stay as they are. */
export function canonicalGuideHash(hash: string): string {
  if (!hash.startsWith("#")) return hash;
  const mapped = LEGACY_GUIDE_ANCHORS[hash.slice(1)];
  return mapped ? `#${mapped}` : hash;
}
