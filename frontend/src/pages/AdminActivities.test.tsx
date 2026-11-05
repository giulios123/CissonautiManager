import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const edition = { start_date: "2026-07-13", end_date: "2026-07-14" };
const hike = {
  id: 3,
  title: "Escursione",
  description: null,
  date: "2026-07-14",
  period: "morning",
  time_label: "9:30-12",
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
    renderAt("/admin/attivita");
    const row = (await screen.findByRole("link", { name: "Escursione" })).closest(
      "tr",
    ) as HTMLElement;
    expect(within(row).getByText("15,00 €")).toBeInTheDocument();
    expect(within(row).getByText("1 / 2")).toBeInTheDocument();
    expect(within(row).getByRole("button", { name: "Elimina" })).toBeDisabled();

    const form = within(screen.getByRole("form", { name: "Nuova attività" }));
    await userEvent.type(form.getByLabelText("Titolo"), "Yoga");
    await userEvent.selectOptions(form.getByLabelText("Fascia"), "evening");
    await userEvent.clear(form.getByLabelText(/Prezzo/));
    await userEvent.type(form.getByLabelText(/Prezzo/), "5");
    await userEvent.click(form.getByRole("button", { name: "Crea l'attività" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Attività creata.");
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({
      title: "Yoga",
      description: null,
      date: "2026-07-13",
      period: "evening",
      time_label: null,
      price_cents: 500,
      capacity: null,
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
    renderAt("/admin/attivita");
    await userEvent.click(await screen.findByRole("button", { name: "Modifica" }));
    const form = within(screen.getByRole("form", { name: "Modifica «Escursione»" }));
    expect(form.getByText(/Ci sono già iscritti/)).toBeInTheDocument();
    await userEvent.click(form.getByRole("button", { name: "Salva le modifiche" }));
    await waitFor(() =>
      expect(form.getByRole("alert")).toHaveTextContent("Con persone già iscritte"),
    );
  });
});
