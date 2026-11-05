import { canonicalPath, canonicalSearch, ROUTES } from "./routes";

describe("canonicalPath", () => {
  it.each([
    ["/iscrizione", "/register"],
    ["/iscrizione/", "/register"],
    ["/accedi", "/login"],
    ["/accedi/verifica", "/login/verify"],
    ["/io", "/me"],
    ["/guida", "/guide"],
    ["/admin/giorni", "/admin/days"],
    ["/admin/settimana", "/admin/week"],
    ["/admin/pasti", "/admin/meals"],
    ["/admin/attivita", "/admin/activities"],
    ["/admin/attivita/3", "/admin/activities/3"],
    ["/admin/iscrizioni/12", "/admin/registrations/12"],
    ["/admin/contributi", "/admin/contributions"],
    ["/admin/da-incassare", "/admin/to-collect"],
    ["/admin/da-verificare", "/admin/to-review"],
    ["/admin/amministratori", "/admin/admins"],
    ["/admin/impostazioni", "/admin/settings"],
  ])("%s -> %s", (alias, english) => {
    expect(canonicalPath(alias)).toBe(english);
  });

  it("leaves English and unknown addresses alone", () => {
    for (const path of Object.values(ROUTES)) expect(canonicalPath(path)).toBeNull();
    expect(canonicalPath("/admin/registrations/1")).toBeNull();
    expect(canonicalPath("/non-esiste")).toBeNull();
  });
});

describe("canonicalSearch", () => {
  it("rewrites the old guide tab", () => {
    expect(canonicalSearch("?scheda=organizzatori")).toBe("?tab=organizers");
    expect(canonicalSearch("?scheda=partecipanti")).toBe("?tab=participants");
  });

  it("keeps other queries, such as the magic link token", () => {
    expect(canonicalSearch("?token=abc")).toBe("?token=abc");
    expect(canonicalSearch("")).toBe("");
  });
});
