import { screen, within } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const split = (confirmed: number, pending: number, external = 0) => ({
  confirmed,
  pending,
  external,
  total: confirmed + pending + external,
});

const report = {
  edition: { name: "Camp 2026", start_date: "2026-07-13", end_date: "2026-07-14" },
  enrollment: {
    by_status: {
      confermata: 2,
      in_attesa_pagamento: 1,
      scaduta: 1,
      disdetta_richiesta: 0,
      rimborsata: 1,
    },
    people_with_seat: 3,
  },
  presence: {
    slots: [
      { day: "2026-07-13", period: "morning", present: split(1, 1), derived: 0 },
      { day: "2026-07-13", period: "evening", present: split(1, 0), derived: 1 },
    ],
    peak: 2,
    average_per_daytime_slot: 1.5,
    person_days: split(2, 1),
  },
  meals: {
    days: [{ day: "2026-07-13", lunches: split(1, 1), dinners: split(1, 0) }],
    lunches: split(1, 1),
    dinners: split(1, 0),
    lunch_diets: { omnivore: 0, vegetarian: 1, vegan: 0, none: 1 },
    dinner_diets: { omnivore: 0, vegetarian: 1, vegan: 0, none: 0 },
    people_with_allergies: 1,
  },
  activities: [
    {
      id: 1,
      title: "Trekking",
      day: "2026-07-13",
      period: "morning",
      price_cents: 1500,
      capacity: 10,
      joined: split(1, 0),
      expected_cents: 1500,
    },
  ],
  contributions: { talk: 1, topic: 0, skill: 2 },
  waitlist: {
    waiting: 1,
    promoted: 2,
    promoted_plus_one: 1,
    left: 0,
    removed: 0,
    cancelled: 0,
    booked: 0,
  },
  revenue: {
    due_cents: 7600,
    due_fee_cents: 3300,
    due_meals_cents: 2800,
    due_activities_cents: 1500,
    due_difference_cents: 0,
    paid_cents: 5400,
    paid_by_channel: { iban: 4900, satispay: 500 },
    refunded_cents: 1100,
    net_cents: 4300,
    to_collect_cents: 1400,
    to_confirm_cents: 700,
    credits_cents: 400,
    to_refund_cents: 0,
    external_due_cents: 0,
    external_paid_cents: 0,
    external_refunded_cents: 0,
    external_net_cents: 0,
    external_to_collect_cents: 0,
    external_credit_cents: 0,
    event_net_cents: 6500,
  },
};

function serve(body: unknown) {
  return stubAdminApi((call) => (call.url === "/api/admin/views/report" ? { body } : undefined));
}

