import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const base = {
  id: 4,
  first_name: "Anna",
  last_name: "Rossi",
  payer: "paying",
  phone: null,
  reference: null,
  internal_note: null,
  diet: null,
  allergies: null,
  allergies_consent_at: null,
  meals: [{ date: "2026-07-13", kind: "lunch" }],
  activities: [],
  due_cents: 800,
  paid_cents: 0,
  refunded_cents: 0,
  balance_cents: 800,
  items: [{ label: "pranzo di lun 13/07", price_cents: 800, collectable_cents: 800 }],
  movements: [],
};
const payment = {
  id: 9,
  kind: "payment",
  amount_cents: 1000,
  channel: "revolut",
  paid_on: "2026-07-13",
  note: "contanti",
  created_at: "2026-07-13T10:00:00Z",
  voided_at: null,
  void_reason: null,
};

function serve(
  guest: object,
  extra?: (call: Call) => { status?: number; body: unknown } | undefined,
) {
  return stubAdminApi((call) => {
    const special = extra?.(call);
    if (special) return special;
    if (call.url === "/api/admin/guests/4" && call.method === "GET") return { body: guest };
    if (call.url === "/api/admin/views/meals") return { body: { days: [] } };
    if (call.url === "/api/admin/activities") return { body: [] };
    return undefined;
  });
}

