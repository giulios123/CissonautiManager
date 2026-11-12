import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const bottle = { id: 3, name: "Borraccia", retired: false, delivered: 1, entitled: 3 };

const row = (id: number, last: string, extra: Record<string, unknown> = {}) => ({
  participant_id: id,
  first_name: "Ada",
  last_name: last,
  booking_id: 10 + id,
  category: "ordinary",
  entitled: true,
  state: "to_deliver",
  delivery: null,
  annulled: [],
  ...extra,
});

const delivered = {
  state: "delivered",
  delivery: { id: 77, delivered_at: "2026-07-13T08:30:00Z", delivered_by: "Boss Admin" },
};

function setup(
  rows: ReturnType<typeof row>[],
  options: { benefits?: (typeof bottle)[]; fail?: string } = {},
) {
  const calls = stubAdminApi((call: Call) => {
    if (call.url === "/api/admin/deliveries/benefits") {
      return { body: options.benefits ?? [bottle] };
    }
    if (call.method === "POST") {
      if (options.fail) return { status: 422, body: { detail: options.fail } };
      return { status: 201, body: { id: 77, changed: true } };
    }
    if (call.url.startsWith("/api/admin/deliveries?")) return { body: rows };
    return undefined;
  });
  renderAt("/admin/deliveries");
  return calls;
}

const posts = (calls: Call[]) => calls.filter((c) => c.method === "POST");

