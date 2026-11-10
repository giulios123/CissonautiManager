import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const meal = (kind: "lunch" | "dinner", over: Record<string, unknown> = {}) => ({
  date: "2026-07-13",
  kind,
  label: kind === "lunch" ? "pranzo di lun 13/07" : "cena di lun 13/07",
  price_cents: kind === "lunch" ? 800 : 1200,
  payment_mode: "organizer",
  collectable_cents: kind === "lunch" ? 800 : 1200,
  ...over,
});
const hike = {
  id: 3,
  title: "Escursione",
  label: "Escursione (lun 13/07 mattina)",
  description: null,
  date: "2026-07-13",
  period: "morning",
  price_cents: 1500,
  payment_mode: "organizer",
  collectable_cents: 1500,
};

function detail(over: Record<string, unknown> = {}, booking: Record<string, unknown> = {}) {
  return {
    participant: {
      id: 1,
      first_name: "Ada",
      last_name: "Lovelace",
      email: "ada@example.com",
      phone: null,
      invited_by: null,
      can_bring: null,
      personal_code: "CSC-7K3P",
    },
    booking: {
      id: 7,
      status: "confermata",
      confirmation_policy: "registration_fee",
      registration_fee_cents: 1100,
      amount_due_cents: 4600,
      paid_cents: 4600,
      balance_cents: 0,
      hold_expires_at: "2026-07-04T10:00:00Z",
      editable: true,
      can_cancel: true,
      slots: [],
      schedule: [],
      payments: [],
      refunds: [],
      fee_exempt: false,
      meals: [meal("lunch"), meal("dinner")],
      activities: [hike],
      ...booking,
    },
    privacy: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
    disclaimer: { version: 1, accepted_at: "2026-07-01T10:00:00Z" },
    refund: null,
    history: [],
    warning: null,
    category: "ordinary",
    ...over,
  };
}

const preview = {
  preview_token: "a".repeat(64),
  status_before: "confermata",
  status_after: "confermata",
  registration_fee_before_cents: 1100,
  registration_fee_after_cents: 0,
  amount_due_before_cents: 4600,
  amount_due_after_cents: 3500,
  paid_cents: 4600,
  balance_before_cents: 0,
  balance_after_cents: -1100,
};

function serve(
  first: unknown,
  extra?: (call: Call) => { status?: number; body: unknown } | undefined,
) {
  return stubAdminApi((call) => {
    const special = extra?.(call);
    if (special) return special;
    if (call.url === "/api/admin/registrations/7" && call.method === "GET") return { body: first };
    return undefined;
  });
}

