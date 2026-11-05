import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, vi } from "vitest";
import { App } from "../App";
import { UNDO_WINDOW_MS } from "./AdminCollect";

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

const row = (id: number, first: string, last: string, code: string, balance = 1100) => ({
  booking_id: id,
  first_name: first,
  last_name: last,
  email: `${first.toLowerCase()}@example.com`,
  personal_code: code,
  status: "in_attesa_pagamento",
  amount_due_cents: balance,
  paid_cents: 0,
  balance_cents: balance,
  hold_expires_at: "2026-11-08T15:44:00Z",
});

const ADA = row(7, "Ada", "Lovelace", "CSC-GGSU");
const GRACE = row(8, "Grace", "Hopper", "CSC-G8AX", 1900);

type Call = { url: string; method: string; body: unknown };
let calls: Call[];
let listing: ReturnType<typeof row>[];
let failPayment: boolean;

// The booking lists a higher payment id than the one just created, as if another admin had paid
// the same booking: undo must use the id the server returned, not the highest one.
function detail(payments: { id: number; voided: boolean }[], warning: string | null = null) {
  return {
    booking: { payments: [...payments, { id: 99, voided: false }] },
    warning,
    payment_id: 41,
  };
}

beforeEach(() => {
  calls = [];
  listing = [ADA, GRACE];
  failPayment = false;
  window.localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      if (url === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
      if (url === "/api/admin/views/to-collect")
        return new Response(JSON.stringify(listing), { status: 200 });
      if (url.endsWith("/payments") && method === "POST") {
        if (failPayment)
          return new Response(JSON.stringify({ detail: "Prenotazione non trovata" }), {
            status: 404,
          });
        return new Response(JSON.stringify(detail([{ id: 41, voided: false }])), { status: 201 });
      }
      if (url.endsWith("/void"))
        return new Response(JSON.stringify(detail([{ id: 41, voided: true }])), { status: 200 });
      return new Response("{}", { status: 404 });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/admin/da-incassare"]}>
      <App />
    </MemoryRouter>,
  );
}

const posted = () => calls.filter((c) => c.method === "POST");

describe("to collect view", () => {
  it("lists the people with their causale, balance and a link to the record", async () => {
    renderPage();
    expect(await screen.findByText("CSC-GGSU")).toBeInTheDocument();
    expect(screen.getByText("2 da incassare")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ada Lovelace" })).toHaveAttribute(
      "href",
      "/admin/iscrizioni/7",
    );
    expect(screen.getAllByRole("link", { name: "Altro importo" })).toHaveLength(2);
  });

  it("says so when there is nothing to collect", async () => {
    listing = [];
    renderPage();
    expect(await screen.findByText("Nessun pagamento da incassare.")).toBeInTheDocument();
  });

  it("tells the admin when the list cannot be loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url === "/api/me"
          ? new Response(JSON.stringify(admin), { status: 200 })
          : new Response("{}", { status: 500 }),
      ),
    );
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("Non riesco a caricare");
  });

  it("filters by name, email and causale, ignoring case", async () => {
    renderPage();
    const search = await screen.findByLabelText("Cerca per nome, email o causale");
    fireEvent.change(search, { target: { value: "  g8ax " } });
    expect(screen.getByText("1 da incassare")).toBeInTheDocument();
    expect(screen.queryByText("CSC-GGSU")).not.toBeInTheDocument();
    fireEvent.change(search, { target: { value: "ADA@example" } });
    expect(screen.getByText("CSC-GGSU")).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "lovelace ada" } });
    expect(screen.getByText("CSC-GGSU")).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "zzz" } });
    expect(screen.getByText("Nessun risultato.")).toBeInTheDocument();
  });

  it("remembers the channel in the browser", async () => {
    renderPage();
    const select = await screen.findByLabelText("Canale dei pagamenti che segni");
    expect(select).toHaveValue("revolut");
    fireEvent.change(select, { target: { value: "satispay" } });
    expect(window.localStorage.getItem("collect-channel")).toBe("satispay");
  });

  it("starts from the saved channel", async () => {
    window.localStorage.setItem("collect-channel", "paypal");
    renderPage();
    expect(await screen.findByLabelText("Canale dei pagamenti che segni")).toHaveValue("paypal");
  });

  it("works when the browser refuses to store anything", async () => {
    const getItem = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const setItem = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    renderPage();
    const select = await screen.findByLabelText("Canale dei pagamenti che segni");
    fireEvent.change(select, { target: { value: "iban" } });
    expect(select).toHaveValue("iban");
    getItem.mockRestore();
    setItem.mockRestore();
  });

  it("names the person on every button", async () => {
    renderPage();
    expect(
      await screen.findByRole("button", { name: "Segna pagato per Grace Hopper" }),
    ).toBeInTheDocument();
  });

  it("registers the whole balance on the chosen channel, with the email deferred", async () => {
    renderPage();
    fireEvent.change(await screen.findByLabelText("Canale dei pagamenti che segni"), {
      target: { value: "iban" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Segna pagato per Grace Hopper" }));
    expect(await screen.findByText("Pagato 19,00 €")).toBeInTheDocument();
    expect(posted()).toEqual([
      {
        url: "/api/admin/registrations/8/payments",
        method: "POST",
        body: { amount_cents: 1900, channel: "iban", defer_confirmation_email: true },
      },
    ]);
    expect(screen.getByRole("status")).toHaveTextContent("19,00 € registrato per Grace Hopper");
  });

  it("shows the warning of the server, such as an expired booking without room", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
        if (url === "/api/admin/views/to-collect")
          return new Response(JSON.stringify([ADA]), { status: 200 });
        return new Response(JSON.stringify(detail([{ id: 41, voided: false }], "Slot pieno.")), {
          status: init?.method === "POST" ? 201 : 200,
        });
      }),
    );
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Segna pagato per Ada/ }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Slot pieno."));
  });

  it("shows the error next to the row and leaves it as it was", async () => {
    failPayment = true;
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Segna pagato per Ada/ }));
    expect(await screen.findByText("Prenotazione non trovata")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Segna pagato per Ada/ })).toBeEnabled();
    expect(screen.queryByText(/^Pagato/)).not.toBeInTheDocument();
  });

  it("undoes the payment with a fixed reason and brings the row back", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Segna pagato per Ada/ }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Annulla il pagamento di Ada Lovelace" }),
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Segna pagato per Ada/ })).toBeInTheDocument(),
    );
    const voided = posted().find((c) => c.url.endsWith("/void"));
    expect(voided).toEqual({
      url: "/api/admin/registrations/7/payments/41/void",
      method: "POST",
      body: { reason: "Annullato subito dalla vista Da incassare" },
    });
    expect(screen.getByRole("status")).toHaveTextContent("Pagamento annullato per Ada Lovelace");
  });

  it("drops the row after the undo window, and no longer offers the undo", async () => {
    renderPage();
    await screen.findByText("CSC-GGSU");
    vi.useFakeTimers({ shouldAdvanceTime: true });
    fireEvent.click(screen.getByRole("button", { name: /Segna pagato per Ada/ }));
    await screen.findByText("Pagato 11,00 €");
    listing = [GRACE];
    await act(async () => {
      await vi.advanceTimersByTimeAsync(UNDO_WINDOW_MS - 1_000);
    });
    expect(screen.getByText("Pagato 11,00 €")).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_500);
    });
    await waitFor(() => expect(screen.queryByText("CSC-GGSU")).not.toBeInTheDocument());
    expect(screen.queryByRole("button", { name: /Annulla il pagamento/ })).not.toBeInTheDocument();
    expect(screen.getByText("CSC-G8AX")).toBeInTheDocument();
  });

  it("keeps each paid row until its own undo window ends", async () => {
    renderPage();
    await screen.findByText("CSC-GGSU");
    vi.useFakeTimers({ shouldAdvanceTime: true });
    fireEvent.click(screen.getByRole("button", { name: /Segna pagato per Ada/ }));
    await screen.findByText("Pagato 11,00 €");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });
    fireEvent.click(screen.getByRole("button", { name: /Segna pagato per Grace/ }));
    await screen.findByText("Pagato 19,00 €");
    // The server no longer lists either of them.
    listing = [];
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_500);
    });
    // Ada's window is over, Grace's has five more seconds: her row is still there with Annulla.
    await waitFor(() => expect(screen.queryByText("CSC-GGSU")).not.toBeInTheDocument());
    expect(screen.getByText("Pagato 19,00 €")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Annulla il pagamento di Grace/ }),
    ).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });
    await waitFor(() => expect(screen.queryByText("CSC-G8AX")).not.toBeInTheDocument());
  });
});
