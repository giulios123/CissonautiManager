import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const edition = { start_date: "2026-07-13", end_date: "2026-07-14" };
const hike = {
  id: 3,
  title: "Escursione",
  description: "Sul monte",
  title_it: "Escursione",
  title_en: "Hike",
  description_it: "Sul monte",
  description_en: "On the mountain",
  translation_missing: false,
  date: "2026-07-14",
  period: "morning",
  time_label: "9:30-12",
  start_time: "09:30",
  end_time: "12:00",
  price_cents: 1500,
  capacity: 2,
  joined: 1,
  free: 1,
};

describe("activities admin page", () => {
  it("lists activities and creates a new one", async () => {
    let list: unknown[] = [hike];
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/activities" && call.method === "GET") return { body: list };
      if (call.url === "/api/admin/activities" && call.method === "POST") {
        list = [...list, { ...hike, id: 4, title: "Yoga", joined: 0 }];
        return { status: 201, body: list[1] };
      }
      return undefined;
    });
    renderAt("/admin/activities");
    const row = (await screen.findByRole("link", { name: "Escursione" })).closest(
      "tr",
    ) as HTMLElement;
    expect(screen.getByRole("table", { name: "Attività dell'edizione" })).toBeInTheDocument();
    expect(within(row).getByText("15,00 €")).toBeInTheDocument();
    expect(within(row).getByText("1 / 2")).toBeInTheDocument();
    expect(within(row).getByRole("button", { name: "Elimina" })).toBeDisabled();

    const form = within(screen.getByRole("form", { name: "Nuova attività" }));
    await userEvent.type(form.getByLabelText("Titolo · IT"), "Yoga");
    await userEvent.type(form.getByLabelText("Titolo · EN"), "Yoga");
    await userEvent.type(form.getByLabelText("Descrizione · IT"), "Una pratica guidata");
    await userEvent.type(form.getByLabelText("Descrizione · EN"), "A guided practice");
    await userEvent.selectOptions(form.getByLabelText("Fascia"), "evening");
    await userEvent.clear(form.getByLabelText(/Prezzo/));
    await userEvent.type(form.getByLabelText(/Prezzo/), "5");
    await userEvent.click(form.getByRole("button", { name: "Crea l'attività" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Attività creata.");
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({
      title: "Yoga",
      title_it: "Yoga",
      title_en: "Yoga",
      description: "Una pratica guidata",
      description_it: "Una pratica guidata",
      description_en: "A guided practice",
      date: "2026-07-13",
      period: "evening",
      start_time: "19:00",
      end_time: "00:00",
      payment_mode: "organizer",
      payment_instructions: null,
      price_cents: 500,
      capacity: null,
      request_key: expect.any(String),
    });
    expect(await screen.findByRole("link", { name: "Yoga" })).toBeInTheDocument();
  });

  it("shows the server refusal when editing", async () => {
    stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/activities") return { body: [hike] };
      if (call.url === "/api/admin/activities/3" && call.method === "PATCH")
        return {
          status: 409,
          body: { detail: "Con persone già iscritte non si cambiano prezzo, giorno e fascia" },
        };
      return undefined;
    });
    renderAt("/admin/activities");
    await userEvent.click(await screen.findByRole("button", { name: "Modifica" }));
    const form = within(screen.getByRole("form", { name: "Modifica «Escursione»" }));
    expect(form.getByText(/Ci sono già iscritti/)).toBeInTheDocument();
    await userEvent.click(form.getByRole("button", { name: "Salva le modifiche" }));
    await waitFor(() =>
      expect(form.getByRole("alert")).toHaveTextContent("Con persone già iscritte"),
    );
  });
});

describe("activity detail page", () => {
  it("lists the people with a CSV download", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/activities/3"
        ? {
            body: {
              ...hike,
              people: [
                {
                  booking_id: 7,
                  first_name: "Ada",
                  last_name: "Lovelace",
                  email: "ada@example.com",
                  phone: "+39 333",
                  status: "confermata",
                },
              ],
            },
          }
        : undefined,
    );
    renderAt("/admin/activities/3");
    expect(await screen.findByRole("heading", { name: "Escursione" })).toBeInTheDocument();
    expect(screen.getByText(/1 \/ 2, 1 posto libero/)).toBeInTheDocument();
    const row = screen.getByRole("link", { name: "Ada Lovelace" }).closest("tr") as HTMLElement;
    expect(within(row).getByText("Confermata")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/activities/3?format=csv&lang=it",
    );
  });
});

describe("contributions view", () => {
  it("filters by kind and flags inactive registrations", async () => {
    const rows = [
      {
        id: 1,
        kind: "talk",
        title: "Macchine",
        description: "Venti minuti",
        booking_id: 7,
        first_name: "Ada",
        last_name: "Lovelace",
        status: "confermata",
        active: true,
        activities: [],
      },
      {
        id: 2,
        kind: "talk",
        title: "Vecchio talk",
        description: null,
        booking_id: 8,
        first_name: "Bob",
        last_name: "Rossi",
        status: "scaduta",
        active: false,
        activities: [],
      },
    ];
    const calls = stubAdminApi((call) =>
      call.url.startsWith("/api/admin/views/contributions") ? { body: rows } : undefined,
    );
    renderAt("/admin/contributi");
    const old = (await screen.findByText("Vecchio talk")).closest("tr") as HTMLElement;
    expect(screen.getByRole("table", { name: "Contributi offerti" })).toBeInTheDocument();
    expect(within(old).getByText("iscrizione scaduta")).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Tipo"), "talk");
    await waitFor(() =>
      expect(calls.some((c) => c.url === "/api/admin/views/contributions?kind=talk")).toBe(true),
    );
    expect(screen.getByRole("link", { name: "Scarica CSV" })).toHaveAttribute(
      "href",
      "/api/admin/views/contributions?kind=talk&format=csv&lang=it",
    );
  });
});
