import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";

function stubFetch(
  handler: (url: string, init?: RequestInit) => { status?: number; body: unknown },
) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push(`${init?.method ?? "GET"} ${url}`);
      const { status = 200, body } = handler(url, init);
      return new Response(status === 204 ? null : JSON.stringify(body), { status });
    }),
  );
  return calls;
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("magic link verification page", () => {
  const ada = {
    id: 1,
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    role: "participant",
    personal_code: "CSC-7K3P",
    has_password: false,
    payment_channels: [],
    bookings: [],
  };

  it("signs in as soon as the page opens, without a button", async () => {
    const calls = stubFetch((url) => ({
      body: url === "/api/auth/verify" ? { role: "participant", redirect: "/io" } : ada,
    }));
    renderAt("/accedi/verifica?token=abc");
    expect(screen.queryByRole("button", { name: "Entra" })).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Ciao Ada!" })).toBeInTheDocument();
    expect(calls.filter((call) => call === "POST /api/auth/verify")).toHaveLength(1);
  });

  it("shows an error and a way to ask for a new link when the token is rejected", async () => {
    stubFetch(() => ({ status: 400, body: { detail: "Link non valido o scaduto" } }));
    renderAt("/accedi/verifica?token=abc");
    expect(await screen.findByRole("alert")).toHaveTextContent("Link non valido o scaduto");
    expect(screen.getByRole("link", { name: "Richiedi un nuovo link" })).toBeInTheDocument();
  });

  it("explains when there is no token at all, without calling the server", () => {
    const calls = stubFetch(() => ({ body: {} }));
    renderAt("/accedi/verifica");
    expect(screen.getByRole("heading", { name: "Link non valido" })).toBeInTheDocument();
    expect(calls.filter((call) => call.includes("/api/auth/verify"))).toHaveLength(0);
  });
});

describe("login page", () => {
  it("shows the neutral message after requesting a link", async () => {
    stubFetch(() => ({ body: { message: "Se l'email è registrata riceverai un link." } }));
    renderAt("/accedi");
    const user = userEvent.setup();
    await user.type(screen.getAllByLabelText("Email")[0], "ada@example.com");
    await user.click(screen.getByRole("button", { name: "Invia il link" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Se l'email è registrata");
  });

  it("shows the generic error for wrong credentials", async () => {
    stubFetch(() => ({ status: 401, body: { detail: "Email o password non corretti" } }));
    renderAt("/accedi");
    const user = userEvent.setup();
    await user.type(screen.getAllByLabelText("Email")[1], "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong password");
    await user.click(screen.getByRole("button", { name: "Entra" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Email o password non corretti");
  });
});

describe("personal page", () => {
  const me = {
    id: 1,
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    role: "participant",
    personal_code: "CSC-7K3P",
    has_password: false,
    payment_channels: [{ code: "iban", label: "Bonifico (IBAN)", instructions: "IT00 0000" }],
    bookings: [
      {
        id: 5,
        status: "in_attesa_pagamento",
        amount_due_cents: 1200,
        paid_cents: 500,
        balance_cents: 700,
        hold_expires_at: "2026-07-04T10:00:00Z",
        slots: [
          { date: "2026-07-13", period: "morning", label: "lun 13/07 mattina (09:00-13:00)" },
        ],
        payments: [],
      },
    ],
  };

  it("redirects to login without a session", async () => {
    stubFetch(() => ({ status: 401, body: { detail: "Not authenticated" } }));
    renderAt("/io");
    expect(await screen.findByRole("heading", { name: "Accedi" })).toBeInTheDocument();
  });

  it("shows balance, deadline, reference code and payment instructions", async () => {
    stubFetch(() => ({ body: me }));
    renderAt("/io");
    expect(await screen.findByRole("heading", { name: "Ciao Ada!" })).toBeInTheDocument();
    expect(screen.getByText("lun 13/07 mattina (09:00-13:00)")).toBeInTheDocument();
    expect(screen.getByText(/Ancora da versare/).parentElement).toHaveTextContent("7,00");
    expect(screen.getByText("CSC-7K3P")).toBeInTheDocument();
    expect(screen.getByText("IT00 0000")).toBeInTheDocument();
    expect(screen.getByText(/12:00/)).toBeInTheDocument();
  });
});
