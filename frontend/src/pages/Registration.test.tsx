import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";

const edition = {
  registration_open: true,
  name: "Camp 2026",
  base_fee_cents: 1000,
  per_day_fee_cents: 100,
  hold_days: 3,
  days: [
    {
      date: "2026-07-13",
      slots: [
        {
          id: 1,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 25,
          available: 10,
        },
        {
          id: 2,
          period: "afternoon",
          start_time: "14:00:00",
          end_time: "18:00:00",
          capacity: 25,
          available: 0,
        },
        {
          id: 7,
          period: "evening",
          start_time: "19:00:00",
          end_time: "00:00:00",
          capacity: null,
          available: null,
        },
      ],
    },
    {
      date: "2026-07-14",
      slots: [
        {
          id: 3,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 25,
          available: 25,
        },
      ],
    },
  ],
  payment_channels: [],
  privacy: { version: 1, body: "Privacy" },
  disclaimer: { version: 1, body: "Scarico" },
};

function mockFetch(responses: Record<string, { status?: number; body: unknown }>) {
  const calls: { url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      const response = responses[url];
      return new Response(JSON.stringify(response.body), { status: response.status ?? 200 });
    }),
  );
  return calls;
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/iscrizione"]}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("Registration page", () => {
  it("tells people when registrations are closed", async () => {
    mockFetch({
      "/api/public/edition": { body: { registration_open: false, name: null, days: [] } },
    });
    renderPage();
    expect(await screen.findByText(/non sono ancora aperte/)).toBeInTheDocument();
  });

  it("shows the paragraph written by the organizers above the form", async () => {
    mockFetch({
      "/api/public/edition": {
        body: { ...edition, registration_intro: "Benvenuto!\nScegli i tuoi turni." },
      },
    });
    renderPage();
    const intro = await screen.findByText(/Benvenuto!/);
    expect(intro).toHaveTextContent("Benvenuto! Scegli i tuoi turni.");
    expect(intro).toHaveClass("intro-text");
  });

  it("disables full slots and updates the fee preview", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    expect(await screen.findByText(/Quota da versare/)).toHaveTextContent("10,00");
    expect(screen.getByLabelText(/Pomeriggio 14:00-18:00 · completo/)).toBeDisabled();

    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 25 posti liberi/));
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("12,00");
  });

  it("always allows the evening, with no seat limit", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    const evening = await screen.findByLabelText(/Sera 19:00-00:00 · senza limite di posti/);
    expect(evening).toBeEnabled();
    await user.click(evening);
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("11,00");
  });

  it("asks for at least one slot", async () => {
    const calls = mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Scegli almeno uno slot");
    expect(calls.filter((c) => c.url.includes("registrations"))).toHaveLength(0);
  });

  it("submits the registration and shows the payment summary", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "in_attesa_pagamento",
            amount_due_cents: 1100,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ label: "lun 13/07 mattina (09:00-13:00)" }],
            payment_channels: [{ code: "iban", label: "Bonifico (IBAN)", instructions: "IT00" }],
          },
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    expect(await screen.findByRole("heading", { name: "Iscrizione ricevuta" })).toBeInTheDocument();
    expect(screen.getByText("CSC-7K3P")).toBeInTheDocument();
    expect(screen.getByText("Bonifico (IBAN)")).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([1]);
    expect(sent.privacy_version).toBe(1);
    expect(sent.email).toBe("ada@example.com");
  });

  it("shows the server message when a slot became full", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 409,
        body: { detail: "Questi slot sono al completo: lun 13/07 mattina. Scegline altri." },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("al completo"));
  });
});

describe("waitlist in the registration form", () => {
  const withList = {
    ...edition,
    days: edition.days.map((day) => ({
      ...day,
      slots: day.slots.map((s) => (s.id === 2 ? { ...s, waitlist_free: 3 } : s)),
    })),
  };

  async function fillIn(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
  }

  it("lets people tick a full slot with a waitlist, and says there is nothing to pay", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: withList },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "waitlisted",
          personal_code: "CSC-7K3P",
          waitlist: [{ label: "lun 13/07 pomeriggio (14:00-18:00)", position: 1 }],
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    const full = await screen.findByLabelText(/Pomeriggio 14:00-18:00 · completo, spunta/);
    expect(full).toBeEnabled();
    await user.click(full);
    expect(screen.getByText(/Solo lista d'attesa/)).toBeInTheDocument();
    await fillIn(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(
      await screen.findByRole("heading", { name: "Sei in lista d'attesa" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/sei 1° in lista/)).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([]);
    expect(sent.waitlist_slot_ids).toEqual([2]);
  });

  it("books free slots and lists the full ones in the summary", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: withList },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "in_attesa_pagamento",
            amount_due_cents: 1100,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ label: "lun 13/07 mattina (09:00-13:00)" }],
            payment_channels: [],
          },
          waitlist: [{ label: "lun 13/07 pomeriggio (14:00-18:00)", position: 2 }],
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Pomeriggio 14:00-18:00 · completo, spunta/));
    // The waitlisted slot is not in the fee: only Monday morning is booked.
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("11,00");
    await fillIn(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(await screen.findByRole("heading", { name: "In lista d'attesa" })).toBeInTheDocument();
    expect(screen.getByText(/sei 2° in lista/)).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([1]);
    expect(sent.waitlist_slot_ids).toEqual([2]);
  });

  it("groups the chosen slots by day in the summary and lets you remove one", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Sera 19:00-00:00/));
    const summary = screen.getByRole("complementary", { name: "Il tuo riepilogo" });
    expect(within(summary).getAllByRole("listitem")).toHaveLength(1);
    expect(within(summary).getByText("2 turni · 1 giorno")).toBeInTheDocument();
    await user.click(within(summary).getByRole("button", { name: /^Togli .* · Mattina$/ }));
    expect(within(summary).getByText("1 turno · 1 giorno")).toBeInTheDocument();
  });

  it("keeps a full slot locked when its waitlist is full too", async () => {
    const fullList = {
      ...edition,
      days: edition.days.map((day) => ({
        ...day,
        slots: day.slots.map((s) => (s.id === 2 ? { ...s, waitlist_free: 0 } : s)),
      })),
    };
    mockFetch({ "/api/public/edition": { body: fullList } });
    renderPage();
    expect(
      await screen.findByLabelText(/Pomeriggio 14:00-18:00 · completo, anche la lista/),
    ).toBeDisabled();
  });
});
