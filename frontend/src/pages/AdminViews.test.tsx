import { render, screen, within } from "@testing-library/react";
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

function stub(handler: (url: string) => unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(JSON.stringify(url === "/api/me" ? admin : handler(url)), { status: 200 }),
    ),
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

const person = (id: number, first: string, last: string, derived = false) => ({
  booking_id: id,
  first_name: first,
  last_name: last,
  status: "confermata",
  derived,
});

describe("days and slots view", () => {
  const slots = {
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
            present: 2,
            free: 23,
            people: [person(7, "Eve", "Adams"), person(8, "Ada", "Lovelace")],
          },
          {
            id: 3,
            period: "evening",
            start_time: "19:00:00",
            end_time: "00:00:00",
            capacity: null,
            present: 1,
            free: null,
            people: [person(8, "Ada", "Lovelace", true)],
          },
        ],
      },
    ],
  };

  it("shows presences, free seats and who is there, linking to each booking", async () => {
    stub(() => slots);
    renderAt("/admin/days");
    const table = await screen.findByRole("table", { name: /13 luglio/ });
    const morning = within(table).getByRole("row", { name: /Mattina/ });
    expect(within(morning).getByText("2 / 25")).toBeInTheDocument();
    expect(within(morning).getByText("23")).toBeInTheDocument();
    expect(within(morning).getByRole("link", { name: "Eve Adams" })).toHaveAttribute(
      "href",
      "/admin/registrations/7",
    );
  });

  it("marks the evening of the whole day as derived and the evening as unlimited", async () => {
    stub(() => slots);
    renderAt("/admin/days");
    const evening = within(await screen.findByRole("row", { name: /Sera/ }));
    expect(evening.getByText("senza limite")).toBeInTheDocument();
    expect(evening.getByText(/sera dell'intero giorno/)).toBeInTheDocument();
  });

  it("offers the CSV download", async () => {
    stub(() => slots);
    renderAt("/admin/days");
    expect(await screen.findByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/views/slots?format=csv",
    );
  });

  it("explains what to do when there are no days", async () => {
    stub(() => ({ days: [] }));
    renderAt("/admin/days");
    expect(await screen.findByText(/configura prima l'edizione/)).toBeInTheDocument();
  });
});

describe("week view", () => {
  const week = {
    days: [
      {
        date: "2026-07-13",
        morning: 2,
        afternoon: 1,
        evening: 2,
        evening_derived: 1,
        people: 3,
        lunches: 2,
        dinners: 1,
        activities: 4,
      },
      {
        date: "2026-07-14",
        morning: 0,
        afternoon: 0,
        evening: 0,
        evening_derived: 0,
        people: 0,
        lunches: 0,
        dinners: 0,
        activities: 0,
      },
    ],
    total_people: 3,
    total_lunches: 2,
    total_dinners: 1,
    total_activities: 4,
  };

  it("shows the counts per day, the derived evenings and the weekly total", async () => {
    stub(() => week);
    renderAt("/admin/settimana");
    const table = await screen.findByRole("table", { name: "Presenze per giorno" });
    const monday = within(within(table).getByRole("row", { name: /13 luglio/ }));
    expect(monday.getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "2",
      "1",
      "2 (di cui 1 per l'intero giorno)",
      "3",
      "2",
      "1",
      "4",
    ]);
    const tuesday = within(within(table).getByRole("row", { name: /14 luglio/ }));
    expect(tuesday.getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "0",
      "0",
      "0",
      "0",
      "0",
      "0",
      "0",
    ]);
    const total = within(within(table).getByRole("row", { name: /Persone diverse/ }));
    expect(total.getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "3",
      "2",
      "1",
      "4",
    ]);
  });

  it("offers the CSV download", async () => {
    stub(() => week);
    renderAt("/admin/settimana");
    expect(await screen.findByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/views/week?format=csv",
    );
  });
});

describe("payments to review", () => {
  const reviewRow = (over: Record<string, unknown>) => ({
    booking_id: 7,
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    personal_code: "CSC-7K3P",
    status: "confermata",
    amount_due_cents: 1100,
    paid_cents: 1200,
    balance_cents: -100,
    reason: "credito",
    reason_label: "Confermata con un credito (ha versato in più)",
    ...over,
  });

  it("lists each case with its reason and amounts, linking to the booking", async () => {
    stub(() => [
      reviewRow({}),
      reviewRow({
        booking_id: 8,
        first_name: "Bob",
        last_name: "Builder",
        reason: "disdetta_da_rimborsare",
        reason_label: "Disdetta richiesta: da rimborsare",
        status: "disdetta_richiesta",
        balance_cents: 0,
      }),
    ]);
    renderAt("/admin/to-review");
    const table = await screen.findByRole("table", { name: "Iscrizioni da verificare" });
    const ada = within(within(table).getByRole("row", { name: /Ada Lovelace/ }));
    expect(ada.getByText(/ha versato in più/)).toBeInTheDocument();
    expect(ada.getByText(/-1,00/)).toBeInTheDocument();
    expect(ada.getByRole("link", { name: /Ada Lovelace/ })).toHaveAttribute(
      "href",
      "/admin/registrations/7",
    );
    expect(screen.getByText("Disdetta richiesta: da rimborsare")).toBeInTheDocument();
    expect(screen.getByText("2 da verificare")).toBeInTheDocument();
  });

  it("offers the CSV download", async () => {
    stub(() => [reviewRow({})]);
    renderAt("/admin/to-review");
    expect(await screen.findByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/views/payments-review?format=csv",
    );
  });

  it("says so when everything is in order", async () => {
    stub(() => []);
    renderAt("/admin/to-review");
    expect(await screen.findByText(/Tutto in ordine/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Scarica CSV" })).not.toBeInTheDocument();
  });
});
