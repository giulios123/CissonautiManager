import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { isInFrame } from "./frame";
import { SiteHeader } from "./SiteHeader";

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
    expect(screen.getByRole("img", { name: "Cissone" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Cissonauti Summer Camp/ })).toHaveAttribute(
      "href",
      "/",
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
    fireEvent.error(screen.getByRole("img", { name: "Cissone" }));
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
    expect(screen.getByRole("img", { name: "Cissone" })).toBeInTheDocument();
  });
});
