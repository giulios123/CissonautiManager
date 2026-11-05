import { titleFor } from "./pageTitle";

describe("titleFor", () => {
  it.each([
    ["/", "Cissonauti Summer Camp"],
    ["/iscrizione", "Iscrizione · Cissonauti Summer Camp"],
    ["/io", "La tua iscrizione · Cissonauti Summer Camp"],
    ["/admin", "Persone · Cissonauti Summer Camp"],
    ["/admin/da-verificare", "Pagamenti da verificare · Cissonauti Summer Camp"],
    ["/admin/report", "Report · Cissonauti Summer Camp"],
    ["/admin/iscrizioni/12", "Scheda iscrizione · Cissonauti Summer Camp"],
    ["/admin/attivita/3", "Attività · Cissonauti Summer Camp"],
    ["/iscrizione/", "Iscrizione · Cissonauti Summer Camp"],
    ["/non-esiste", "Pagina non trovata · Cissonauti Summer Camp"],
  ])("%s -> %s", (path, title) => {
    expect(titleFor(path)).toBe(title);
  });

  it("gives every route a different title", () => {
    const paths = Object.keys({
      "/iscrizione": 1,
      "/accedi": 1,
      "/accedi/verifica": 1,
      "/io": 1,
      "/admin": 1,
      "/admin/giorni": 1,
      "/admin/settimana": 1,
      "/admin/pasti": 1,
      "/admin/attivita": 1,
      "/admin/contributi": 1,
      "/admin/report": 1,
      "/admin/da-verificare": 1,
      "/admin/amministratori": 1,
      "/admin/impostazioni": 1,
    });
    expect(new Set(paths.map(titleFor)).size).toBe(paths.length);
  });
});
