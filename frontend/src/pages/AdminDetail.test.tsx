import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call, type Reply } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

export const detailFixture = (
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
    status: "in_attesa_pagamento",
    amount_due_cents: 1100,
    paid_cents: 0,
    balance_cents: 1100,
    hold_expires_at: "2026-07-04T10:00:00Z",
    editable: true,
    can_cancel: true,
    slots: [
      { id: 1, date: "2026-07-13", period: "morning", label: "lun 13/07 mattina (09:00-13:00)" },
    ],
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

export function serve(detail: unknown, extra?: (call: Call) => Reply | undefined) {
  return stubAdminApi((call) => {
    const special = extra?.(call);
    if (special) return special;
    if (call.url === "/api/admin/registrations/7" && call.method === "GET") return { body: detail };
    return undefined;
  });
}

describe("refund", () => {
  const cancelled = detailFixture(
    {},
    {
      status: "disdetta_richiesta",
      paid_cents: 1100,
      balance_cents: 0,
      editable: false,
      can_cancel: false,
    },
  );

  it("is offered only on a requested cancellation", async () => {
    serve(detailFixture());
    renderAt("/admin/iscrizioni/7");
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    expect(
      screen.queryByRole("heading", { name: "Segna come rimborsata" }),
    ).not.toBeInTheDocument();
  });

  it("starts from what was paid and sends amount, date and note", async () => {
    const closed = detailFixture(
      { refund: { amount_cents: 1100, refunded_on: "2026-07-03", note: "Revolut" } },
      {
        status: "rimborsata",
        paid_cents: 1100,
        balance_cents: 0,
        editable: false,
        can_cancel: false,
      },
    );
    const calls = serve(cancelled, (call) =>
      call.method === "POST" ? { body: closed } : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const user = userEvent.setup();
    const form = within(await screen.findByRole("form", { name: "Segna come rimborsata" }));
    expect(form.getByLabelText("Importo rimborsato (€)")).toHaveValue("11,00");
    await user.type(form.getByLabelText("Nota (facoltativa)"), "Revolut");
    await user.click(form.getByRole("button", { name: "Segna come rimborsata" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Disdetta chiusa");
    const post = calls.find((call) => call.method === "POST")!;
    expect(post.url).toBe("/api/admin/registrations/7/refund");
    expect(post.body).toEqual({ amount_cents: 1100, refunded_on: null, note: "Revolut" });
    expect(screen.getByText(/Rimborsati/)).toHaveTextContent("11,00");
    expect(screen.queryByRole("form", { name: "Segna come rimborsata" })).not.toBeInTheDocument();
  });

  it("lets the amount be zero when nothing was paid", async () => {
    const calls = serve(
      detailFixture({}, { status: "disdetta_richiesta", paid_cents: 0, balance_cents: 1100 }),
      (call) => (call.method === "POST" ? { body: detailFixture() } : undefined),
    );
    renderAt("/admin/iscrizioni/7");
    const form = within(await screen.findByRole("form", { name: "Segna come rimborsata" }));
    expect(form.getByLabelText("Importo rimborsato (€)")).toHaveValue("0,00");
    expect(form.queryByRole("button", { name: /Tutto quanto versato/ })).not.toBeInTheDocument();
    await userEvent.click(form.getByRole("button", { name: "Segna come rimborsata" }));
    await screen.findByRole("status");
    expect(calls.find((call) => call.method === "POST")?.body).toMatchObject({ amount_cents: 0 });
  });

  it("rejects an invalid amount without calling the server", async () => {
    const calls = serve(cancelled);
    renderAt("/admin/iscrizioni/7");
    const user = userEvent.setup();
    const form = within(await screen.findByRole("form", { name: "Segna come rimborsata" }));
    await user.clear(form.getByLabelText("Importo rimborsato (€)"));
    await user.type(form.getByLabelText("Importo rimborsato (€)"), "abc");
    await user.click(form.getByRole("button", { name: "Segna come rimborsata" }));
    expect(await form.findByRole("alert")).toHaveTextContent("importo valido");
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("shows the server's refusal", async () => {
    serve(cancelled, (call) =>
      call.method === "POST"
        ? { status: 422, body: { detail: "Il rimborso non può superare quanto versato (11,00 €)" } }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const form = within(await screen.findByRole("form", { name: "Segna come rimborsata" }));
    await userEvent.click(form.getByRole("button", { name: "Segna come rimborsata" }));
    expect(await form.findByRole("alert")).toHaveTextContent("non può superare");
  });
});

describe("history", () => {
  it("lists what admins did by hand, newest first", async () => {
    serve(
      detailFixture({
        history: [
          {
            at: "2026-07-03T09:00:00Z",
            actor: "Gina Organizer",
            action: "refund",
            detail: "Rimborso registrato: 11,00 € il 03/07/2026",
          },
          {
            at: "2026-07-02T09:00:00Z",
            actor: "Gina Organizer",
            action: "x",
            detail: "Prima modifica",
          },
        ],
      }),
    );
    renderAt("/admin/iscrizioni/7");
    const section = within(await screen.findByRole("region", { name: "Cronologia" }));
    const items = section.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Rimborso registrato");
    expect(items[0]).toHaveTextContent("Gina Organizer");
    expect(items[1]).toHaveTextContent("Prima modifica");
  });

  it("is not shown when there is nothing to tell", async () => {
    serve(detailFixture());
    renderAt("/admin/iscrizioni/7");
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    expect(screen.queryByRole("region", { name: "Cronologia" })).not.toBeInTheDocument();
  });
});

describe("edit details", () => {
  it("shows the saved values and sends them all, clearing what was emptied", async () => {
    const updated = detailFixture({
      participant: {
        first_name: "Adele",
        last_name: "Lovelace",
        email: "ada@example.com",
        phone: null,
        invited_by: null,
        can_bring: "Un talk",
        personal_code: "CSC-7K3P",
      },
    });
    const calls = serve(
      detailFixture({
        participant: {
          first_name: "Ada",
          last_name: "Lovelace",
          email: "ada@example.com",
          phone: "+39 333 111",
          invited_by: "Grace",
          can_bring: "Un talk",
          personal_code: "CSC-7K3P",
        },
      }),
      (call) => (call.method === "PATCH" ? { body: updated } : undefined),
    );
    renderAt("/admin/iscrizioni/7");
    const user = userEvent.setup();
    const form = within(await screen.findByRole("form", { name: "Modifica i dati" }));
    expect(form.getByLabelText("Nome")).toHaveValue("Ada");
    expect(form.getByLabelText(/Telefono/)).toHaveValue("+39 333 111");
    await user.clear(form.getByLabelText("Nome"));
    await user.type(form.getByLabelText("Nome"), "Adele");
    await user.clear(form.getByLabelText(/Telefono/));
    await user.clear(form.getByLabelText(/Invitato da/));
    await user.click(form.getByRole("button", { name: "Salva i dati" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Dati salvati");
    const patch = calls.find((call) => call.method === "PATCH")!;
    expect(patch.url).toBe("/api/admin/registrations/7");
    expect(patch.body).toEqual({
      first_name: "Adele",
      last_name: "Lovelace",
      email: "ada@example.com",
      phone: "",
      invited_by: "",
      can_bring: "Un talk",
    });
    expect(screen.getByLabelText("Nome")).toHaveValue("Adele");
  });

  it("shows why the server refused, next to the form", async () => {
    serve(detailFixture(), (call) =>
      call.method === "PATCH"
        ? { status: 409, body: { detail: "Questa email è già usata da un'altra persona" } }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const form = within(await screen.findByRole("form", { name: "Modifica i dati" }));
    await userEvent.click(form.getByRole("button", { name: "Salva i dati" }));
    expect(await form.findByRole("alert")).toHaveTextContent("già usata");
  });
});

describe("hold extension and reactivation", () => {
  it("proposes the current deadline in Rome time and sends the new one as typed", async () => {
    const calls = serve(detailFixture(), (call) =>
      call.method === "PATCH" ? { body: detailFixture() } : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const form = within(await screen.findByRole("form", { name: "Proroga il blocco" }));
    const input = form.getByLabelText("Nuova scadenza");
    expect(input).toHaveValue("2026-07-04T12:00"); // 10:00 UTC is 12:00 in Rome
    fireEvent.change(input, { target: { value: "2026-07-08T11:00" } });
    await userEvent.click(form.getByRole("button", { name: "Proroga" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Scadenza prorogata");
    expect(calls.find((call) => call.method === "PATCH")?.body).toEqual({
      hold_expires_at: "2026-07-08T11:00",
    });
  });

  it("shows the server's refusal", async () => {
    serve(detailFixture(), (call) =>
      call.method === "PATCH"
        ? {
            status: 422,
            body: { detail: "La nuova scadenza deve essere successiva a quella attuale" },
          }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const form = within(await screen.findByRole("form", { name: "Proroga il blocco" }));
    await userEvent.click(form.getByRole("button", { name: "Proroga" }));
    expect(await form.findByRole("alert")).toHaveTextContent("successiva");
  });

  it("offers neither action on a confirmed booking", async () => {
    serve(detailFixture({}, { status: "confermata" }));
    renderAt("/admin/iscrizioni/7");
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    expect(screen.queryByRole("form", { name: "Proroga il blocco" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Riattiva la prenotazione" }),
    ).not.toBeInTheDocument();
  });

  it("reactivates an expired booking", async () => {
    const calls = serve(detailFixture({}, { status: "scaduta" }), (call) =>
      call.method === "POST" ? { body: detailFixture() } : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    expect(screen.queryByRole("form", { name: "Proroga il blocco" })).not.toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: "Riattiva la prenotazione" }));
    expect(await screen.findByRole("status")).toHaveTextContent("riattivata");
    expect(calls.find((call) => call.method === "POST")?.url).toBe(
      "/api/admin/registrations/7/reactivate",
    );
    expect(screen.getByRole("form", { name: "Proroga il blocco" })).toBeInTheDocument();
  });

  it("says when there is no room left", async () => {
    serve(detailFixture({}, { status: "scaduta" }), (call) =>
      call.method === "POST"
        ? { status: 409, body: { detail: "Non c'è più posto in questi slot: lun 13/07 mattina" } }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    await userEvent.click(await screen.findByRole("button", { name: "Riattiva la prenotazione" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Non c'è più posto");
  });
});

const slotsView = {
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
          present: 1,
          free: 24,
        },
        {
          id: 2,
          period: "afternoon",
          start_time: "14:00:00",
          end_time: "18:00:00",
          capacity: 1,
          present: 1,
          free: 0,
        },
        {
          id: 3,
          period: "evening",
          start_time: "19:00:00",
          end_time: "00:00:00",
          capacity: null,
          present: 4,
          free: null,
        },
      ],
    },
    {
      date: "2026-07-14",
      slots: [
        {
          id: 4,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 25,
          present: 0,
          free: 25,
        },
      ],
    },
  ],
};

describe("admin slot editor", () => {
  const open = async (extra?: (call: Call) => Reply | undefined) => {
    const calls = serve(detailFixture(), (call) =>
      call.url === "/api/admin/views/slots" ? { body: slotsView } : extra?.(call),
    );
    renderAt("/admin/iscrizioni/7");
    await userEvent.click(await screen.findByRole("button", { name: "Cambia gli slot" }));
    return { calls, form: within(await screen.findByRole("form", { name: "Cambia gli slot" })) };
  };

  it("shows presences and starts from the person's own slots", async () => {
    const { form } = await open();
    const [monday] = form.getAllByRole("group");
    expect(within(monday).getByRole("checkbox", { name: /Mattina/ })).toBeChecked();
    expect(
      within(monday).getByRole("checkbox", { name: /Mattina.*1\/25 presenti/ }),
    ).toBeInTheDocument();
    expect(
      within(monday).getByRole("checkbox", { name: /Sera.*4 presenti, senza limite/ }),
    ).toBeInTheDocument();
  });

  it("does not let a full slot be added until the capacity is forced", async () => {
    const { form } = await open();
    const [monday] = form.getAllByRole("group");
    const full = within(monday).getByRole("checkbox", { name: /Pomeriggio.*completo/ });
    expect(full).toBeDisabled();
    await userEvent.click(form.getByRole("checkbox", { name: /Forza oltre la capienza/ }));
    expect(full).toBeEnabled();
  });

  it("sends the chosen slots and the force flag, then shows the new amount", async () => {
    const updated = detailFixture(
      { warning: "Attenzione: capienza superata in lun 13/07 pomeriggio." },
      { amount_due_cents: 1200 },
    );
    const { calls, form } = await open((call) =>
      call.method === "PUT" ? { body: updated } : undefined,
    );
    const [monday, tuesday] = form.getAllByRole("group");
    await userEvent.click(form.getByRole("checkbox", { name: /Forza oltre la capienza/ }));
    await userEvent.click(within(monday).getByRole("checkbox", { name: /Pomeriggio/ }));
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    await userEvent.click(form.getByRole("button", { name: "Salva gli slot" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Nuova quota: 12,00");
    expect(calls.find((call) => call.method === "PUT")).toMatchObject({
      url: "/api/admin/registrations/7/slots",
      body: { slot_ids: [1, 2, 4], force: true },
    });
    expect(screen.getByText(/capienza superata/)).toBeInTheDocument();
  });

  it("shows the server's refusal", async () => {
    const { form } = await open((call) =>
      call.method === "PUT"
        ? { status: 409, body: { detail: "Questi slot sono al completo: lun 13/07 pomeriggio." } }
        : undefined,
    );
    await userEvent.click(form.getByRole("button", { name: "Salva gli slot" }));
    expect(await form.findByRole("alert")).toHaveTextContent("al completo");
  });

  it("is not offered when the booking can no longer change", async () => {
    serve(detailFixture({}, { status: "rimborsata", editable: false, can_cancel: false }));
    renderAt("/admin/iscrizioni/7");
    await screen.findByRole("heading", { name: "Ada Lovelace" });
    expect(screen.queryByRole("button", { name: "Cambia gli slot" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Disdici a nome della persona" }),
    ).not.toBeInTheDocument();
  });
});

describe("admin cancellation", () => {
  const ask = async () => {
    await userEvent.click(
      await screen.findByRole("button", { name: "Disdici a nome della persona" }),
    );
    return within(await screen.findByRole("dialog"));
  };

  it("asks first, saying what happens to payments, and does nothing if you go back", async () => {
    const calls = serve(detailFixture({}, { paid_cents: 500, balance_cents: 600 }));
    renderAt("/admin/iscrizioni/7");
    const dialog = await ask();
    expect(dialog.getByText(/Ha già versato 5,00/)).toBeInTheDocument();
    await userEvent.click(dialog.getByRole("button", { name: "No, torno indietro" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("keeps the booking on screen when a refund is still to be recorded", async () => {
    const after = detailFixture(
      {},
      { status: "disdetta_richiesta", paid_cents: 500, editable: false, can_cancel: false },
    );
    const calls = serve(detailFixture({}, { paid_cents: 500, balance_cents: 600 }), (call) =>
      call.method === "POST" ? { body: { outcome: "requested", detail: after } } : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const dialog = await ask();
    await userEvent.click(dialog.getByRole("button", { name: "Sì, disdico" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Disdetta registrata");
    expect(calls.find((call) => call.method === "POST")?.url).toBe(
      "/api/admin/registrations/7/cancel",
    );
    expect(screen.getByRole("form", { name: "Segna come rimborsata" })).toBeInTheDocument();
  });

  it("goes back to the list when the booking was removed, and says so there", async () => {
    serve(detailFixture(), (call) => {
      if (call.method === "POST") return { body: { outcome: "removed", detail: null } };
      if (call.url.startsWith("/api/admin/registrations?")) return { body: [] };
      return undefined;
    });
    renderAt("/admin/iscrizioni/7");
    const dialog = await ask();
    expect(dialog.getByText(/viene rimossa/)).toBeInTheDocument();
    await userEvent.click(dialog.getByRole("button", { name: "Sì, disdico" }));
    expect(await screen.findByRole("heading", { name: "Persone" })).toBeInTheDocument();
    expect(await screen.findByRole("status")).toHaveTextContent("Ada Lovelace disdetta e rimossa");
  });

  it("keeps the dialog open with the server's message on failure", async () => {
    serve(detailFixture(), (call) =>
      call.method === "POST"
        ? { status: 409, body: { detail: "Questa iscrizione non si può più disdire" } }
        : undefined,
    );
    renderAt("/admin/iscrizioni/7");
    const dialog = await ask();
    await userEvent.click(dialog.getByRole("button", { name: "Sì, disdico" }));
    expect(await dialog.findByRole("alert")).toHaveTextContent("non si può più disdire");
  });
});