describe("the deliveries page", () => {
  it("says where to add the benefits when the catalogue is empty", async () => {
    setup([], { benefits: [] });
    expect(
      await screen.findByText("Nessun benefit nel catalogo. Aggiungili in Impostazioni."),
    ).toBeInTheDocument();
  });

  it("lists the benefit with its counters and the people with their state", async () => {
    setup([row(1, "Alfa"), row(2, "Charlie", { category: "internal_non_paying", ...delivered })]);
    expect(
      await screen.findByRole("option", { name: "Borraccia (1 consegnati, 3 con diritto)" }),
    ).toBeInTheDocument();
    const alfa = (await screen.findByRole("link", { name: "Ada Alfa" })).closest("tr")!;
    expect(within(alfa).getByText("Da consegnare")).toBeInTheDocument();
    expect(within(alfa).getByText("Ordinaria")).toBeInTheDocument();
    const charlie = screen.getByRole("link", { name: "Ada Charlie" }).closest("tr")!;
    expect(within(charlie).getByText(/Consegnato il .* da Boss Admin/)).toBeInTheDocument();
    expect(within(charlie).getByText("Interno non pagante")).toBeInTheDocument();
  });

  it("marks a delivery whose person lost the entitlement, and keeps it listed", async () => {
    setup([
      row(2, "Charlie", { entitled: false, ...delivered, state: "delivered_without_entitlement" }),
    ]);
    expect(await screen.findByText("Senza diritto attuale")).toBeInTheDocument();
    expect(
      screen.getByText(/La consegna resta registrata, ma la persona non ha più diritto/),
    ).toBeInTheDocument();
  });

  it("shows the annulled deliveries with their reason", async () => {
    setup([
      row(1, "Alfa", {
        annulled: [
          {
            id: 5,
            delivered_at: "2026-07-13T08:30:00Z",
            annulled_at: "2026-07-13T09:00:00Z",
            annulled_by: "Boss Admin",
            reason: "Persona sbagliata",
          },
        ],
      }),
    ]);
    expect(
      await screen.findByText(/Annullata il .* da Boss Admin: Persona sbagliata/),
    ).toBeInTheDocument();
  });

  it("delivers with one request and reloads the list", async () => {
    // The list answers like the server: after the delivery the person is delivered.
    let done = false;
    const calls = stubAdminApi((call: Call) => {
      if (call.url === "/api/admin/deliveries/benefits") return { body: [bottle] };
      if (call.method === "POST") {
        done = true;
        return { status: 201, body: { id: 77, changed: true } };
      }
      if (call.url.startsWith("/api/admin/deliveries?")) {
        return { body: [row(1, "Alfa", done ? delivered : {})] };
      }
      return undefined;
    });
    renderAt("/admin/deliveries");
    const button = await screen.findByRole("button", { name: "Consegna «Borraccia» a Ada Alfa" });
    await userEvent.dblClick(button);
    expect(await screen.findByText("Consegna registrata.")).toBeInTheDocument();
    expect(posts(calls)).toHaveLength(1);
    expect(posts(calls)[0].body).toMatchObject({ participant_id: 1, benefit_id: 3 });
    expect(String((posts(calls)[0].body as { request_key: string }).request_key)).toMatch(
      /^[0-9a-f-]{36}$/,
    );
    expect(await screen.findByText(/Consegnato il .* da Boss Admin/)).toBeInTheDocument();
  });

  it("shows the refusal of the server", async () => {
    setup([row(1, "Alfa")], { fail: "Questa persona non ha diritto ai benefit." });
    await userEvent.click(
      await screen.findByRole("button", { name: "Consegna «Borraccia» a Ada Alfa" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Questa persona non ha diritto ai benefit.",
    );
  });

  it("annuls only with a reason, and gives the focus back to the button", async () => {
    const calls = setup([row(2, "Charlie", delivered)]);
    const button = await screen.findByRole("button", {
      name: "Annulla la consegna di «Borraccia» a Ada Charlie",
    });
    await userEvent.click(button);
    const dialog = await screen.findByRole("dialog", {
      name: "Annullare la consegna di «Borraccia» a Ada Charlie?",
    });
    const confirm = within(dialog).getByRole("button", { name: "Annulla la consegna" });
    expect(confirm).toBeDisabled();
    await userEvent.type(
      within(dialog).getByLabelText("Motivo (obbligatorio)"),
      "Persona sbagliata",
    );
    await userEvent.click(confirm);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts(calls)).toHaveLength(1);
    expect(posts(calls)[0].url).toBe("/api/admin/deliveries/77/annul");
    expect(posts(calls)[0].body).toEqual({ reason: "Persona sbagliata" });
    expect(await screen.findByText("Consegna annullata.")).toBeInTheDocument();
  });

  it("changes nothing when the annulment is dismissed", async () => {
    const calls = setup([row(2, "Charlie", delivered)]);
    const button = await screen.findByRole("button", {
      name: "Annulla la consegna di «Borraccia» a Ada Charlie",
    });
    await userEvent.click(button);
    await userEvent.click(await screen.findByRole("button", { name: "No, torno indietro" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts(calls)).toHaveLength(0);
    expect(button).toHaveFocus();
  });

  it("asks the server for the search and the filter", async () => {
    const calls = setup([row(1, "Alfa")]);
    await screen.findByRole("link", { name: "Ada Alfa" });
    await userEvent.type(screen.getByLabelText("Cerca per nome"), "alf");
    await userEvent.selectOptions(screen.getByLabelText("Mostra"), "pending");
    await waitFor(() =>
      expect(calls.some((c) => c.url.includes("q=alf") && c.url.includes("state=pending"))).toBe(
        true,
      ),
    );
    expect(screen.getByRole("link", { name: "Scarica CSV" }).getAttribute("href")).toContain(
      "benefit_id=3",
    );
  });

  it("exports the CSV with the same search and filter as the list", async () => {
    setup([row(1, "Alfa")]);
    await screen.findByRole("link", { name: "Ada Alfa" });
    await userEvent.type(screen.getByLabelText("Cerca per nome"), " alf ");
    await userEvent.selectOptions(screen.getByLabelText("Mostra"), "pending");
    await waitFor(() => {
      const href = screen.getByRole("link", { name: "Scarica CSV" }).getAttribute("href") ?? "";
      expect(href).toContain("q=alf&");
      expect(href).toContain("state=pending");
    });
  });

  it("ignores a slow answer for the benefit that is no longer selected", async () => {
    const flask = { id: 4, name: "Borsa", retired: false, delivered: 0, entitled: 3 };
    const calls = stubAdminApi((call: Call) => {
      if (call.url === "/api/admin/deliveries/benefits") return { body: [bottle, flask] };
      if (call.url.includes("benefit_id=4")) return { body: [row(2, "Bravo")] };
      if (call.url.startsWith("/api/admin/deliveries?")) return { body: [row(1, "Alfa")] };
      return undefined;
    });
    // Hold back the answer for the first benefit until the second one has been shown.
    const real = globalThis.fetch;
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    let held = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url.includes("benefit_id=3") && !held) {
          held = true;
          const response = await real(url, init);
          await gate;
          return response;
        }
        return real(url, init);
      }),
    );
    renderAt("/admin/deliveries");
    await screen.findByLabelText("Benefit");
    await waitFor(() => expect(held).toBe(true));
    await userEvent.selectOptions(screen.getByLabelText("Benefit"), "4");
    expect(await screen.findByRole("link", { name: "Ada Bravo" })).toBeInTheDocument();
    release();
    await waitFor(() => expect(calls.length).toBeGreaterThan(3));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByRole("link", { name: "Ada Alfa" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ada Bravo" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Consegna «Borsa» a Ada Bravo" }),
    ).toBeInTheDocument();
  });

  it("does not offer to deliver a retired benefit", async () => {
    setup([row(1, "Alfa")], { benefits: [{ ...bottle, retired: true }] });
    expect(
      await screen.findByRole("button", { name: "Consegna «Borraccia» a Ada Alfa" }),
    ).toBeDisabled();
  });
});
