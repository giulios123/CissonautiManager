import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { isInFrame } from "./frame";
import bundledLogoUrl from "./assets/logo-cissone.png";
import { EventNameProvider, useRefreshEventName } from "./eventName";
import { SiteHeader } from "./SiteHeader";

afterEach(() => vi.unstubAllGlobals());

function RefreshEdition() {
  const refresh = useRefreshEventName();
  return (
    <button type="button" onClick={refresh}>
      Refresh edition
    </button>
  );
}

function renderHeader(compact?: boolean) {
  return render(
    <MemoryRouter>
      <SiteHeader compact={compact} />
    </MemoryRouter>,
  );
}

describe("SiteHeader", () => {
  it("shows logo and name outside the iframe", () => {
    renderHeader(false);
    expect(screen.getByRole("img", { name: "Logo di Cissonauti Summer Camp" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Cissonauti Summer Camp/ })).toHaveAttribute(
      "href",
      "/me",
    );
  });

  it("shows only the name inside the iframe", () => {
    renderHeader(true);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("Cissonauti Summer Camp")).toBeInTheDocument();
  });

  it("falls back to the name when the logo cannot load", () => {
    renderHeader(false);
    fireEvent.error(screen.getByRole("img", { name: "Logo di Cissonauti Summer Camp" }));
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("Cissonauti Summer Camp")).toBeInTheDocument();
  });

  it("uses the full header when the page is not framed", () => {
    expect(isInFrame()).toBe(false);
    render(
      <MemoryRouter>
        <SiteHeader />
      </MemoryRouter>,
    );
    expect(screen.getByRole("img", { name: "Logo di Cissonauti Summer Camp" })).toBeInTheDocument();
  });

  it("uses the edition logo and falls back to the bundled logo if it fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ name: "Camp 2027", registration_open: false, logo_url: "/logo?v=1" }),
            { status: 200 },
          ),
      ),
    );
    render(
      <MemoryRouter>
        <EventNameProvider>
          <SiteHeader compact={false} />
        </EventNameProvider>
      </MemoryRouter>,
    );

    const image = await screen.findByRole("img", { name: "Logo di Camp 2027" });
    expect(image).toHaveAttribute("src", "/logo?v=1");
    fireEvent.error(image);
    expect(await screen.findByRole("img", { name: "Logo di Camp 2027" })).toHaveAttribute(
      "src",
      bundledLogoUrl,
    );
  });

  it("retries the same logo after it is restored and uploaded again", async () => {
    let logoUrl: string | null = "/api/public/edition/logo?v=failed";
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ name: "Camp 2027", registration_open: false, logo_url: logoUrl }),
            { status: 200 },
          ),
      ),
    );
    render(
      <MemoryRouter>
        <EventNameProvider>
          <SiteHeader compact={false} />
          <RefreshEdition />
        </EventNameProvider>
      </MemoryRouter>,
    );

    const image = await screen.findByRole("img", { name: "Logo di Camp 2027" });
    fireEvent.error(image);
    await waitFor(() =>
      expect(screen.getByRole("img", { name: "Logo di Camp 2027" })).toHaveAttribute(
        "src",
        bundledLogoUrl,
      ),
    );

    logoUrl = null;
    fireEvent.click(screen.getByRole("button", { name: "Refresh edition" }));
    await waitFor(() =>
      expect(screen.getByRole("img", { name: "Logo di Camp 2027" })).toHaveAttribute(
        "src",
        bundledLogoUrl,
      ),
    );

    logoUrl = "/api/public/edition/logo?v=failed";
    fireEvent.click(screen.getByRole("button", { name: "Refresh edition" }));
    await waitFor(() =>
      expect(screen.getByRole("img", { name: "Logo di Camp 2027" })).toHaveAttribute(
        "src",
        logoUrl,
      ),
    );
  });
});