describe("guest accounts", () => {
  it("shows what is due, the items and records a payment once per request", async () => {
    const calls = serve(base, (call) =>
      call.url === "/api/admin/guests/4/movements"
        ? {
            status: 201,
            body: {
              ...base,
              paid_cents: 500,
              balance_cents: 300,
              movements: [{ ...payment, amount_cents: 500 }],
            },
          }
        : undefined,
    );
    renderAt("/admin/guests/4");
    const section = (await screen.findByRole("heading", { name: "Conti" }))
      .parentElement as HTMLElement;
    expect(within(section).getByText(/pranzo di lun 13\/07/)).toBeInTheDocument();
    expect(within(section).queryByRole("button", { name: "Registra una restituzione" })).toBeNull();

    await userEvent.click(within(section).getByRole("button", { name: "Registra un pagamento" }));
    const dialog = await screen.findByRole("dialog");
    // The balance is the suggestion.
    expect(within(dialog).getByLabelText("Importo ricevuto (€)")).toHaveValue("8,00");
    await userEvent.clear(within(dialog).getByLabelText("Importo ricevuto (€)"));
    await userEvent.type(within(dialog).getByLabelText("Importo ricevuto (€)"), "5");
    await userEvent.selectOptions(within(dialog).getByLabelText("Canale"), "satispay");
    await userEvent.click(within(dialog).getByRole("button", { name: "Registra pagamento" }));
    await screen.findByText("Pagamento registrato.");
    const post = calls.find((c) => c.method === "POST");
    expect(post?.body).toMatchObject({ kind: "payment", amount_cents: 500, channel: "satispay" });
    expect((post?.body as { request_key: string }).request_key).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("offers a refund only when there is a credit and caps the suggestion at it", async () => {
    serve({
      ...base,
      paid_cents: 1000,
      balance_cents: -200,
      movements: [payment],
    });
    renderAt("/admin/guests/4");
    const section = (await screen.findByRole("heading", { name: "Conti" }))
      .parentElement as HTMLElement;
    expect(within(section).getByText("Credito")).toBeInTheDocument();
    await userEvent.click(
      within(section).getByRole("button", { name: "Registra una restituzione" }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Credito da restituire: 2,00 €")).toBeInTheDocument();
    expect(within(dialog).getByLabelText("Importo ricevuto (€)")).toHaveValue("2,00");
  });

  it("shows a server refusal in the dialog", async () => {
    serve({ ...base, paid_cents: 1000, balance_cents: -200, movements: [payment] }, (call) =>
      call.url === "/api/admin/guests/4/movements"
        ? { status: 422, body: { detail: "La restituzione non può superare il credito" } }
        : undefined,
    );
    renderAt("/admin/guests/4");
    await userEvent.click(await screen.findByRole("button", { name: "Registra una restituzione" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Registra restituzione" }));
    expect(await within(dialog).findByText(/non può superare il credito/)).toBeInTheDocument();
  });

  it("voids a movement with a reason and shows it struck through", async () => {
    const calls = serve(
      { ...base, paid_cents: 1000, balance_cents: -200, movements: [payment] },
      (call) =>
        call.url === "/api/admin/guests/movements/9/void"
          ? {
              body: {
                ...base,
                movements: [
                  { ...payment, voided_at: "2026-07-13T11:00:00Z", void_reason: "Doppione" },
                ],
              },
            }
          : undefined,
    );
    renderAt("/admin/guests/4");
    await userEvent.click(await screen.findByRole("button", { name: /Annulla il pagamento di/ }));
    const dialog = await screen.findByRole("dialog");
    const confirm = within(dialog).getByRole("button", { name: "Sì, annullo" });
    expect(confirm).toBeDisabled();
    await userEvent.type(within(dialog).getByLabelText("Motivo (obbligatorio)"), "Doppione");
    await userEvent.click(confirm);
    await screen.findByText("Movimento annullato: non conta più nei conti.");
    expect(screen.getByText("annullato")).toBeInTheDocument();
    expect(screen.getByText(/Doppione/)).toBeInTheDocument();
    expect(calls.find((c) => c.url.endsWith("/void"))?.body).toEqual({ reason: "Doppione" });
  });

  it("says the guest owes nothing when not paying", async () => {
    serve({ ...base, payer: "non_paying", due_cents: 0, balance_cents: 0 });
    renderAt("/admin/guests/4");
    expect(await screen.findByText(/Esterno non pagante: non deve nulla/)).toBeInTheDocument();
  });

  it("marks a provider item as not part of the account", async () => {
    serve({
      ...base,
      due_cents: 0,
      balance_cents: 0,
      items: [{ label: "pranzo di lun 13/07", price_cents: 900, collectable_cents: 0 }],
    });
    renderAt("/admin/guests/4");
    expect(await screen.findByText(/9,00 € da pagare al fornitore/)).toBeInTheDocument();
  });
});

describe("guests in the to-collect page", () => {
  const row = {
    guest_id: 4,
    first_name: "Anna",
    last_name: "Rossi",
    reference: "con Maria",
    items: [{ label: "pranzo di lun 13/07", price_cents: 800, collectable_cents: 800 }],
    due_cents: 800,
    paid_cents: 300,
    balance_cents: 500,
  };

  it("lists guests apart from the bookings and records a payment from the row", async () => {
    let rows: unknown[] = [row];
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/views/to-collect") return { body: [] };
      if (call.url.startsWith("/api/admin/guests/to-collect")) return { body: rows };
      if (call.url === "/api/admin/guests/4/movements") {
        rows = [];
        return { status: 201, body: { ...base, paid_cents: 800, balance_cents: 0 } };
      }
      return undefined;
    });
    renderAt("/admin/to-collect");
    const section = (await screen.findByRole("heading", { name: "Esterni da incassare" }))
      .parentElement as HTMLElement;
    const line = within(section)
      .getByRole("rowheader", { name: /Anna Rossi/ })
      .closest("tr") as HTMLElement;
    expect(within(line).getByText(/pranzo di lun 13\/07 · 8,00 €/)).toBeInTheDocument();
    expect(within(line).getByText("5,00 €")).toBeInTheDocument();
    await userEvent.click(
      within(line).getByRole("button", { name: /Registra un incasso da Anna Rossi/ }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByLabelText("Importo ricevuto (€)")).toHaveValue("5,00");
    await userEvent.click(within(dialog).getByRole("button", { name: "Registra pagamento" }));
    await screen.findByText("Incasso registrato per Anna Rossi.");
    await waitFor(() =>
      expect(screen.queryByRole("rowheader", { name: /Anna Rossi/ })).not.toBeInTheDocument(),
    );
    expect(calls.filter((c) => c.url.endsWith("/movements"))).toHaveLength(1);
  });

  it("stays out of the way when no guest owes anything", async () => {
    stubAdminApi((call) => {
      if (call.url === "/api/admin/views/to-collect") return { body: [] };
      if (call.url.startsWith("/api/admin/guests/to-collect")) return { body: [] };
      return undefined;
    });
    renderAt("/admin/to-collect");
    await screen.findByRole("heading", { name: "Da incassare" });
    expect(screen.queryByRole("heading", { name: "Esterni da incassare" })).toBeNull();
  });

  it("searches guests by name", async () => {
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/views/to-collect") return { body: [] };
      if (call.url.startsWith("/api/admin/guests/to-collect")) return { body: [row] };
      return undefined;
    });
    renderAt("/admin/to-collect");
    await userEvent.type(await screen.findByLabelText("Cerca un esterno per nome"), "ann");
    await waitFor(() =>
      expect(calls.some((c) => c.url === "/api/admin/guests/to-collect?q=ann")).toBe(true),
    );
  });
});

describe("guest money in the report", () => {
  it("shows the guest figures apart and the event total", async () => {
    const revenue = {
      due_cents: 0,
      due_fee_cents: 0,
      due_meals_cents: 0,
      due_activities_cents: 0,
      due_difference_cents: 0,
      paid_cents: 0,
      paid_by_channel: {},
      refunded_cents: 0,
      net_cents: 0,
      to_collect_cents: 0,
      to_confirm_cents: null,
      credits_cents: 0,
      to_refund_cents: 0,
      external_due_cents: 800,
      external_paid_cents: 600,
      external_refunded_cents: 0,
      external_net_cents: 600,
      external_to_collect_cents: 200,
      external_credit_cents: 0,
      event_net_cents: 600,
    };
    const split = { confirmed: 0, pending: 0, external: 0, total: 0 };
    stubAdminApi((call) =>
      call.url === "/api/admin/views/report"
        ? {
            body: {
              edition: { name: "Camp", start_date: null, end_date: null },
              enrollment: { by_status: {}, people_with_seat: 0 },
              presence: { slots: [], peak: 0, average_per_daytime_slot: 0, person_days: split },
              meals: {
                days: [],
                lunches: split,
                dinners: split,
                lunch_diets: {},
                dinner_diets: {},
                people_with_allergies: 0,
              },
              activities: [],
              contributions: {},
              waitlist: {
                waiting: 0,
                promoted: 0,
                promoted_plus_one: 0,
                left: 0,
                removed: 0,
                cancelled: 0,
                booked: 0,
              },
              revenue,
              days: [],
            },
          }
        : undefined,
    );
    renderAt("/admin/report");
    const table = await screen.findByRole("table", { name: "Incassi esterni" });
    expect(within(table).getByText("Versato dagli esterni").closest("tr")).toHaveTextContent(
      "6,00",
    );
    expect(
      within(table).getByText("Totale evento (quote più esterni)").closest("tr"),
    ).toHaveTextContent("6,00");
  });
});
