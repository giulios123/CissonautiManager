import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const edition = {
  id: 1,
  name: "Camp 2026",
  start_date: "2026-07-13",
  end_date: "2026-07-17",
  morning_start: "09:00:00",
  morning_end: "13:00:00",
  afternoon_start: "14:00:00",
  afternoon_end: "18:00:00",
  evening_start: "19:00:00",
  evening_end: "00:00:00",
  default_capacity: 25,
  hold_days: 3,
  waitlist_percent: 20,
  base_fee_cents: 1000,
  per_day_fee_cents: 100,
  lunch_price_cents: 800,
  dinner_price_cents: 1200,
  slots: [],
  payment_channels: [],
  privacy: null,
  disclaimer: null,
};

const confirmationPreview = {
  current_policy: "legacy_total",
  proposed_policy: "registration_fee",
  ready: true,
  already_active: false,
  preview_token: "a".repeat(64),
  eligible_count: 2,
  excluded_expired_count: 1,
  excluded_closed_count: 3,
  waitlist_only_count: 4,
  new_confirmation_count: 1,
  email_templates_to_review: [{ kind: "payment_confirmation", locale: "it" }],
  blockers: [],
  rows: [
    {
      booking_id: 17,
      name: "Ada Lovelace",
      email: "ada@example.com",
      status_before: "in_attesa_pagamento",
      status_after: "confermata",
      registration_fee_cents: 1200,
      amount_due_cents: 2500,
      paid_cents: 1200,
      balance_before_cents: 300,
      balance_after_cents: 1300,
      confirmation_balance_after_cents: 0,
      sends_confirmation: true,
    },
    {
      booking_id: 18,
      name: "Grace Hopper",
      email: "grace@example.com",
      status_before: "confermata",
      status_after: "confermata",
      registration_fee_cents: 1200,
      amount_due_cents: 2200,
      paid_cents: 2500,
      balance_before_cents: -300,
      balance_after_cents: -300,
      confirmation_balance_after_cents: 0,
      sends_confirmation: false,
    },
  ],
};

