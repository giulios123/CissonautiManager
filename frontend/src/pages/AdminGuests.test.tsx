import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const anna = {
  id: 4,
  first_name: "Anna",
  last_name: "Rossi",
  payer: "paying",
  phone: "333",
  reference: "con Maria",
  internal_note: null,
  diet: "vegan",
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
const mealsView = {
  days: [
    {
      date: "2026-07-13",
      meals: [
        { kind: "lunch", price_cents: 800, payment_mode: "organizer", count: 1, people: [] },
        { kind: "dinner", price_cents: 1200, payment_mode: "organizer", count: 0, people: [] },
      ],
    },
  ],
};
const hike = {
  id: 3,
  title: "Escursione",
  description: null,
  date: "2026-07-13",
  period: "morning",
  time_label: null,
  price_cents: 0,
  capacity: 1,
  joined: 1,
  free: 0,
};

describe("guests list", () => {
  it("lists the guests and creates a new one", async () => {
    let list: unknown[] = [anna];
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/guests" && call.method === "GET") return { body: list };
      if (call.url === "/api/admin/guests" && call.method === "POST") {
        list = [...list, { ...anna, id: 5, first_name: "Luca", last_name: "Bianchi" }];
        return { status: 201, body: list[1] };
      }
      return undefined;
    });
    renderAt("/admin/guests");
    const row = (await screen.findByRole("rowheader", { name: /Anna Rossi/ })).closest(
      "tr",
    ) as HTMLElement;
    expect(within(row).getByText("con Maria")).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "Anna Rossi" })).toHaveAttribute(
      "href",
      "/admin/guests/4",
    );
    expect(document.title).toBe("Esterni · Cissonauti Summer Camp");

    await userEvent.type(screen.getByLabelText("Nome"), "Luca");
    await userEvent.type(screen.getByLabelText("Cognome"), "Bianchi");
    await userEvent.click(screen.getByRole("button", { name: "Aggiungi" }));
    await screen.findByRole("link", { name: "Luca Bianchi" });
    const post = calls.find((c) => c.method === "POST");
    expect(post?.body).toMatchObject({ first_name: "Luca", last_name: "Bianchi", payer: "paying" });
    expect(post?.body).not.toHaveProperty("confirm_duplicate");
    // The form is empty again for the next guest.
    expect(screen.getByLabelText("Nome")).toHaveValue("");
  });

  it("asks before saving someone with the same name", async () => {
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/guests" && call.method === "GET") return { body: [anna] };
      if (call.url === "/api/admin/guests" && call.method === "POST") {
        const body = call.body as { confirm_duplicate?: boolean };
        return body.confirm_duplicate
          ? { status: 201, body: anna }
          : { status: 409, body: { detail: "C'è già una persona con questo nome: Anna Rossi." } };
      }
      return undefined;
    });
    renderAt("/admin/guests");
    await screen.findByRole("link", { name: "Anna Rossi" });
    await userEvent.type(screen.getByLabelText("Nome"), "Anna");
    await userEvent.type(screen.getByLabelText("Cognome"), "Rossi");
    await userEvent.click(screen.getByRole("button", { name: "Aggiungi" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/C'è già una persona/)).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole("button", { name: "Salva comunque" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    const posts = calls.filter((c) => c.method === "POST");
    expect(posts).toHaveLength(2);
    expect(posts[1].body).toMatchObject({ confirm_duplicate: true });
  });

  it("shows the allergy field only with the collected consent", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/guests" && call.method === "GET" ? { body: [] } : undefined,
    );
    renderAt("/admin/guests");
    await screen.findByText("Nessun esterno inserito.");
    expect(screen.queryByLabelText("Allergie e intolleranze")).not.toBeInTheDocument();
    await userEvent.click(screen.getByLabelText(/Ho raccolto il consenso/));
    expect(screen.getByLabelText("Allergie e intolleranze")).toBeInTheDocument();
  });
});

