import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { I18nProvider } from "../i18n";
import { adminMe } from "../test-utils";

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

function settings(overrides: Record<string, unknown> = {}) {
  return {
    templates: {
      it: { subject: "", body: "" },
      en: { subject: "Welcome!", body: "Hi {first_name}" },
    },
    defaults: {
      it: {
        subject: "Iscrizione al {event}",
        body: "Ciao {first_name}",
        card_text: "Sono {first_name}",
      },
      en: {
        subject: "Registration for {event}",
        body: "Hi {first_name}",
        card_text: "I'm {first_name}",
      },
    },
    card: {
      has_image: false,
      text_it: "",
      text_en: "",
      text_color: "#ffffff",
      text_position: "bottom",
    },
    ...overrides,
  };
}

type Call = { method: string; url: string; body?: unknown; isForm?: boolean; language?: string };

function stub(
  state: { current: ReturnType<typeof settings> },
  onCall?: (call: Call) => Response | undefined,
) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call: Call = {
        method: init?.method ?? "GET",
        url,
        isForm: init?.body instanceof FormData,
        body:
          init?.body && !(init.body instanceof FormData)
            ? JSON.parse(String(init.body))
            : init?.body,
        language: ((init?.headers ?? {}) as Record<string, string>)["Accept-Language"],
      };
      calls.push(call);
      const custom = onCall?.(call);
      if (custom) return custom;
      if (url === "/api/me") return new Response(JSON.stringify(adminMe), { status: 200 });
      if (url === "/api/admin/edition")
        return new Response(JSON.stringify(edition), { status: 200 });
      if (url === "/api/admin/email/registration" && call.method === "GET")
        return new Response(JSON.stringify(state.current), { status: 200 });
      if (url === "/api/admin/email/registration" && call.method === "PUT") {
        const body = call.body as { templates: unknown; card: Record<string, unknown> };
        state.current = settings({
          templates: body.templates,
          card: { ...state.current.card, ...body.card },
        });
        return new Response(JSON.stringify(state.current), { status: 200 });
      }
      return new Response("{}", { status: 200 });
    }),
  );
  return calls;
}

function renderPage(locale: "it" | "en" = "en") {
  render(
    <I18nProvider locale={locale}>
      <MemoryRouter initialEntries={["/admin/settings"]}>
        <App />
      </MemoryRouter>
    </I18nProvider>,
  );
}

async function open(locale: "it" | "en" = "en") {
  renderPage(locale);
  return screen.findByRole("form", {
    name: locale === "en" ? "Registration email" : "Email di iscrizione",
  });
}

