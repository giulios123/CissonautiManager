import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { I18nProvider } from "../i18n";
import { adminMe } from "../test-utils";

type Reply = { status?: number; body: unknown };

function stub(handler: (url: string) => Reply | undefined) {
  const calls: { url: string; language?: string }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const headers = (init?.headers ?? {}) as Record<string, string>;
      calls.push({ url, language: headers["Accept-Language"] });
      if (url === "/api/me") return new Response(JSON.stringify(adminMe), { status: 200 });
      const { status = 200, body } = handler(url) ?? { status: 404, body: {} };
      return new Response(JSON.stringify(body), { status });
    }),
  );
  return calls;
}

function renderEnglish(path: string) {
  render(
    <I18nProvider locale="en">
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </I18nProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

const row = {
  id: 7,
  first_name: "Ada",
  last_name: "Lovelace",
  email: "ada@example.com",
  phone: null,
  personal_code: "CSC-0001",
  days: 2,
  evenings: 1,
  status: "in_attesa_pagamento",
  amount_due_cents: 1100,
  paid_cents: 0,
  balance_cents: 1100,
  hold_expires_at: "2026-07-20T10:00:00Z",
};

describe("the admin panel in English", () => {
  it("shows the menu and the people list in English", async () => {
    stub((url) => (url.startsWith("/api/admin/registrations") ? { body: [row] } : undefined));
    renderEnglish("/admin");
    const nav = await screen.findByRole("navigation", { name: "Organizers' panel" });
    for (const name of ["People", "Days and slots", "Week", "To collect", "To review", "Settings"])
      expect(within(nav).getByRole("link", { name })).toBeInTheDocument();
    expect(within(nav).getByRole("button", { name: "Sign out" })).toBeInTheDocument();
    expect(await screen.findByText("1 registration")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Balance" })).toBeInTheDocument();
    expect(screen.getByText("Awaiting payment", { selector: "span.status" })).toBeInTheDocument();
    expect(screen.getAllByText("€11.00", { selector: "td" })).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Ada Lovelace" })).toHaveAttribute(
      "href",
      "/admin/registrations/7",
    );
    expect(document.title).toBe("People · Cissonauti Summer Camp");
  });

  it("asks for the CSV in the language of the page", async () => {
    stub((url) => (url.startsWith("/api/admin/registrations") ? { body: [row] } : undefined));
    renderEnglish("/admin");
    const link = await screen.findByRole("link", { name: "Download CSV" });
    expect(link).toHaveAttribute("href", "/api/admin/registrations?format=csv&lang=en");
  });

  it("starts over, asking the server again, when the language changes", async () => {
    const calls = stub((url) =>
      url.startsWith("/api/admin/registrations") ? { body: [row] } : undefined,
    );
    renderEnglish("/admin");
    await screen.findByText("1 registration");
    const before = calls.filter((c) => c.url.startsWith("/api/admin/registrations")).length;
    await userEvent.setup().click(screen.getByRole("button", { name: "Italian" }));
    expect(await screen.findByText("1 iscrizione")).toBeInTheDocument();
    await waitFor(() =>
      expect(calls.filter((c) => c.url.startsWith("/api/admin/registrations")).length).toBe(
        before + 1,
      ),
    );
    expect(calls.at(-1)?.language).toBe("it");
  });

  it("shows the to-collect page in English", async () => {
    stub((url) => (url === "/api/admin/views/to-collect" ? { body: [] } : undefined));
    renderEnglish("/admin/to-collect");
    expect(await screen.findByRole("heading", { name: "To collect" })).toBeInTheDocument();
    expect(await screen.findByText("No payments to collect.")).toBeInTheDocument();
    expect(screen.getByLabelText("Channel of the payments you mark")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Bank transfer (IBAN)" })).toBeInTheDocument();
  });

  it("opens the Italian address of a page in English", async () => {
    stub((url) => (url === "/api/admin/views/to-review" ? { body: [] } : undefined));
    renderEnglish("/admin/da-verificare");
    expect(await screen.findByRole("heading", { name: "Payments to review" })).toBeInTheDocument();
  });

  it("shows the settings page in English", async () => {
    stub((url) => {
      if (url === "/api/admin/edition")
        return {
          body: {
            id: 1,
            name: "Camp 2026",
            start_date: "2026-07-13",
            end_date: "2026-07-17",
            morning_start: "09:00:00",
            morning_end: "13:00:00",
            afternoon_start: "14:00:00",
            afternoon_end: "18:00:00",
            evening_start: "19:00:00",
            evening_end: "00:00:00",
            default_capacity: 25,
            hold_days: 3,
            waitlist_percent: 20,
            base_fee_cents: 1000,
            per_day_fee_cents: 100,
            lunch_price_cents: 800,
            dinner_price_cents: 1200,
            slots: [],
            logo_url: null,
            payment_channels: [],
            privacy: null,
            disclaimer: null,
          },
        };
      if (url === "/api/admin/edition/confirmation-policy/preview")
        return {
          body: {
            current_policy: "legacy_total",
            proposed_policy: "registration_fee",
            ready: true,
            already_active: false,
            preview_token: "a".repeat(64),
            eligible_count: 0,
            excluded_expired_count: 0,
            excluded_closed_count: 0,
            waitlist_only_count: 0,
            new_confirmation_count: 0,
            email_templates_to_review: [],
            blockers: [],
            rows: [],
          },
        };
      return undefined;
    });
    renderEnglish("/admin/settings");
    expect(await screen.findByRole("heading", { name: "Settings", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save edition" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Booking confirmation rule" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Calculate preview" }));
    expect(
      await screen.findByText(
        "The recalculation uses current prices. Payments and voids stay unchanged; the balance or credit may change. Only active bookings are recalculated.",
      ),
    ).toBeInTheDocument();
  });
});