describe("category and exemptions panel", () => {
  it("previews the amounts before and after and applies only that preview", async () => {
    const calls = serve(detail(), (call) => {
      if (call.url.endsWith("/exemptions/preview")) return { body: preview };
      if (call.url.endsWith("/exemptions/apply"))
        return {
          body: detail(
            { category: "internal_non_paying" },
            {
              fee_exempt: true,
              registration_fee_cents: 0,
              amount_due_cents: 3500,
              balance_cents: -1100,
            },
          ),
        };
      return undefined;
    });
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    await userEvent.selectOptions(within(panel).getByLabelText("Categoria"), "internal_non_paying");
    await userEvent.click(within(panel).getByLabelText("Quota di partecipazione"));
    expect(within(panel).queryByRole("button", { name: "Applica le esenzioni" })).toBeNull();
    await userEvent.click(within(panel).getByRole("button", { name: "Mostra l'anteprima" }));
    const table = await within(panel).findByRole("table", { name: "Anteprima delle esenzioni" });
    expect(within(table).getByText("35,00 €")).toBeInTheDocument();
    await userEvent.click(within(panel).getByRole("button", { name: "Applica le esenzioni" }));
    await screen.findAllByText("Esenzioni applicate.");
    const sent = calls.filter((c) => c.url.includes("/exemptions/"));
    expect(sent.map((c) => c.url.split("/").pop())).toEqual(["preview", "apply"]);
    expect(sent[0].body).toMatchObject({ category: "internal_non_paying", fee_exempt: true });
    expect(sent[1].body).toMatchObject({ preview_token: preview.preview_token });
  });

  it("makes the preview obsolete when a choice changes", async () => {
    serve(detail(), (call) =>
      call.url.endsWith("/exemptions/preview") ? { body: preview } : undefined,
    );
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    await userEvent.click(within(panel).getByLabelText("Quota di partecipazione"));
    await userEvent.click(within(panel).getByRole("button", { name: "Mostra l'anteprima" }));
    await within(panel).findByRole("table", { name: "Anteprima delle esenzioni" });
    await userEvent.click(within(panel).getByLabelText(/pranzo di lun 13\/07/));
    expect(within(panel).queryByRole("table")).toBeNull();
    expect(within(panel).queryByRole("button", { name: "Applica le esenzioni" })).toBeNull();
  });

  it("shows the refusal of a stale preview and asks for a new one", async () => {
    serve(detail(), (call) => {
      if (call.url.endsWith("/exemptions/preview")) return { body: preview };
      if (call.url.endsWith("/exemptions/apply"))
        return { status: 409, body: { detail: "La prenotazione è cambiata dopo l'anteprima" } };
      return undefined;
    });
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    await userEvent.click(within(panel).getByLabelText("Quota di partecipazione"));
    await userEvent.click(within(panel).getByRole("button", { name: "Mostra l'anteprima" }));
    await userEvent.click(
      await within(panel).findByRole("button", { name: "Applica le esenzioni" }),
    );
    expect(await within(panel).findByRole("alert")).toHaveTextContent(
      "è cambiata dopo l'anteprima",
    );
    expect(within(panel).queryByRole("button", { name: "Applica le esenzioni" })).toBeNull();
  });

  it("saves the category alone without a preview", async () => {
    const calls = serve(detail(), (call) =>
      call.url.endsWith("/category")
        ? { body: detail({ category: "internal_non_paying" }) }
        : undefined,
    );
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    const save = within(panel).getByRole("button", { name: "Salva la categoria" });
    expect(save).toBeDisabled();
    await userEvent.selectOptions(within(panel).getByLabelText("Categoria"), "internal_non_paying");
    await userEvent.click(save);
    await screen.findAllByText("Categoria salvata.");
    expect(calls.find((c) => c.url.endsWith("/category"))?.body).toEqual({
      category: "internal_non_paying",
    });
  });

  it("does not offer provider items for exemption and is absent for closed bookings", async () => {
    serve(
      detail({}, { meals: [meal("lunch", { payment_mode: "provider", collectable_cents: 0 })] }),
    );
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    expect(within(panel).queryByLabelText(/pranzo di lun 13\/07/)).toBeNull();
  });

  it("hides the panel when the booking cannot be edited", async () => {
    serve(detail({}, { editable: false, status: "rimborsata" }));
    renderAt("/admin/registrations/7");
    await screen.findByRole("heading", { name: /Iscrizione/ });
    expect(screen.queryByRole("heading", { name: "Categoria ed esenzioni" })).toBeNull();
  });

  it("marks the exempt items already saved", async () => {
    serve(
      detail({}, { fee_exempt: true, meals: [meal("lunch", { exempt: true }), meal("dinner")] }),
    );
    renderAt("/admin/registrations/7");
    const panel = (await screen.findByRole("heading", { name: "Categoria ed esenzioni" }))
      .parentElement as HTMLElement;
    expect(within(panel).getByLabelText("Quota di partecipazione")).toBeChecked();
    expect(within(panel).getByLabelText(/pranzo di lun 13\/07/)).toBeChecked();
    expect(within(panel).getByLabelText(/cena di lun 13\/07/)).not.toBeChecked();
  });
});

