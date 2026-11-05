import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const edition = {
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
  payment_channels: [],
  privacy: null,
  disclaimer: null,
};

describe("settings", () => {
  it("edits the waitlist percentage", async () => {
    const calls = stubAdminApi((call) =>
      call.url === "/api/admin/edition" ? { body: edition } : undefined,
    );
    renderAt("/admin/impostazioni");
    const field = await screen.findByLabelText("Lista d'attesa (% dei posti)");
    expect(field).toHaveValue(20);
    await userEvent.clear(field);
    await userEvent.type(field, "30");
    await userEvent.click(screen.getByRole("button", { name: "Salva edizione" }));
    await waitFor(() =>
      expect(
        (calls.find((c) => c.method === "PUT")?.body as Record<string, unknown>).waitlist_percent,
      ).toBe(30),
    );
  });

  it("edits the meal prices", async () => {
    const calls = stubAdminApi((call) =>
      call.url === "/api/admin/edition" ? { body: edition } : undefined,
    );
    renderAt("/admin/impostazioni");
    const lunch = await screen.findByLabelText("Prezzo del pranzo (€)");
    expect(lunch).toHaveValue("8,00");
    await userEvent.clear(lunch);
    await userEvent.type(lunch, "9,50");
    await userEvent.click(screen.getByRole("button", { name: "Salva edizione" }));
    await waitFor(() => {
      const body = calls.find((c) => c.method === "PUT")?.body as Record<string, unknown>;
      expect([body.lunch_price_cents, body.dinner_price_cents]).toEqual([950, 1200]);
    });
  });

  it("offers the health consent text", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/edition" ? { body: edition } : undefined));
    renderAt("/admin/impostazioni");
    expect(
      await screen.findByRole("heading", { name: /Consenso per allergie e intolleranze/ }),
    ).toBeInTheDocument();
  });
});
