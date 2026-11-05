import { screen, within } from "@testing-library/react";
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
