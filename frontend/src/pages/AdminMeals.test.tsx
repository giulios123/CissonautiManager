import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call, type Reply } from "../test-utils";

const detailFixture = (
  over: Record<string, unknown> = {},
  booking: Record<string, unknown> = {},
) => ({
  participant: {
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    phone: null,
    invited_by: null,
    can_bring: "Un talk",
    personal_code: "CSC-7K3P",
  },
  booking: {
    id: 7,
    status: "confermata",
    amount_due_cents: 1100,
    paid_cents: 1100,
    balance_cents: 0,
    hold_expires_at: "2026-07-04T10:00:00Z",
    editable: true,
    can_cancel: true,
    slots: [],
    payments: [],
    ...booking,
  },
  privacy: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
  disclaimer: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
  refund: null,
  history: [],
  warning: null,
  ...over,
});

function serve(detail: unknown, extra: (call: Call) => Reply | undefined) {
  return stubAdminApi((call) => {
    const special = extra(call);
    if (special) return special;
    if (call.url === "/api/admin/registrations/7" && call.method === "GET") return { body: detail };
    return undefined;
  });
}

afterEach(() => vi.unstubAllGlobals());

const allowed = [
  { date: "2026-07-13", kind: "lunch", label: "pranzo di lun 13/07", past: true },
  { date: "2026-07-13", kind: "dinner", label: "cena di lun 13/07", past: true },
];

describe("meals in the admin detail", () => {
  it("shows diet and allergies and changes meals of a past day", async () => {
    const detail = detailFixture(
      { lunch_price_cents: 800, dinner_price_cents: 1200 },
      {
        allowed_meals: allowed,
        meals: [],
        diet: "vegan",
        allergies: "Arachidi",
        health_consent_version: 1,
      },
    );
    const calls = serve(detail, (call) =>
      call.url === "/api/admin/registrations/7/meals"
        ? { body: detailFixture({}, { meals: [allowed[0]], allowed_meals: allowed }) }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const section = (await screen.findByRole("heading", { name: "Pasti ed esigenze alimentari" }))
      .parentElement as HTMLElement;
    expect(within(section).getByText(/Regime: vegano/)).toBeInTheDocument();
    expect(within(section).getByText(/Arachidi \(consenso versione 1\)/)).toBeInTheDocument();
    await userEvent.click(within(section).getByRole("button", { name: "Cambia i pasti" }));
    const form = within(screen.getByRole("form", { name: "Scegli pranzi e cene" }));
    const lunch = form.getByRole("checkbox", { name: "Pranzo" });
    expect(lunch).toBeEnabled();
    await userEvent.click(lunch);
    await userEvent.click(form.getByRole("button", { name: "Salva i pasti" }));
    expect((await screen.findAllByText("Pasti aggiornati.")).length).toBeGreaterThan(0);
    expect(calls.find((c) => c.method === "PUT")?.body).toEqual({
      meals: [{ date: "2026-07-13", kind: "lunch" }],
    });
  });
});

describe("meals view", () => {
  const view = {
    days: [
      {
        date: "2026-07-13",
        meals: [
          {
            kind: "lunch",
            count: 2,
            diets: { omnivore: 1, vegetarian: 0, vegan: 1, none: 0 },
            people: [
              {
                booking_id: 7,
                first_name: "Ada",
                last_name: "Lovelace",
                diet: "vegan",
                allergies: "Arachidi",
              },
              {
                booking_id: 8,
                first_name: "Bob",
                last_name: "Rossi",
                diet: "omnivore",
                allergies: null,
              },
            ],
          },
          {
            kind: "dinner",
            count: 0,
            diets: { omnivore: 0, vegetarian: 0, vegan: 0, none: 0 },
            people: [],
          },
        ],
      },
    ],
  };

  it("shows counts, diets and allergies per meal", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/views/meals" ? { body: view } : undefined));
    renderAt("/admin/pasti");
    const lunch = (await screen.findByRole("rowheader", { name: "Pranzo" })).closest(
      "tr",
    ) as HTMLElement;
    expect(within(lunch).getByText("1 onnivori, 1 vegani")).toBeInTheDocument();
    expect(within(lunch).getByText("Ada Lovelace: Arachidi")).toBeInTheDocument();
    expect(within(lunch).getByRole("link", { name: "Bob Rossi" })).toHaveAttribute(
      "href",
      "/admin/iscrizioni/8",
    );
  });

  it("asks before downloading the CSV with health data", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/views/meals" ? { body: view } : undefined));
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);
    renderAt("/admin/pasti");
    const link = await screen.findByRole("link", { name: "Scarica CSV" });
    expect(link).toHaveAttribute("href", "/api/admin/views/meals?format=csv");
    await userEvent.click(link);
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("dati sanitari"));
  });
});
