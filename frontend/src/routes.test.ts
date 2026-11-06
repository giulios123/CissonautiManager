import { canonicalGuideHash, canonicalPath, canonicalSearch, ROUTES } from "./routes";

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

describe("canonicalGuideHash", () => {
  it.each([
    ["#giorni-e-slot", "#days-and-slots"],
    ["#persone", "#people"],
    ["#da-incassare", "#to-collect"],
    ["#lista-attesa-e-piu-uno", "#waitlist-and-plus-one"],
    ["#iscriversi", "#signing-up"],
    ["#disdetta", "#cancelling"],
  ])("%s -> %s", (old, current) => {
    expect(canonicalGuideHash(old)).toBe(current);
  });

  it("leaves current anchors and empty hashes alone", () => {
    expect(canonicalGuideHash("#days-and-slots")).toBe("#days-and-slots");
    expect(canonicalGuideHash("#report")).toBe("#report");
    expect(canonicalGuideHash("")).toBe("");
  });

  it("covers every old file name of the guide", async () => {
    // The anchors are the file names without their number: every renamed section must be mapped.
    const old = [
      "persone",
      "giorni-e-slot",
      "settimana",
      "pasti",
      "attivita",
      "contributi",
      "report",
      "da-verificare",
      "amministratori",
      "impostazioni",
      "lista-attesa-e-piu-uno",
      "da-incassare",
      "iscriversi",
      "accedere",
      "pagare",
      "cambiare-slot",
      "lista-attesa",
      "disdetta",
    ];
    const { loadAdminGuide, participantGuide } = await import("./guide/content");
    const slugs = new Set([
      ...participantGuide("en").map((s) => s.slug),
      ...(await loadAdminGuide("en")).map((s) => s.slug),
    ]);
    for (const slug of old) expect(slugs).toContain(canonicalGuideHash(`#${slug}`).slice(1));
  });
});