describe("report page", () => {
  it("counts external guests in meals and activities, apart from the bookings", async () => {
    serve({
      ...report,
      meals: {
        ...report.meals,
        days: [{ day: "2026-07-13", lunches: split(1, 1, 2), dinners: split(1, 0) }],
      },
      activities: [{ ...report.activities[0], joined: split(1, 0, 3) }],
    });
    renderAt("/admin/report");
    const meals = await screen.findByRole("table", { name: "Pranzi e cene per giorno" });
    expect(within(meals).getByRole("columnheader", { name: "Di cui esterni" })).toBeInTheDocument();
    const lunch = within(meals)
      .getByText(/, pranzo/)
      .closest("tr") as HTMLElement;
    // Confirmed, pending, total (guests included) and the guests apart.
    expect(
      within(lunch)
        .getAllByRole("cell")
        .map((c) => c.textContent),
    ).toEqual(["1", "1", "4", "2"]);
    const trekking = within(screen.getByRole("table", { name: /Adesioni e incasso/ }))
      .getByText("Trekking")
      .closest("tr") as HTMLElement;
    expect(within(trekking).getAllByRole("cell")[5]).toHaveTextContent("3");
  });

  it("shows every section with its numbers", async () => {
    serve(report);
    renderAt("/admin/report");
    await screen.findByRole("heading", { name: "Iscrizioni", level: 2 });
    expect(screen.getByRole("heading", { name: "Report", level: 1 })).toBeInTheDocument();
    for (const name of [
      "Iscrizioni",
      "Presenze",
      "Pasti",
      "Attività",
      "Contributi",
      "Lista d'attesa",
      "Incassi",
    ]) {
      expect(screen.getByRole("heading", { name, level: 2 })).toBeInTheDocument();
    }
    expect(document.title).toBe("Report · Cissonauti Summer Camp");

    const presence = screen.getByRole("table", { name: "Presenti per giorno e slot" });
    const morning = within(presence)
      .getByText(/mattina/)
      .closest("tr") as HTMLElement;
    expect(
      within(morning)
        .getAllByRole("cell")
        .map((c) => c.textContent),
    ).toEqual(["1", "1", "2"]);
    expect(within(presence).getByText(/di cui 1 per l'intero giorno/)).toBeInTheDocument();
    expect(screen.getByText("1,5")).toBeInTheDocument();

    const trekking = screen.getByRole("table", { name: /Adesioni e incasso/ });
    expect(
      within(trekking).getByText("15,00 €", { selector: "td:nth-child(2)" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Persone con allergie o intolleranze/)).toHaveTextContent("1");
  });

  it("writes the money in euros, split by channel", async () => {
    serve(report);
    renderAt("/admin/report");
    const money = await screen.findByRole("table", { name: /Quanto è dovuto/ });
    const row = (label: string) => within(money).getByText(label).closest("tr") as HTMLElement;
    expect(within(row("Totale dovuto")).getByText("76,00 €")).toBeInTheDocument();
    expect(within(row("Ancora da incassare")).getByText("14,00 €")).toBeInTheDocument();
    expect(within(row("Residuo per confermare")).getByText("7,00 €")).toBeInTheDocument();
    expect(within(row("Bonifico (IBAN)")).getByText("49,00 €")).toBeInTheDocument();
    expect(within(row("Netto (versato meno rimborsato)")).getByText("43,00 €")).toBeInTheDocument();
    expect(within(money).queryByText(/differenza di prezzi/)).not.toBeInTheDocument();
  });

  it("shows the price difference only when there is one", async () => {
    serve({ ...report, revenue: { ...report.revenue, due_difference_cents: -200 } });
    renderAt("/admin/report");
    expect(await screen.findByText(/differenza di prezzi cambiati/)).toBeInTheDocument();
  });

  it("offers the CSV download", async () => {
    serve(report);
    renderAt("/admin/report");
    const csv = await screen.findByRole("link", { name: "Scarica CSV" });
    expect(csv).toHaveAttribute("href", "/api/admin/views/report?format=csv&lang=it");
  });

  it("shows empty sections as zero, not as an error", async () => {
    serve({
      ...report,
      activities: [],
      presence: { ...report.presence, slots: [], peak: 0, average_per_daytime_slot: 0 },
      meals: { ...report.meals, days: [] },
      contributions: { talk: 0, topic: 0, skill: 0 },
    });
    renderAt("/admin/report");
    expect(await screen.findByText("Nessuna attività.")).toBeInTheDocument();
    expect(screen.getByText("0,0")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("explains when there is no edition yet", async () => {
    serve({ ...report, edition: null });
    renderAt("/admin/report");
    expect(await screen.findByText(/Nessuna edizione configurata/)).toBeInTheDocument();
  });

  it("tells when the report cannot be loaded", async () => {
    stubAdminApi(() => ({ status: 500, body: {} }));
    renderAt("/admin/report");
    expect(await screen.findByRole("alert")).toHaveTextContent("Non riesco a caricare il report");
  });

  it("is reachable from the admin menu", async () => {
    serve(report);
    renderAt("/admin/report");
    const link = await screen.findByRole("link", { name: "Report" });
    expect(link).toHaveAttribute("href", "/admin/report");
    expect(link).toHaveAttribute("aria-current", "page");
  });
});
