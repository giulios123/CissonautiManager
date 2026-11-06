import { render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { App } from "./App";

function Where() {
  const { pathname, search, hash } = useLocation();
  return <output data-testid="where">{`${pathname}${search}${hash}`}</output>;
}

describe("App routing", () => {
  it.each([
    ["/iscrizione", "/register"],
    ["/accedi", "/login"],
    ["/accedi/verifica?token=abc", "/login/verify?token=abc"],
    ["/io", "/me"],
    ["/guida?scheda=organizzatori#giorni-e-slot", "/guide?tab=organizers#days-and-slots"],
    ["/guida#iscriversi", "/guide#signing-up"],
    ["/io#giorni-e-slot", "/me#giorni-e-slot"],
    ["/admin/giorni", "/admin/days"],
    ["/admin/registrations/12", "/admin/registrations/12"],
  ])("sends the Italian address %s to %s", (from, to) => {
    render(
      <MemoryRouter initialEntries={[from]}>
        <App />
        <Where />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("where")).toHaveTextContent(to);
  });

  it("shows the home page", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Cissonauti Summer Camp" })).toBeInTheDocument();
  });

  it("sets a different title on each page", () => {
    render(
      <MemoryRouter initialEntries={["/register"]}>
        <App />
      </MemoryRouter>,
    );
    expect(document.title).toBe("Iscrizione · Cissonauti Summer Camp");
  });

  it("shows a not found page for unknown routes", () => {
    render(
      <MemoryRouter initialEntries={["/non-esiste"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Pagina non trovata" })).toBeInTheDocument();
  });
});