describe("settings", () => {
  it("uploads a logo, updates its preview, and restores the original", async () => {
    let logoUrl: string | null = null;
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/public/edition")
        return { body: { name: edition.name, logo_url: logoUrl, registration_open: false } };
      if (call.url === "/api/admin/edition") return { body: { ...edition, logo_url: logoUrl } };
      if (call.url === "/api/admin/edition/logo" && call.method === "PUT") {
        logoUrl = "/api/public/edition/logo?v=abc";
        return { body: { ...edition, logo_url: logoUrl } };
      }
      if (call.url === "/api/admin/edition/logo" && call.method === "DELETE") {
        logoUrl = null;
        return { body: { ...edition, logo_url: null } };
      }
      return undefined;
    });
    renderAt("/admin/impostazioni");
    const file = new File(["png bytes"], "logo.png", { type: "image/png" });
    await userEvent.upload(await screen.findByLabelText(/Immagine \(PNG/), file);
    expect(await screen.findByText("Logo aggiornato.")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Anteprima del logo di Camp 2026" })).toHaveAttribute(
      "src",
      "/api/public/edition/logo?v=abc",
    );
    expect(
      (
        calls.find((call) => call.method === "PUT" && call.body instanceof FormData)
          ?.body as FormData
      ).get("file"),
    ).toBeInstanceOf(File);

    await userEvent.click(screen.getByRole("button", { name: "Ripristina il logo originale" }));
    expect(await screen.findByText("Logo originale ripristinato.")).toBeInTheDocument();
    expect(
      calls.some((call) => call.method === "DELETE" && call.url === "/api/admin/edition/logo"),
    ).toBe(true);
  });

  it("has a section menu whose entries point at the headings of the page", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/edition" ? { body: edition } : undefined));
    renderAt("/admin/settings");
    const menu = await screen.findByRole("navigation", { name: "Impostazioni" });
    const edition_ = within(menu).getByRole("link", { name: "Edizione" });
    expect(edition_).toHaveAttribute("href", "#edition-title");
    expect(edition_).toHaveAttribute("aria-current", "location");
    expect(document.getElementById("edition-title")).toHaveTextContent("Edizione");
    await userEvent.click(within(menu).getByRole("link", { name: "Canali di pagamento" }));
    expect(within(menu).getByRole("link", { name: "Canali di pagamento" })).toHaveAttribute(
      "aria-current",
      "location",
    );
    // The email sections load their own data (not stubbed here): the others are always drawn.
    const targets = within(menu)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href")!.slice(1))
      .filter((id) => id !== "regemail-title" && id !== "emails-title");
    await waitFor(() => {
      for (const id of targets) expect(document.getElementById(id)).not.toBeNull();
    });
  });

  it("shows no section menu before the edition is saved", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/edition"
        ? { status: 404, body: { detail: "No edition" } }
        : undefined,
    );
    renderAt("/admin/settings");
    expect(await screen.findByRole("heading", { name: "Edizione", level: 2 })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Impostazioni" })).not.toBeInTheDocument();
  });

  it("edits the waitlist percentage", async () => {
    const calls = stubAdminApi((call) =>
      call.url === "/api/admin/edition" ? { body: edition } : undefined,
    );
    renderAt("/admin/impostazioni");
    const field = await screen.findByLabelText("Lista d'attesa (% dei posti)");
    expect(field).toHaveValue(20);
    await userEvent.clear(field);
    await userEvent.type(field, "30");
    await userEvent.click(screen.getByRole("button", { name: "Salva edizione" }));
    await waitFor(() =>
      expect(
        (calls.find((c) => c.method === "PUT")?.body as Record<string, unknown>).waitlist_percent,
      ).toBe(30),
    );
  });

  it("edits the meal prices", async () => {
    const calls = stubAdminApi((call) =>
      call.url === "/api/admin/edition" ? { body: edition } : undefined,
    );
    renderAt("/admin/impostazioni");
    const lunch = await screen.findByLabelText("Prezzo del pranzo (€)");
    expect(lunch).toHaveValue("8,00");
    await userEvent.clear(lunch);
    await userEvent.type(lunch, "9,50");
    await userEvent.click(screen.getByRole("button", { name: "Salva edizione" }));
    await waitFor(() => {
      const body = calls.find((c) => c.method === "PUT")?.body as Record<string, unknown>;
      expect([body.lunch_price_cents, body.dinner_price_cents]).toEqual([950, 1200]);
    });
  });

  it("offers the health consent text", async () => {
    stubAdminApi((call) => (call.url === "/api/admin/edition" ? { body: edition } : undefined));
    renderAt("/admin/impostazioni");
    expect(
      await screen.findByRole("heading", { name: /Consenso per allergie e intolleranze/ }),
    ).toBeInTheDocument();
  });

  it("publishes optional consent text in Italian and English as one version", async () => {
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/legal-documents")
        return {
          body: {
            id: 5,
            kind: "attendance",
            version: 1,
            body: "Presenza IT",
            body_it: "Presenza IT",
            body_en: "Attendance EN",
            is_legacy: false,
          },
        };
      return undefined;
    });
    renderAt("/admin/impostazioni");
    const heading = await screen.findByRole("heading", {
      name: "Visibilità della presenza nell'area riservata",
    });
    const form = heading.closest("form");
    expect(form).not.toBeNull();
    const section = within(form as HTMLFormElement);
    await userEvent.type(section.getByLabelText("Testo italiano"), "Presenza IT");
    await userEvent.type(section.getByLabelText("Testo inglese"), "Attendance EN");
    await userEvent.click(section.getByRole("button", { name: "Pubblica nuova versione" }));

    await waitFor(() => {
      const request = calls.find((call) => call.url === "/api/admin/legal-documents");
      expect(request?.body).toEqual({
        kind: "attendance",
        body_it: "Presenza IT",
        body_en: "Attendance EN",
      });
    });
  });

  it("previews the legacy transition and lets the admin cancel without applying it", async () => {
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/edition/confirmation-policy/preview")
        return { body: confirmationPreview };
      return undefined;
    });
    renderAt("/admin/impostazioni");

    expect(await screen.findByText("da verificare con l'anteprima")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Calcola l'anteprima" }));

    expect(await screen.findByText("la conferma richiede il totale dovuto")).toBeInTheDocument();
    expect(screen.getByText("Email di conferma previste: 1")).toBeInTheDocument();
    expect(screen.getByText("Testi email personalizzati da controllare")).toBeInTheDocument();
    expect(screen.getByText(/prima di applicarla/)).toHaveTextContent(/nuova anteprima/);
    expect(screen.getByText("Conferma pagamento (Italiano)")).toBeInTheDocument();
    expect(screen.getByText("In attesa di pagamento")).toBeInTheDocument();
    expect(screen.getAllByText("Confermata")).toHaveLength(3);
    expect(screen.getAllByText("credito di 3,00 €")).toHaveLength(2);
    expect(screen.getByText("Saldo/credito dopo")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Annulla anteprima" }));
    expect(
      screen.queryByRole("table", { name: "Ricalcolo proposto per ogni iscrizione attiva" }),
    ).not.toBeInTheDocument();
    expect(calls.some((call) => call.url.endsWith("/activate"))).toBe(false);
  });

  it("applies a valid preview once and reports the transition", async () => {
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/edition/confirmation-policy/preview")
        return { body: confirmationPreview };
      if (call.url === "/api/admin/edition/confirmation-policy/activate")
        return {
          body: {
            already_applied: false,
            activated_at: "2026-11-07T10:00:00Z",
            updated_bookings: 2,
            new_confirmations: 1,
            transferred_notices: 1,
          },
        };
      return undefined;
    });
    renderAt("/admin/settings");

    await userEvent.click(await screen.findByRole("button", { name: "Calcola l'anteprima" }));
    const apply = await screen.findByRole("button", { name: "Applica la nuova regola" });
    await userEvent.dblClick(apply);

    await screen.findByText(/Regola attivata: 2 iscrizioni aggiornate/);
    const activationCalls = calls.filter(
      (call) => call.url === "/api/admin/edition/confirmation-policy/activate",
    );
    expect(activationCalls).toHaveLength(1);
    expect(activationCalls[0].body).toEqual({ preview_token: "a".repeat(64) });
    expect(
      screen.getByText("La nuova regola è già attiva per questa edizione."),
    ).toBeInTheDocument();
  });

  it("discards a stale preview and requires a fresh one", async () => {
    let previews = 0;
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/edition") return { body: edition };
      if (call.url === "/api/admin/edition/confirmation-policy/preview") {
        previews += 1;
        return { body: confirmationPreview };
      }
      if (call.url === "/api/admin/edition/confirmation-policy/activate")
        return {
          status: 409,
          body: { detail: "I dati sono cambiati. Ricarica l'anteprima prima di applicare." },
        };
      return undefined;
    });
    renderAt("/admin/impostazioni");

    await userEvent.click(await screen.findByRole("button", { name: "Calcola l'anteprima" }));
    await userEvent.click(await screen.findByRole("button", { name: "Applica la nuova regola" }));

    expect(
      await screen.findByText("I dati sono cambiati. Ricarica l'anteprima prima di applicare."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Calcola l'anteprima" }));
    await screen.findByRole("table");
    expect(previews).toBe(2);
    expect(calls.filter((call) => call.url.endsWith("/activate"))).toHaveLength(1);
  });
});
