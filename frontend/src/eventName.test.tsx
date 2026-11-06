import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "./App";

function stubEdition(name: string | null, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url === "/api/public/edition" && status === 200)
        return new Response(JSON.stringify({ registration_open: false, name }), { status });
      return new Response("{}", { status: status === 200 ? 404 : status });
    }),
  );
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("event name", () => {
  it("shows the name of the edition in header, home and tab title", async () => {
    stubEdition("Camp d'autunno 2026");
    renderAt("/");
    expect(await screen.findByRole("heading", { name: "Camp d'autunno 2026" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Camp d'autunno 2026/ })).toBeInTheDocument();
    expect(document.title).toBe("Camp d'autunno 2026");
  });

  it("puts the name after the page in the tab title", async () => {
    stubEdition("Camp d'autunno 2026");
    renderAt("/register");
    await vi.waitFor(() => expect(document.title).toMatch(/ · Camp d'autunno 2026$/));
  });

  it("keeps the default name when there is no edition", async () => {
    stubEdition(null);
    renderAt("/");
    expect(
      await screen.findByRole("heading", { name: "Cissonauti Summer Camp" }),
    ).toBeInTheDocument();
  });

  it("keeps the default name when the server is unreachable", async () => {
    stubEdition(null, 500);
    renderAt("/");
    expect(
      await screen.findByRole("heading", { name: "Cissonauti Summer Camp" }),
    ).toBeInTheDocument();
  });
});