describe("refunds of credit", () => {
  const credit = { paid_cents: 5000, balance_cents: -400 };

  it("shows the credit and records a refund with a retry-safe key", async () => {
    const calls = serve(detail({}, credit), (call) =>
      call.url.endsWith("/refunds")
        ? {
            status: 201,
            body: detail(
              {},
              {
                paid_cents: 4600,
                balance_cents: 0,
                refunds: [
                  {
                    id: 1,
                    amount_cents: 400,
                    channel: "satispay",
                    refunded_on: "2026-07-13",
                    note: "contanti",
                  },
                ],
              },
            ),
          }
        : undefined,
    );
    renderAt("/admin/registrations/7");
    const section = (await screen.findByRole("heading", { name: "Credito e rimborsi" }))
      .parentElement as HTMLElement;
    expect(
      within(section).getByText(/Credito \(versato oltre il totale dovuto\): 4,00 €/),
    ).toBeInTheDocument();
    await userEvent.click(within(section).getByRole("button", { name: "Registra un rimborso" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByLabelText("Importo rimborsato (€)")).toHaveValue("4,00");
    await userEvent.selectOptions(within(dialog).getByLabelText("Canale"), "satispay");
    await userEvent.click(within(dialog).getByRole("button", { name: "Registra rimborso" }));
    await screen.findAllByText(/Rimborso registrato/);
    const post = calls.find((c) => c.url.endsWith("/refunds"));
    expect(post?.body).toMatchObject({ amount_cents: 400, channel: "satispay" });
    expect((post?.body as { request_key: string }).request_key).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("shows the refusal of the server in the dialog", async () => {
    serve(detail({}, credit), (call) =>
      call.url.endsWith("/refunds")
        ? { status: 422, body: { detail: "Il rimborso non può superare il credito" } }
        : undefined,
    );
    renderAt("/admin/registrations/7");
    await userEvent.click(await screen.findByRole("button", { name: "Registra un rimborso" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Registra rimborso" }));
    expect(await within(dialog).findByText(/non può superare il credito/)).toBeInTheDocument();
  });

  it("has no refund button without credit", async () => {
    serve(detail());
    renderAt("/admin/registrations/7");
    await screen.findByRole("heading", { name: /Iscrizione/ });
    expect(screen.queryByRole("button", { name: "Registra un rimborso" })).toBeNull();
  });

  it("voids a refund with a reason and shows it struck through", async () => {
    const withRefund = detail(
      {},
      {
        ...credit,
        refunds: [
          { id: 1, amount_cents: 400, channel: "revolut", refunded_on: "2026-07-13", note: null },
        ],
      },
    );
    const calls = serve(withRefund, (call) =>
      call.url.endsWith("/refunds/1/void")
        ? {
            body: detail(
              {},
              {
                ...credit,
                refunds: [
                  {
                    id: 1,
                    amount_cents: 400,
                    channel: "revolut",
                    refunded_on: "2026-07-13",
                    note: null,
                    voided: true,
                    void_reason: "Errore",
                  },
                ],
              },
            ),
          }
        : undefined,
    );
    renderAt("/admin/registrations/7");
    await userEvent.click(await screen.findByRole("button", { name: /Annulla il rimborso di/ }));
    const dialog = await screen.findByRole("dialog");
    const confirm = within(dialog).getByRole("button", { name: "Sì, annullo" });
    expect(confirm).toBeDisabled();
    await userEvent.type(within(dialog).getByLabelText("Motivo (obbligatorio)"), "Errore");
    await userEvent.click(confirm);
    await screen.findAllByText("Rimborso annullato.");
    expect(screen.getByText("annullato")).toBeInTheDocument();
    expect(calls.find((c) => c.url.endsWith("/void"))?.body).toEqual({ reason: "Errore" });
  });
});

describe("people list and report", () => {
  it("filters by category and marks the internal ones", async () => {
    const row = (id: number, name: string, category: string) => ({
      id,
      first_name: name,
      last_name: "Test",
      email: `${name}@example.com`,
      phone: null,
      personal_code: `CSC-${id}`,
      days: 1,
      evenings: 0,
      status: "confermata",
      amount_due_cents: 1100,
      paid_cents: 1100,
      balance_cents: 0,
      hold_expires_at: null,
      created_at: "2026-07-01T10:00:00Z",
      category,
      fee_exempt: category === "internal_non_paying",
    });
    const calls = stubAdminApi((call) => {
      if (!call.url.startsWith("/api/admin/registrations")) return undefined;
      const internal = call.url.includes("category=internal_non_paying");
      return {
        body: internal
          ? [row(2, "Bea", "internal_non_paying")]
          : [row(1, "Ada", "ordinary"), row(2, "Bea", "internal_non_paying")],
      };
    });
    renderAt("/admin");
    const bea = await screen.findByRole("link", { name: /Bea Test/ });
    expect(bea.closest("tr")).toHaveTextContent("Interno non pagante");
    expect(screen.getByRole("link", { name: /Ada Test/ }).closest("tr")).not.toHaveTextContent(
      "Interno non pagante",
    );
    await userEvent.selectOptions(screen.getByLabelText("Categoria"), "internal_non_paying");
    await waitFor(() => expect(screen.queryByRole("link", { name: /Ada Test/ })).toBeNull());
    expect(calls.some((c) => c.url.includes("category=internal_non_paying"))).toBe(true);
  });
});
