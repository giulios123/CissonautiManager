import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";

const admin = {
  id: 1,
  first_name: "Boss",
  last_name: "",
  email: "boss@example.com",
  role: "admin",
  personal_code: "CSC-0001",
  has_password: true,
  bookings: [],
  payment_channels: [],
};
const row = {
  id: 7,
  first_name: "Ada",
  last_name: "Lovelace",
  email: "ada@example.com",
  phone: "+39 333 1234567",
  personal_code: "CSC-7K3P",
  days: 2,
  evenings: 1,
  status: "in_attesa_pagamento",
  amount_due_cents: 1200,
  paid_cents: 0,
  balance_cents: 1200,
  hold_expires_at: "2026-07-04T10:00:00Z",
};
const detail = (status: string, paid: number) => ({
  participant: {
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    phone: null,
    invited_by: "Grace",
    can_bring: "Un talk",
    personal_code: "CSC-7K3P",
  },
  booking: {
    id: 7,
    status,
    amount_due_cents: 1200,
    paid_cents: paid,
    balance_cents: 1200 - paid,
    hold_expires_at: "2026-07-04T10:00:00Z",
    slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina (09:00-13:00)" }],
    payments: paid
      ? [{ amount_cents: paid, channel: "iban", paid_on: "2026-07-02", note: "via Anna" }]
      : [],
  },
  privacy: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
  disclaimer: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
  warning: null,
});

function stub(
  handler: (method: string, url: string, body?: unknown) => { status?: number; body: unknown },
) {
  const calls: { method: string; url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ method, url, body });
      const { status = 200, body: payload } = handler(method, url, body);
      return new Response(JSON.stringify(payload), { status });
    }),
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("admin area", () => {
  it("sends anonymous visitors to the login page", async () => {
    stub(() => ({ status: 401, body: { detail: "Not authenticated" } }));
    renderAt("/admin");
    expect(await screen.findByRole("heading", { name: "Accedi" })).toBeInTheDocument();
  });

  it("keeps participants out", async () => {
    stub(() => ({ body: { ...admin, role: "participant" } }));
    renderAt("/admin");
    expect(await screen.findByRole("heading", { name: "Accesso riservato" })).toBeInTheDocument();
  });

  it("lists registrations with amounts and status", async () => {
    stub((_m, url) => ({ body: url === "/api/me" ? admin : [row] }));
    renderAt("/admin");
    const cell = await screen.findByRole("link", { name: /Ada Lovelace/ });
    const tableRow = cell.closest("tr")!;
    expect(within(tableRow).getByText("In attesa di pagamento")).toBeInTheDocument();
    expect(within(tableRow).getAllByText(/12,00/)).toHaveLength(2);
  });

  it("shows phone and evenings and offers the CSV with the same filters", async () => {
    stub((_m, url) => ({ body: url === "/api/me" ? admin : [row] }));
    renderAt("/admin");
    const cell = await screen.findByRole("link", { name: /Ada Lovelace/ });
    const tableRow = cell.closest("tr")!;
    expect(within(tableRow).getByText("+39 333 1234567")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Sere" })).toBeInTheDocument();
    const csv = screen.getByRole("link", { name: "Scarica CSV" });
    expect(csv).toHaveAttribute("href", "/api/admin/registrations?format=csv");
    await userEvent.type(screen.getByLabelText(/Cerca/), "ada");
    expect(screen.getByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/registrations?q=ada&format=csv",
    );
  });

  it("filters the list by search text", async () => {
    const calls = stub((_m, url) => ({ body: url === "/api/me" ? admin : [row] }));
    renderAt("/admin");
    await screen.findByRole("link", { name: /Ada Lovelace/ });
    await userEvent.type(screen.getByLabelText(/Cerca/), "ada");
    expect(calls.some((c) => c.url.includes("q=ada"))).toBe(true);
  });

  it("registers a payment from the detail page", async () => {
    const calls = stub((method, url) => {
      if (url === "/api/me") return { body: admin };
      if (method === "POST") return { status: 201, body: detail("confermata", 1200) };
      return { body: detail("in_attesa_pagamento", 0) };
    });
    renderAt("/admin/iscrizioni/7");
    const user = userEvent.setup();
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    await user.click(screen.getByRole("button", { name: /Metti il saldo/ }));
    expect(screen.getByLabelText("Importo (€)")).toHaveValue("12,00");
    await user.click(screen.getByRole("button", { name: "Registra pagamento" }));

    expect(await screen.findByRole("status")).toHaveTextContent("confermata");
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe("/api/admin/registrations/7/payments");
    expect(post.body).toMatchObject({ amount_cents: 1200, channel: "iban", paid_on: null });
    expect(screen.getByRole("heading", { name: /Confermata/ })).toBeInTheDocument();
  });

  it("rejects an invalid amount without calling the server", async () => {
    const calls = stub((_m, url) => ({
      body: url === "/api/me" ? admin : detail("in_attesa_pagamento", 0),
    }));
    renderAt("/admin/iscrizioni/7");
    const user = userEvent.setup();
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    await user.type(screen.getByLabelText("Importo (€)"), "abc");
    await user.click(screen.getByRole("button", { name: "Registra pagamento" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("importo valido");
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });
});
