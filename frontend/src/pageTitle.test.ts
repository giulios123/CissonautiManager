import { titleFor } from "./pageTitle";

describe("titleFor", () => {
  it.each([
    ["/", "Cissonauti Summer Camp"],
    ["/register", "Iscrizione · Cissonauti Summer Camp"],
    ["/me", "La tua iscrizione · Cissonauti Summer Camp"],
    ["/guide", "Guida · Cissonauti Summer Camp"],
    ["/admin", "Persone · Cissonauti Summer Camp"],
    ["/admin/to-collect", "Da incassare · Cissonauti Summer Camp"],
    ["/admin/to-review", "Pagamenti da verificare · Cissonauti Summer Camp"],
    ["/admin/report", "Report · Cissonauti Summer Camp"],
    ["/admin/registrations/12", "Scheda iscrizione · Cissonauti Summer Camp"],
    ["/admin/activities/3", "Attività · Cissonauti Summer Camp"],
    ["/register/", "Iscrizione · Cissonauti Summer Camp"],
    ["/non-esiste", "Pagina non trovata · Cissonauti Summer Camp"],
  ])("%s -> %s", (path, title) => {
    expect(titleFor(path)).toBe(title);
  });

  it("gives every route a different title", () => {
    const paths = Object.keys({
      "/register": 1,
      "/login": 1,
      "/login/verify": 1,
      "/me": 1,
      "/guide": 1,
      "/admin": 1,
      "/admin/days": 1,
      "/admin/week": 1,
      "/admin/meals": 1,
      "/admin/activities": 1,
      "/admin/contributions": 1,
      "/admin/report": 1,
      "/admin/to-collect": 1,
      "/admin/to-review": 1,
      "/admin/admins": 1,
      "/admin/settings": 1,
    });
    expect(new Set(paths.map((path) => titleFor(path))).size).toBe(paths.length);
  });
});

describe("titleFor in English", () => {
  it.each([
    ["/register", "Registration · Cissonauti Summer Camp"],
    ["/me", "Your registration · Cissonauti Summer Camp"],
    ["/admin/to-collect", "To collect · Cissonauti Summer Camp"],
    ["/nowhere", "Page not found · Cissonauti Summer Camp"],
  ])("%s -> %s", (path, title) => {
    expect(titleFor(path, "en")).toBe(title);
  });
});
