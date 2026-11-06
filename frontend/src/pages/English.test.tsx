import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { I18nProvider } from "../i18n";
import { translate, translatePlural } from "../i18n/messages";

const slot = (id: number, period: string, available: number | null) => ({
  id,
  period,
  start_time: period === "morning" ? "09:00:00" : "14:00:00",
  end_time: period === "morning" ? "13:00:00" : "18:00:00",
  capacity: available === null ? null : 25,
  available,
});

const edition = {
  registration_open: true,
  name: "Camp 2026",
  base_fee_cents: 1000,
  per_day_fee_cents: 100,
  hold_days: 3,
  days: [{ date: "2026-07-13", slots: [slot(1, "morning", 10), slot(2, "afternoon", 0)] }],
  payment_channels: [],
  privacy: { version: 1, body: "Privacy" },
  disclaimer: { version: 1, body: "Waiver" },
};

const me = {
  id: 1,
  first_name: "Ada",
  last_name: "Lovelace",
  email: "ada@example.com",
  role: "participant",
  personal_code: "CSC-0001",
  has_password: false,
  locale: "en",
  payment_channels: [{ code: "iban", label: "Bank transfer", instructions: "IT00" }],
  bookings: [
    {
      id: 7,
      status: "in_attesa_pagamento",
      amount_due_cents: 1100,
      paid_cents: 0,
      balance_cents: 1100,
      hold_expires_at: "2026-07-20T10:00:00Z",
      editable: true,
      can_cancel: true,
      slots: [{ id: 1, date: "2026-07-13", period: "morning", label: "Mon 13 Jul morning" }],
      payments: [],
    },
  ],
};

type Handler = (url: string, init?: RequestInit) => { status?: number; body: unknown };

function stub(handler: Handler) {
  const calls: { method: string; url: string; body?: unknown; language?: string }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const headers = (init?.headers ?? {}) as Record<string, string>;
      calls.push({
        method: init?.method ?? "GET",
        url,
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
        language: headers["Accept-Language"],
      });
      const { status = 200, body } = handler(url, init);
      return new Response(status === 204 ? null : JSON.stringify(body), { status });
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

describe("the app in English", () => {
  it("shows the registration form in English and sends the language", async () => {
    const calls = stub((url) => ({ body: url === "/api/public/edition" ? edition : {} }));
    renderEnglish("/register");
    expect(await screen.findByText("Amount to pay:")).toHaveTextContent("€10.00");
    expect(screen.getByRole("heading", { name: "When you're coming" })).toBeInTheDocument();
    expect(screen.getByLabelText("First name")).toBeInTheDocument();
    expect(screen.getByLabelText(/Morning 09:00-13:00 · 10 places left/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Afternoon 14:00-18:00 · full/)).toBeDisabled();
    expect(screen.getByText("Your place is held for 3 days")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign up" })).toBeInTheDocument();
    expect(calls[0].language).toBe("en");
    expect(document.title).toBe("Registration · Camp 2026");
  });

  it("counts shifts and days with the right plural", async () => {
    stub(() => ({ body: edition }));
    renderEnglish("/register");
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText(/Morning 09:00-13:00/));
    expect(screen.getByText("1 shift · 1 day")).toBeInTheDocument();
  });

  it("sends the language with the registration", async () => {
    const calls = stub((url) => ({ body: url === "/api/public/edition" ? edition : {} }));
    renderEnglish("/register");
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText(/Morning 09:00-13:00/));
    await user.type(screen.getByLabelText("First name"), "Ada");
    await user.type(screen.getByLabelText("Last name"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("What can you bring to the camp?"), "A talk");
    await user.click(screen.getByLabelText("I have read and accept the privacy notice"));
    await user.click(screen.getByLabelText("I have read and accept the liability waiver"));
    await user.click(screen.getByRole("button", { name: "Sign up" }));
    await waitFor(() =>
      expect(calls.find((c) => c.url === "/api/public/registrations")?.body).toMatchObject({
        locale: "en",
        slot_ids: [1],
      }),
    );
  });

  it("shows the sign-in page in English", async () => {
    stub(() => ({ body: {} }));
    renderEnglish("/login");
    expect(await screen.findByRole("heading", { name: "Sign in", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send the link" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Or sign in with your password" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign up for the camp" })).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("shows the personal page in English", async () => {
    stub((url) => ({ body: url === "/api/me" ? me : edition }));
    renderEnglish("/me");
    expect(await screen.findByRole("heading", { name: "Hi Ada!" })).toBeInTheDocument();
    expect(screen.getByText("Awaiting payment")).toBeInTheDocument();
    expect(screen.getByText(/Fee:/)).toBeInTheDocument();
    expect(screen.getByText(/Still to pay:/)).toBeInTheDocument();
    expect(screen.getAllByText("€11.00", { selector: "strong" })).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Request cancellation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Choose lunches and dinners" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "How it works: the guide" })).toHaveAttribute(
      "href",
      "/guide",
    );
    expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
  });

  it("asks the server again when the language is switched, so its labels follow", async () => {
    const calls = stub((url) => ({ body: url === "/api/me" ? me : edition }));
    renderEnglish("/me");
    const user = userEvent.setup();
    await screen.findByRole("heading", { name: "Hi Ada!" });
    const before = calls.filter((c) => c.url === "/api/me").length;
    await user.click(screen.getByRole("button", { name: "Italian" }));
    expect(await screen.findByRole("heading", { name: "Ciao Ada!" })).toBeInTheDocument();
    await waitFor(() => expect(calls.filter((c) => c.url === "/api/me").length).toBe(before + 1));
    expect(calls.filter((c) => c.url === "/api/me").at(-1)?.language).toBe("it");
  });

  it("opens the cancellation dialog in English", async () => {
    stub((url) => ({ body: url === "/api/me" ? me : edition }));
    renderEnglish("/me");
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Request cancellation" }));
    expect(
      screen.getByRole("dialog", { name: "Do you want to cancel your registration?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "No, go back" })).toHaveFocus();
    expect(screen.getByRole("button", { name: "Yes, cancel" })).toBeInTheDocument();
  });

  it("shows the not found page in English", () => {
    stub(() => ({ body: {} }));
    renderEnglish("/nowhere");
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });
});

describe("message helpers", () => {
  it("fills placeholders and keeps unknown ones", () => {
    expect(translate("en", "me.hello", { name: "Ada" })).toBe("Hi Ada!");
    expect(translate("it", "me.hello", { name: "Ada" })).toBe("Ciao Ada!");
    expect(translate("en", "me.hello", {})).toBe("Hi {name}!");
  });

  it("picks the plural form of each language", () => {
    expect(translatePlural("it", "reg.shifts", 1)).toBe("1 turno");
    expect(translatePlural("it", "reg.shifts", 3)).toBe("3 turni");
    expect(translatePlural("en", "reg.shifts", 1)).toBe("1 shift");
    expect(translatePlural("en", "reg.shifts", 0)).toBe("0 shifts");
    expect(translatePlural("en", "seats.free", 1)).toBe("1 place left");
  });
});
