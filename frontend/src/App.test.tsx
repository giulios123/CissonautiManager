import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "./App";

describe("App routing", () => {
  it("shows the home page", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Cisonauti Summer Camp" })).toBeInTheDocument();
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
