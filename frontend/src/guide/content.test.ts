import {
  ADMIN_GUIDE_LINK,
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
  ])("%s is explained in the section %s", (path, slug) => {
    expect(adminGuideSlug(path)).toBe(slug);
  });

  it("has no section for an unknown page", () => {
    expect(adminGuideSlug("/admin/altro")).toBeUndefined();
  });

  it("opens the guide at the top, without a section", () => {
    expect(ADMIN_GUIDE_LINK).toBe("/guide?tab=organizers");
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
      "/admin/guests",
      "/admin/contributions",
      "/admin/report",
      "/admin/to-collect",
      "/admin/to-review",
      "/admin/admins",
      "/admin/settings",
    ];
    for (const page of pages) expect(slugs).toContain(adminGuideSlug(page));
  });

  it.each(["it", "en"] as const)("gives every %s section a title and a body", async (locale) => {
    const sections = await loadAdminGuide(locale);
    expect(sections.length).toBeGreaterThan(0);
    for (const section of sections) {
      expect(section.title).not.toBe("");
      expect(section.body).not.toBe("");
    }
  });

  it("has the same sections, in the same order, in Italian and English", async () => {
    const english = (await loadAdminGuide("en")).map((s) => s.slug);
    expect(english).toEqual((await loadAdminGuide("it")).map((s) => s.slug));
  });

  it("is really translated: no English section repeats the Italian text", async () => {
    const italian = await loadAdminGuide("it");
    (await loadAdminGuide("en")).forEach((section, index) => {
      expect(section.title).not.toBe(italian[index].title);
      expect(section.body).not.toBe(italian[index].body);
    });
  });

  it("has an English section for every page of the panel", async () => {
    const slugs = (await loadAdminGuide("en")).map((section) => section.slug);
    for (const page of ["/admin", "/admin/days", "/admin/to-collect", "/admin/settings"])
      expect(slugs).toContain(adminGuideSlug(page));
  });
});
