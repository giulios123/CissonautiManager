import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const texts = {
  placeholders: ["{nome}", "{evento}"],
  registration_intro: { stored: null, default: "Scegli i momenti in cui vuoi venire." },
  emails: [
    {
      kind: "registration",
      label: "Iscrizione",
      automatic: "I slot scelti, la quota e il link.",
      defaults: {
        subject: "Iscrizione a {evento}",
        intro: "Ciao {nome},\n\ngrazie!",
        closing: "",
      },
      stored: { subject: null, intro: null, closing: null },
    },
    {
      kind: "cancellation",
      label: "Disdetta",
      automatic: "Cosa succede ai pagamenti.",
      defaults: { subject: "Disdetta a {evento}", intro: "Ciao {nome}", closing: "" },
      stored: { subject: "Addio", intro: null, closing: null },
    },
  ],
};

function handler(call: Call) {
  if (call.url === "/api/admin/email-texts" && call.method === "GET") return { body: texts };
  if (call.url.startsWith("/api/admin/email-texts/")) {
    const kind = call.url.split("/").pop();
    const email = texts.emails.find((e) => e.kind === kind)!;
    const sent = call.body as {
      subject: string | null;
      intro: string | null;
      closing: string | null;
    };
    return { body: { ...email, stored: sent } };
  }
  if (call.url === "/api/admin/registration-intro") {
    const sent = (call.body as { text: string | null }).text;
    return { body: { stored: sent, default: texts.registration_intro.default } };
  }
  return undefined;
}

describe("texts page", () => {
  it("shows the defaults, the stored values and what stays automatic", async () => {
    stubAdminApi(handler);
    renderAt("/admin/testi");
    expect(await screen.findByRole("heading", { name: "Testi" })).toBeInTheDocument();
    expect(screen.getByLabelText("Testo sopra il modulo")).toHaveValue(
      "Scegli i momenti in cui vuoi venire.",
    );
    const registration = screen.getByRole("form", { name: "Email «Iscrizione»" });
    expect(within(registration).getByLabelText("Oggetto")).toHaveValue("Iscrizione a {evento}");
    expect(
      within(registration).getByText("I slot scelti, la quota e il link."),
    ).toBeInTheDocument();
    const cancellation = screen.getByRole("form", { name: "Email «Disdetta»" });
    expect(within(cancellation).getByLabelText("Oggetto")).toHaveValue("Addio");
  });

  it("saves the paragraph above the form", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/testi");
    const field = await screen.findByLabelText("Testo sopra il modulo");
    await userEvent.clear(field);
    await userEvent.type(field, "Ciao a tutti");
    await userEvent.click(screen.getByRole("button", { name: "Salva il testo" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Testo salvato.");
    expect(calls.find((c) => c.url === "/api/admin/registration-intro")?.body).toEqual({
      text: "Ciao a tutti",
    });
  });

  it("restores the default paragraph", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/testi");
    await screen.findByLabelText("Testo sopra il modulo");
    await userEvent.click(screen.getByRole("button", { name: "Ripristina il predefinito" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Ripristinato");
    expect(calls.find((c) => c.url === "/api/admin/registration-intro")?.body).toEqual({
      text: null,
    });
  });

  it("saves the three parts of an email", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/testi");
    const form = await screen.findByRole("form", { name: "Email «Iscrizione»" });
    const subject = within(form).getByLabelText("Oggetto");
    fireEvent.change(subject, { target: { value: "Benvenuto a {evento}" } });
    await userEvent.type(within(form).getByLabelText("Testo dopo i dati"), "A presto!");
    await userEvent.click(within(form).getByRole("button", { name: "Salva" }));
    expect(await within(form).findByRole("status")).toHaveTextContent("Testo salvato.");
    expect(calls.find((c) => c.url === "/api/admin/email-texts/registration")?.body).toEqual({
      subject: "Benvenuto a {evento}",
      intro: "Ciao {nome},\n\ngrazie!",
      closing: "A presto!",
    });
  });

  it("restores the default texts of an email", async () => {
    const calls = stubAdminApi(handler);
    renderAt("/admin/testi");
    const form = await screen.findByRole("form", { name: "Email «Disdetta»" });
    await userEvent.click(within(form).getByRole("button", { name: "Ripristina i predefiniti" }));
    await waitFor(() =>
      expect(within(form).getByLabelText("Oggetto")).toHaveValue("Disdetta a {evento}"),
    );
    expect(calls.find((c) => c.url === "/api/admin/email-texts/cancellation")?.body).toEqual({
      subject: null,
      intro: null,
      closing: null,
    });
  });

  it("shows the server error next to the email", async () => {
    stubAdminApi((call) =>
      call.method === "PUT"
        ? { status: 422, body: { detail: "L'oggetto può avere al massimo 200 caratteri" } }
        : handler(call),
    );
    renderAt("/admin/testi");
    const form = await screen.findByRole("form", { name: "Email «Iscrizione»" });
    await userEvent.click(within(form).getByRole("button", { name: "Salva" }));
    expect(await within(form).findByRole("alert")).toHaveTextContent("al massimo 200");
  });

  it("asks to save the edition first when there is none", async () => {
    stubAdminApi((call) =>
      call.url === "/api/admin/email-texts" ? { status: 404, body: { detail: "x" } } : undefined,
    );
    renderAt("/admin/testi");
    expect(await screen.findByText(/Salva prima l'edizione/)).toBeInTheDocument();
  });

  it("is reachable from the admin menu, with a way back to the personal page", async () => {
    stubAdminApi(handler);
    renderAt("/admin/testi");
    const nav = await screen.findByRole("navigation", { name: "Pannello organizzatori" });
    expect(within(nav).getByRole("link", { name: "Testi" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(nav).getByRole("link", { name: "La mia pagina" })).toHaveAttribute("href", "/io");
  });
});