describe("guest page", () => {
  function serve(extra?: (call: Call) => { status?: number; body: unknown } | undefined) {
    return stubAdminApi((call) => {
      const special = extra?.(call);
      if (special) return special;
      if (call.url === "/api/admin/guests/4" && call.method === "GET") return { body: anna };
      if (call.url === "/api/admin/views/meals") return { body: mealsView };
      if (call.url === "/api/admin/activities") return { body: [hike] };
      return undefined;
    });
  }

  it("saves the meals of the guest without asking for any presence", async () => {
    const calls = serve((call) =>
      call.url === "/api/admin/guests/4/meals"
        ? {
            body: {
              ...anna,
              meals: [
                { date: "2026-07-13", kind: "lunch" },
                { date: "2026-07-13", kind: "dinner" },
              ],
            },
          }
        : undefined,
    );
    renderAt("/admin/guests/4");
    await screen.findByRole("heading", { name: /Anna Rossi/ });
    expect(screen.getByRole("checkbox", { name: /Pranzo/ })).toBeChecked();
    await userEvent.click(screen.getByRole("checkbox", { name: /Cena/ }));
    await userEvent.click(screen.getByRole("button", { name: "Salva pasti" }));
    await screen.findAllByText("Salvato.");
    expect(calls.find((c) => c.method === "PUT")?.body).toEqual({
      meals: [
        { date: "2026-07-13", kind: "lunch" },
        { date: "2026-07-13", kind: "dinner" },
      ],
    });
  });

  it("offers to force a full activity and shows the warning", async () => {
    const calls = serve((call) => {
      if (call.url !== "/api/admin/guests/4/activities") return undefined;
      const body = call.body as { force: boolean };
      return body.force
        ? {
            body: {
              ...anna,
              activities: [{ id: 3, title: "Escursione", date: "2026-07-13", period: "morning" }],
              warning: "Attenzione: capienza superata in Escursione.",
            },
          }
        : { status: 409, body: { detail: "Attività al completo: Escursione." } };
    });
    renderAt("/admin/guests/4");
    await screen.findByRole("heading", { name: /Anna Rossi/ });
    await userEvent.click(screen.getByRole("checkbox", { name: /Escursione/ }));
    await userEvent.click(screen.getByRole("button", { name: "Salva attività" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("al completo");
    await userEvent.click(screen.getByRole("checkbox", { name: "Forza oltre la capienza" }));
    await userEvent.click(screen.getByRole("button", { name: "Salva attività" }));
    expect(await screen.findByText(/capienza superata/)).toBeInTheDocument();
    const puts = calls.filter((c) => c.method === "PUT" && c.url.endsWith("/activities"));
    expect(puts.map((c) => c.body)).toEqual([
      { activity_ids: [3], force: false },
      { activity_ids: [3], force: true },
    ]);
  });

  it("deletes the guest after a confirmation and goes back to the list", async () => {
    const calls = serve((call) =>
      call.url === "/api/admin/guests/4" && call.method === "DELETE"
        ? { status: 204, body: null }
        : call.url === "/api/admin/guests" && call.method === "GET"
          ? { body: [] }
          : undefined,
    );
    renderAt("/admin/guests/4");
    await screen.findByRole("heading", { name: /Anna Rossi/ });
    await userEvent.click(screen.getByRole("button", { name: "Elimina esterno" }));
    const dialog = await screen.findByRole("dialog");
    expect(calls.some((c) => c.method === "DELETE")).toBe(false);
    await userEvent.click(within(dialog).getByRole("button", { name: "Elimina" }));
    await screen.findByText("Nessun esterno inserito.");
    expect(calls.some((c) => c.method === "DELETE")).toBe(true);
  });

  it("says when the guest does not exist", async () => {
    stubAdminApi(() => undefined);
    renderAt("/admin/guests/99");
    expect(await screen.findByRole("alert")).toHaveTextContent("Esterno non trovato.");
  });
});

describe("guests in the other views", () => {
  it("meals view labels a guest and links to the guest page", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/views/meals"
        ? {
            body: {
              days: [
                {
                  date: "2026-07-13",
                  meals: [
                    {
                      kind: "lunch",
                      count: 2,
                      diets: { omnivore: 0, vegetarian: 0, vegan: 1, none: 1 },
                      people: [
                        {
                          booking_id: 7,
                          guest_id: null,
                          external: false,
                          first_name: "Ada",
                          last_name: "Lovelace",
                          diet: null,
                          allergies: null,
                          collectable_cents: 800,
                        },
                        {
                          booking_id: null,
                          guest_id: 4,
                          external: true,
                          first_name: "Anna",
                          last_name: "Rossi",
                          diet: "vegan",
                          allergies: "noci",
                          collectable_cents: 0,
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          }
        : undefined,
    );
    renderAt("/admin/meals");
    const lunch = (await screen.findByRole("rowheader", { name: "Pranzo" })).closest(
      "tr",
    ) as HTMLElement;
    expect(within(lunch).getByRole("link", { name: "Anna Rossi" })).toHaveAttribute(
      "href",
      "/admin/guests/4",
    );
    expect(within(lunch).getByRole("link", { name: "Ada Lovelace" })).toHaveAttribute(
      "href",
      "/admin/registrations/7",
    );
    expect(within(lunch).getByText(/Esterno/)).toBeInTheDocument();
    expect(within(lunch).getByText("Anna Rossi: noci")).toBeInTheDocument();
  });

  it("activity page lists the guests apart from the participants", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/activities/3"
        ? {
            body: {
              ...hike,
              people: [],
              guests: [
                {
                  guest_id: 4,
                  first_name: "Anna",
                  last_name: "Rossi",
                  phone: "333",
                  payer: "paying",
                },
              ],
              note_history: [],
              internal_note: null,
              payment_mode: "organizer",
            },
          }
        : undefined,
    );
    renderAt("/admin/activities/3");
    const table = await screen.findByRole("table", { name: "Esterni iscritti" });
    expect(within(table).getByRole("link", { name: "Anna Rossi" })).toHaveAttribute(
      "href",
      "/admin/guests/4",
    );
    expect(screen.queryByText("Nessun iscritto per ora.")).not.toBeInTheDocument();
  });

  it("is reachable from the admin menu", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/guests" ? { body: [] } : undefined));
    renderAt("/admin/guests");
    const nav = await screen.findByRole("navigation", { name: "Pannello organizzatori" });
    expect(within(nav).getByRole("link", { name: "Esterni" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});
