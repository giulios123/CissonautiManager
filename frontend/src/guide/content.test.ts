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
    ["/admin", "people"],
    ["/admin/days", "days-and-slots"],
    ["/admin/registrations/12", "people"],
    ["/admin/activities/3", "activities"],
    ["/admin/report/", "report"],
  ])("%s opens the section %s", (path, slug) => {
    expect(adminGuideSlug(path)).toBe(slug);
    expect(adminGuideLink(path)).toBe(`/guide?tab=organizers#${slug}`);
  });

  it("opens the guide without a section for an unknown page", () => {
    expect(adminGuideLink("/admin/altro")).toBe("/guide?tab=organizers");
  });
});

describe("participant guide", () => {
  it.each(["it", "en"] as const)("is built from the %s files in the repository", (locale) => {
    const sections = participantGuide(locale);
    expect(sections.length).toBeGreaterThan(0);
    for (const section of sections) {
      expect(section.title).not.toBe("");
      expect(section.body).not.toBe("");
    }
  });

  it("has the same sections, in the same order, in Italian and English", () => {
    expect(participantGuide("en").map((s) => s.slug)).toEqual(
      participantGuide("it").map((s) => s.slug),
    );
  });

  it("is really translated: no English section repeats the Italian text", () => {
    const italian = participantGuide("it");
    participantGuide("en").forEach((section, index) => {
      expect(section.title).not.toBe(italian[index].title);
      expect(section.body).not.toBe(italian[index].body);
    });
  });
});

describe("admin guide", () => {
  it("has a section for every page of the panel", async () => {
    const slugs = (await loadAdminGuide("it")).map((section) => section.slug);
    const pages = [
      "/admin",
      "/admin/days",
      "/admin/week",
      "/admin/meals",
      "/admin/activities",
      "/admin/contributions",
      "/admin/report",
      "/admin/to-collect",
      "/admin/to-review",
      "/admin/admins",
      "/admin/settings",
    ];
    for (const page of pages) expect(slugs).toContain(adminGuideSlug(page));
  });

  it("gives every section a title and a body", async () => {
    for (const section of await loadAdminGuide("it")) {
      expect(section.title).not.toBe("");
      expect(section.body).not.toBe("");
    }
  });
});
