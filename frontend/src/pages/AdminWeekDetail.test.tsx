import { render, screen, waitFor, within } from "@testing-library/react";
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

const day = (over: Record<string, unknown>) => ({
  date: "2026-07-13",
  morning: 0,
  afternoon: 0,
  evening: 0,
  evening_derived: 0,
  people: 0,
  lunches: 0,
  dinners: 0,
  activities: 0,
  ...over,
});

const row = (over: Record<string, unknown>) => ({
  date: "2026-07-13",
  booking_id: null,
  guest_id: null,
  external: false,
  name: "",
  status: null,
  derived: false,
  activity_id: null,
  activity_title: null,
  ...over,
});

function stub(week: unknown, detail: (url: URL) => { status: number; body: unknown }) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      const url = new URL(input, "http://localhost");
      calls.push(`${url.pathname}${url.search}`);
      if (url.pathname === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
      if (url.pathname === "/api/admin/views/week/detail") {
        const { status, body } = detail(url);
        return new Response(JSON.stringify(body), { status });
      }
      return new Response(JSON.stringify(week), { status: 200 });
    }),
  );
  return calls;
}

function renderWeek() {
  render(
    <MemoryRouter initialEntries={["/admin/week"]}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

const week = {
  days: [day({ morning: 1, lunches: 1, activities: 2, people: 1 }), day({ date: "2026-07-14" })],
  total_people: 1,
  total_lunches: 1,
  total_dinners: 0,
  total_activities: 2,
};

describe("week detail", () => {
  it("opens the list behind a number and gives the focus back on close", async () => {
    const calls = stub(week, () => ({
      status: 200,
      body: {
        metric: "lunch",
        date: "2026-07-13",
        count: 1,
        distinct_people: null,
        rows: [row({ name: "Anna Rossi", guest_id: 4, external: true })],
      },
    }));
    renderWeek();
    const button = await screen.findByRole("button", { name: /^Pranzi, .*13 luglio: 1/ });
    await userEvent.click(button);
    const dialog = await screen.findByRole("dialog", { name: /Pranzi · .*13 luglio/ });
    expect(await within(dialog).findByRole("link", { name: "Anna Rossi" })).toHaveAttribute(
      "href",
      "/admin/guests/4",
    );
    expect(within(dialog).getByText("(esterno)")).toBeInTheDocument();
    expect(calls).toContain("/api/admin/views/week/detail?metric=lunch&date=2026-07-13");
    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(button).toHaveFocus();
  });

  it("keeps Tab inside the dialog", async () => {
    stub(week, () => ({
      status: 200,
      body: { metric: "lunch", date: "2026-07-13", count: 1, distinct_people: null, rows: [] },
    }));
    renderWeek();
    await userEvent.click(await screen.findByRole("button", { name: /^Pranzi, .*13 luglio/ }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.tab();
    expect(dialog).toContainElement(document.activeElement as HTMLElement);
  });

  it("shows the sign-ups and the distinct people of the activities", async () => {
    stub(week, () => ({
      status: 200,
      body: {
        metric: "activities",
        date: null,
        count: 2,
        distinct_people: 1,
        rows: [
          row({
            name: "Ada Lovelace",
            booking_id: 7,
            status: "confermata",
            activity_title: "Yoga",
          }),
          row({
            date: "2026-07-14",
            name: "Ada Lovelace",
            booking_id: 7,
            status: "confermata",
            activity_title: "Escursione",
          }),
        ],
      },
    }));
    renderWeek();
    await userEvent.click(
      await screen.findByRole("button", { name: /^Attività, tutta la settimana/ }),
    );
    const dialog = await screen.findByRole("dialog", { name: /Attività · tutta la settimana/ });
    expect(await within(dialog).findByText("2 adesioni · 1 persone diverse")).toBeInTheDocument();
    expect(within(dialog).getAllByRole("link", { name: "Ada Lovelace" })).toHaveLength(2);
    expect(within(dialog).getByText(/Escursione/)).toBeInTheDocument();
  });

  it("says so when there is nobody", async () => {
    stub(week, () => ({
      status: 200,
      body: { metric: "morning", date: "2026-07-14", count: 0, distinct_people: null, rows: [] },
    }));
    renderWeek();
    const buttons = await screen.findAllByRole("button", { name: /^Mattina, .*14 luglio: 0/ });
    await userEvent.click(buttons[0]);
    expect(await screen.findByText("Nessuna persona per questo numero.")).toBeInTheDocument();
  });

  it("warns when the list no longer matches the cell and refreshes the table", async () => {
    const calls = stub(week, () => ({
      status: 200,
      body: {
        metric: "lunch",
        date: "2026-07-13",
        count: 3,
        distinct_people: null,
        rows: [],
      },
    }));
    renderWeek();
    await userEvent.click(await screen.findByRole("button", { name: /^Pranzi, .*13 luglio: 1/ }));
    expect(await screen.findByText(/cambiato da 1 a 3/)).toBeInTheDocument();
    await waitFor(() =>
      expect(calls.filter((c) => c === "/api/admin/views/week").length).toBeGreaterThan(1),
    );
  });

  it("shows an error with a way to retry", async () => {
    let attempts = 0;
    stub(week, () => {
      attempts += 1;
      return attempts === 1
        ? { status: 500, body: { detail: "x" } }
        : {
            status: 200,
            body: {
              metric: "lunch",
              date: "2026-07-13",
              count: 1,
              distinct_people: null,
              rows: [],
            },
          };
    });
    renderWeek();
    await userEvent.click(await screen.findByRole("button", { name: /^Pranzi, .*13 luglio/ }));
    expect(await screen.findByText("Non riesco a caricare l'elenco.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Riprova" }));
    expect(await screen.findByText("Totale: 1")).toBeInTheDocument();
  });
});
