import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { adminMe } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const VERSION = { version: "abc1234def5678", built_at: "2026-11-05T10:30:00Z" };
const RELEASES = {
  releases: [
    {
      version: "abc1234",
      date: "2026-11-05T10:30:00+01:00",
      features: ["Add the guide"],
      fixes: ["Fix the title"],
    },
  ],
};

function stub(me: unknown | null, releases: unknown = RELEASES) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      urls.push(url);
      if (url === "/api/me") {
        return me === null
          ? new Response(JSON.stringify({ detail: "Not authenticated" }), { status: 401 })
          : new Response(JSON.stringify(me), { status: 200 });
      }
      if (url === "/api/version") return new Response(JSON.stringify(VERSION), { status: 200 });
      if (url === "/api/admin/release-notes") {
        return new Response(JSON.stringify(releases), { status: 200 });
      }
      return new Response("{}", { status: 404 });
    }),
  );
  return urls;
}

function renderGuide(path = "/guida") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

const participantMe = { ...adminMe, role: "participant", first_name: "Ada" };

describe("Guide", () => {
  it("sends anonymous visitors to the login", async () => {
    const urls = stub(null);
    renderGuide();
    await waitFor(() => expect(urls).toContain("/api/me"));
    await waitFor(() => expect(screen.queryByRole("heading", { name: "Guida" })).toBeNull());
    expect(urls).not.toContain("/api/admin/release-notes");
  });

  it("shows participants only their guide, without tabs or release notes", async () => {
    const urls = stub(participantMe);
    renderGuide();
    expect(await screen.findByRole("heading", { name: "Guida", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Iscriversi", level: 2 })).toBeInTheDocument();
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.queryByRole("heading", { name: "Persone" })).toBeNull();
    expect(screen.getByRole("link", { name: "Torna alla tua iscrizione" })).toHaveAttribute(
      "href",
      "/io",
    );
    expect(await screen.findByText("abc1234")).toBeInTheDocument();
    expect(urls).not.toContain("/api/admin/release-notes");
  });

  it("gives admins three tabs, starting from the organizers guide", async () => {
    stub(adminMe);
    renderGuide();
    const tabs = await screen.findAllByRole("tab");
    expect(tabs.map((tab) => tab.textContent)).toEqual(["Organizzatori", "Partecipanti", "Novità"]);
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByRole("heading", { name: "Persone", level: 2 })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Iscriversi" })).toBeNull();
  });

  it("shows the participants guide in its tab", async () => {
    stub(adminMe);
    renderGuide();
    await userEvent.click(await screen.findByRole("tab", { name: "Partecipanti" }));
    expect(
      await screen.findByRole("heading", { name: "Iscriversi", level: 2 }),
    ).toBeInTheDocument();
  });

  it("loads the release notes only when the tab is opened", async () => {
    const urls = stub(adminMe);
    renderGuide();
    await screen.findByRole("heading", { name: "Persone", level: 2 });
    expect(urls).not.toContain("/api/admin/release-notes");

    await userEvent.click(screen.getByRole("tab", { name: "Novità" }));
    expect(await screen.findByText("Add the guide")).toBeInTheDocument();
    expect(screen.getByText("Fix the title")).toBeInTheDocument();
    expect(urls).toContain("/api/admin/release-notes");
  });

  it("says so when there are no release notes yet", async () => {
    stub(adminMe, { releases: [] });
    renderGuide("/guida?scheda=novita");
    expect(await screen.findByText(/dopo il primo rilascio/)).toBeInTheDocument();
  });

  it("moves between tabs with the arrow keys", async () => {
    stub(adminMe);
    renderGuide();
    const first = await screen.findByRole("tab", { name: "Organizzatori" });
    first.focus();
    await userEvent.keyboard("{ArrowRight}");
    const second = screen.getByRole("tab", { name: "Partecipanti" });
    expect(second).toHaveAttribute("aria-selected", "true");
    expect(second).toHaveFocus();
    await userEvent.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Novità" })).toHaveAttribute("aria-selected", "true");
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Organizzatori" })).toHaveFocus();
  });

  it("scrolls to the section named in the link", async () => {
    stub(adminMe);
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    renderGuide("/guida?scheda=organizzatori#giorni-e-slot");
    await screen.findByRole("heading", { name: "Giorni e slot", level: 2 });
    await waitFor(() => expect(scroll).toHaveBeenCalled());
  });
});

describe("links to the guide", () => {
  it("opens the section of the admin page you are on", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url === "/api/me"
          ? new Response(JSON.stringify(adminMe), { status: 200 })
          : new Response(JSON.stringify({ days: [], pending: [] }), { status: 200 }),
      ),
    );
    renderGuide("/admin/giorni");
    const link = await screen.findByRole("link", { name: "Guida" });
    expect(link).toHaveAttribute("href", "/guida?scheda=organizzatori#giorni-e-slot");
  });

  it("is reachable from the personal page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url === "/api/me"
          ? new Response(JSON.stringify(participantMe), { status: 200 })
          : new Response(JSON.stringify({ days: [] }), { status: 200 }),
      ),
    );
    renderGuide("/io");
    expect(await screen.findByRole("link", { name: "Come funziona: la guida" })).toHaveAttribute(
      "href",
      "/guida",
    );
  });
});
