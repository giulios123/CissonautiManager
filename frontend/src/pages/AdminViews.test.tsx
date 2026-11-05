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
    renderAt("/admin/giorni");
    const table = await screen.findByRole("table", { name: /13 luglio/ });
    const morning = within(table).getByRole("row", { name: /Mattina/ });
    expect(within(morning).getByText("2 / 25")).toBeInTheDocument();
    expect(within(morning).getByText("23")).toBeInTheDocument();
    expect(within(morning).getByRole("link", { name: "Eve Adams" })).toHaveAttribute(
      "href",
      "/admin/iscrizioni/7",
    );
  });

  it("marks the evening of the whole day as derived and the evening as unlimited", async () => {
    stub(() => slots);
    renderAt("/admin/giorni");
    const evening = within(await screen.findByRole("row", { name: /Sera/ }));
    expect(evening.getByText("senza limite")).toBeInTheDocument();
    expect(evening.getByText(/sera dell'intero giorno/)).toBeInTheDocument();
  });

  it("offers the CSV download", async () => {
    stub(() => slots);
    renderAt("/admin/giorni");
    expect(await screen.findByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/views/slots?format=csv",
    );
  });

  it("explains what to do when there are no days", async () => {
    stub(() => ({ days: [] }));
    renderAt("/admin/giorni");
    expect(await screen.findByText(/configura prima l'edizione/)).toBeInTheDocument();
  });
});
