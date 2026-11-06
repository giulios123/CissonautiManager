import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const email = (subject: string, body: string) => ({
  templates: { it: { subject: "", body: "" }, en: { subject, body } },
  defaults: {
    it: { subject: "Disdetta al {event}", body: "Ciao {first_name},\n\nabbiamo registrato" },
    en: { subject: "Cancellation for {event}", body: "Hi {first_name},\n\nwe have recorded" },
  },
});

const texts = {
  emails: {
    cancellation: email("Bye", "Hi {first_name}"),
    magic_link: email("", ""),
  },
  form_intro: {
    it: "",
    en: "Welcome",
    defaults: { it: "Scegli i momenti.", en: "Choose when you want to come." },
  },
};

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

function handler(call: Call) {
  if (call.url === "/api/admin/edition") return { body: edition };
  if (call.url === "/api/admin/email/texts") return { body: texts };
  if (call.url.startsWith("/api/admin/email/texts/")) {
    const kind = call.url.split("/").pop() as keyof typeof texts.emails;
    const sent = (call.body as { templates: Record<string, unknown> }).templates;
    return {
      body: {
        ...texts,
        emails: { ...texts.emails, [kind]: { ...texts.emails[kind], templates: sent } },
      },
    };
  }
  if (call.url === "/api/admin/email/form-intro") {
    const sent = call.body as { it: string; en: string };
    return { body: { ...texts, form_intro: { ...texts.form_intro, ...sent } } };
  }
  return undefined;
}

describe("texts of the other emails and of the form", () => {
  it("shows the defaults as placeholders, the saved text and what stays automatic", async () => {
    stubAdminApi(handler);
    renderAt("/admin/settings");
    const form = await screen.findByRole("form", { name: "Email «Disdetta»" });
    expect(within(form).getByLabelText(/Oggetto/)).toHaveAttribute(
      "placeholder",
      "Disdetta al {event}",
    );
    expect(within(form).getByText(/Cosa succede ai pagamenti/)).toBeInTheDocument();
    expect(within(form).getByText("Parte automatica (non modificabile)")).toBeInTheDocument();
  });

  it("switches language and shows the other language's text", async () => {
    stubAdminApi(handler);
    renderAt("/admin/settings");
    const form = await screen.findByRole("form", { name: "Email «Disdetta»" });
    expect(within(form).getByLabelText(/Oggetto/)).toHaveValue("");
    await userEvent.click(screen.getAllByRole("button", { name: "Inglese" }).at(-1)!);
    expect(within(form).getByLabelText(/Oggetto/)).toHaveValue("Bye");
  });

  it("saves both languages of an email", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/settings");
    const form = await screen.findByRole("form", { name: "Email «Link di accesso»" });
    await userEvent.type(within(form).getByLabelText(/Oggetto/), "Entra");
    await userEvent.click(within(form).getByRole("button", { name: "Salva" }));
    expect(await within(form).findByRole("status")).toHaveTextContent("Email salvata.");
    const sent = calls.find((c) => c.url === "/api/admin/email/texts/magic_link");
    expect(sent?.method).toBe("PUT");
    expect(sent?.body).toEqual({
      templates: { it: { subject: "Entra", body: "" }, en: { subject: "", body: "" } },
    });
  });

  it("shows the server's complaint next to the email", async () => {
    stubAdminApi((call) =>
      call.method === "PUT" && call.url.includes("/texts/")
        ? { status: 422, body: { detail: "Segnaposto sconosciuto: {x}." } }
        : handler(call),
    );
    renderAt("/admin/settings");
    const form = await screen.findByRole("form", { name: "Email «Disdetta»" });
    await userEvent.click(within(form).getByRole("button", { name: "Salva" }));
    expect(await within(form).findByRole("alert")).toHaveTextContent("Segnaposto sconosciuto");
  });

  it("saves the paragraph above the form for both languages", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/settings");
    const field = await screen.findByLabelText("Testo sopra il modulo (vuoto = testo standard)");
    await userEvent.type(field, "Ciao a tutti");
    await userEvent.click(screen.getByRole("button", { name: "Salva il testo" }));
    expect(await screen.findAllByText("Testo salvato.")).not.toHaveLength(0);
    await waitFor(() =>
      expect(calls.find((c) => c.url === "/api/admin/email/form-intro")?.body).toEqual({
        it: "Ciao a tutti",
        en: "Welcome",
      }),
    );
  });

  it("tells when the texts cannot be loaded", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/email/texts"
        ? { status: 500, body: { detail: "x" } }
        : handler(call),
    );
    renderAt("/admin/settings");
    expect(
      await screen.findByText("Non riesco a caricare i testi delle email."),
    ).toBeInTheDocument();
  });

  it("has a way back to the personal page in the admin menu", async () => {
    stubAdminApi(handler);
    renderAt("/admin/settings");
    const nav = await screen.findByRole("navigation", { name: "Pannello organizzatori" });
    expect(within(nav).getByRole("link", { name: "La mia pagina" })).toHaveAttribute("href", "/me");
  });
});