describe("registration email settings", () => {
  it("shows the texts of the first language and the standard wording as placeholders", async () => {
    stub({ current: settings() });
    const form = await open();
    expect(within(form).getByLabelText(/Subject/)).toHaveValue("");
    expect(within(form).getByLabelText(/Subject/)).toHaveAttribute(
      "placeholder",
      "Iscrizione al {event}",
    );
    expect(within(form).getByLabelText(/Opening text/)).toHaveAttribute(
      "placeholder",
      "Ciao {first_name}",
    );
  });

  it("switches language and shows the other language's text", async () => {
    stub({ current: settings() });
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "English" }));
    expect(within(form).getByLabelText(/Subject/)).toHaveValue("Welcome!");
    expect(within(form).getByLabelText(/Opening text/)).toHaveValue("Hi {first_name}");
    expect(within(form).getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("inserts a placeholder where the cursor is", async () => {
    stub({ current: settings() });
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "English" }));
    const body = within(form).getByLabelText(/Opening text/) as HTMLTextAreaElement;
    await userEvent.clear(body);
    await userEvent.type(body, "Hello , welcome");
    body.setSelectionRange(6, 6);
    body.dispatchEvent(new Event("select", { bubbles: true }));
    await userEvent.click(within(form).getByRole("button", { name: "Insert First name" }));
    expect(body).toHaveValue("Hello {first_name}, welcome");
  });

  it("inserts into the subject when it was the last field used", async () => {
    stub({ current: settings() });
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "English" }));
    const subject = within(form).getByLabelText(/Subject/) as HTMLInputElement;
    await userEvent.clear(subject);
    await userEvent.type(subject, "Hi ");
    await userEvent.click(within(form).getByRole("button", { name: "Insert Last name" }));
    expect(subject).toHaveValue("Hi {last_name}");
  });

  it("saves both languages and the picture settings", async () => {
    const calls = stub({ current: settings() });
    const form = await open();
    await userEvent.type(within(form).getByLabelText(/Subject/), "Benvenuto {{first_name}");
    await userEvent.selectOptions(within(form).getByLabelText("Text position"), "top");
    await userEvent.click(within(form).getByRole("button", { name: "Save email" }));
    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    const sent = calls.find((c) => c.method === "PUT")!.body as {
      templates: Record<string, { subject: string; body: string }>;
      card: Record<string, string>;
    };
    expect(sent.templates.it.subject).toBe("Benvenuto {first_name}");
    expect(sent.templates.en).toEqual({ subject: "Welcome!", body: "Hi {first_name}" });
    expect(sent.card.text_position).toBe("top");
    expect(sent.card.text_color).toBe("#ffffff");
    expect(await within(form).findByText("Email saved.")).toBeInTheDocument();
  });

  it("shows the server's complaint about a wrong placeholder", async () => {
    stub({ current: settings() }, (call) =>
      call.method === "PUT"
        ? new Response(JSON.stringify({ detail: "Unknown placeholder: {nome}." }), { status: 422 })
        : undefined,
    );
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "Save email" }));
    expect(await within(form).findByRole("alert")).toHaveTextContent(
      "Unknown placeholder: {nome}.",
    );
  });

  it("uploads the background as a file and shows the remove button", async () => {
    const state = { current: settings() };
    const calls = stub(state, (call) => {
      if (call.method === "PUT" && call.url.endsWith("/image")) {
        state.current = settings({ card: { ...state.current.card, has_image: true } });
        return new Response(JSON.stringify(state.current), { status: 200 });
      }
      return undefined;
    });
    const form = await open();
    const file = new File([new Uint8Array([1, 2, 3])], "bg.png", { type: "image/png" });
    await userEvent.upload(within(form).getByLabelText(/Background \(JPEG/), file);
    await within(form).findByText("Background uploaded.");
    const upload = calls.find((c) => c.url.endsWith("/image"))!;
    expect(upload.method).toBe("PUT");
    expect(upload.isForm).toBe(true);
    expect(within(form).getByRole("button", { name: "Remove the background" })).toBeInTheDocument();
  });

  it("shows why an upload was refused", async () => {
    stub({ current: settings() }, (call) =>
      call.method === "PUT" && call.url.endsWith("/image")
        ? new Response(JSON.stringify({ detail: "The image is too big: 5 MB at most." }), {
            status: 413,
          })
        : undefined,
    );
    const form = await open();
    const file = new File([new Uint8Array([1])], "big.png", { type: "image/png" });
    await userEvent.upload(within(form).getByLabelText(/Background \(JPEG/), file);
    expect(await within(form).findByRole("alert")).toHaveTextContent("too big");
  });

  it("removes the background", async () => {
    const state = { current: settings({ card: { ...settings().card, has_image: true } }) };
    const calls = stub(state, (call) => {
      if (call.method === "DELETE") {
        state.current = settings();
        return new Response(JSON.stringify(state.current), { status: 200 });
      }
      return undefined;
    });
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "Remove the background" }));
    await within(form).findByText("Background removed.");
    expect(calls.some((c) => c.method === "DELETE")).toBe(true);
    expect(within(form).queryByRole("button", { name: "Remove the background" })).toBeNull();
  });

  it("asks for the preview with what is typed", async () => {
    stub({ current: settings() });
    const form = await open();
    await userEvent.type(
      within(form).getByLabelText(/Sentence on the picture/),
      "Hello {{first_name}",
    );
    const preview = await within(form).findByRole("img", { name: "Preview of the email picture" });
    await waitFor(() => {
      const src = (
        within(form).getByRole("img", { name: "Preview of the email picture" }) as HTMLImageElement
      ).src;
      expect(src).toContain("/api/admin/email/registration/preview.png");
      expect(decodeURIComponent(src.replace(/\+/g, " "))).toContain("text=Hello {first_name}");
      expect(src).toContain("locale=it");
    });
    expect(preview).toBeInTheDocument();
  });

  it("sends a test email in the language of the selected tab", async () => {
    const calls = stub({ current: settings() }, (call) =>
      call.method === "POST"
        ? new Response(JSON.stringify({ message: "Test email sent to boss@example.com." }), {
            status: 200,
          })
        : undefined,
    );
    const form = await open();
    await userEvent.click(within(form).getByRole("button", { name: "English" }));
    await userEvent.click(within(form).getByRole("button", { name: "Send me a test" }));
    expect(
      await within(form).findByText("Test email sent to boss@example.com."),
    ).toBeInTheDocument();
    expect(calls.find((c) => c.method === "POST")!.url).toBe(
      "/api/admin/email/registration/test?locale=en",
    );
  });

  it("is in Italian when the app is", async () => {
    stub({ current: settings() });
    const form = await open("it");
    expect(within(form).getByLabelText(/Oggetto/)).toBeInTheDocument();
    expect(within(form).getByRole("button", { name: "Inviami una prova" })).toBeInTheDocument();
    expect(within(form).getByRole("button", { name: "Inserisci Nome" })).toBeInTheDocument();
  });

  it("tells when it cannot load", async () => {
    stub({ current: settings() }, (call) =>
      call.method === "GET" && call.url === "/api/admin/email/registration"
        ? new Response("{}", { status: 500 })
        : undefined,
    );
    renderPage();
    expect(await screen.findByText("I can't load the registration email.")).toBeInTheDocument();
  });
});
