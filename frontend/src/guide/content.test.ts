import {
  adminGuideLink,
  adminGuideSlug,
  loadAdminGuide,
  parseSections,
  participantGuide,
} from "./content";

describe("parseSections", () => {
  it("orders by file name and takes slug and title from the file", () => {
    const sections = parseSections({
      "./x/02-pagare.md": "# Pagare\n\nCausale.",
      "./x/01-iscriversi.md": "# Iscriversi\n\nScegli i giorni.",
    });
    expect(sections.map((s) => s.slug)).toEqual(["iscriversi", "pagare"]);
    expect(sections[0]).toEqual({
      slug: "iscriversi",
      title: "Iscriversi",
      body: "Scegli i giorni.",
    });
  });

  it("falls back to the slug when the file has no title", () => {
    const [section] = parseSections({ "./x/01-lista-attesa.md": "Solo testo." });
    expect(section.title).toBe("lista attesa");
    expect(section.body).toBe("Solo testo.");
  });
});

describe("admin guide links", () => {
  it.each([
    ["/admin", "persone"],
    ["/admin/giorni", "giorni-e-slot"],
    ["/admin/iscrizioni/12", "persone"],
    ["/admin/attivita/3", "attivita"],
    ["/admin/report/", "report"],
  ])("%s opens the section %s", (path, slug) => {
    expect(adminGuideSlug(path)).toBe(slug);
    expect(adminGuideLink(path)).toBe(`/guida?scheda=organizzatori#${slug}`);
  });

  it("opens the guide without a section for an unknown page", () => {
    expect(adminGuideLink("/admin/altro")).toBe("/guida?scheda=organizzatori");
  });
});

describe("participant guide", () => {
  it("is built from the files in the repository", () => {
    expect(participantGuide.length).toBeGreaterThan(0);
    for (const section of participantGuide) {
      expect(section.title).not.toBe("");
      expect(section.body).not.toBe("");
    }
  });
});

describe("admin guide", () => {
  it("has a section for every page of the panel", async () => {
    const slugs = (await loadAdminGuide()).map((section) => section.slug);
    const pages = [
      "/admin",
      "/admin/giorni",
      "/admin/settimana",
      "/admin/pasti",
      "/admin/attivita",
      "/admin/contributi",
      "/admin/report",
      "/admin/da-incassare",
      "/admin/da-verificare",
      "/admin/amministratori",
      "/admin/impostazioni",
    ];
    for (const page of pages) expect(slugs).toContain(adminGuideSlug(page));
  });

  it("gives every section a title and a body", async () => {
    for (const section of await loadAdminGuide()) {
      expect(section.title).not.toBe("");
      expect(section.body).not.toBe("");
    }
  });
});
