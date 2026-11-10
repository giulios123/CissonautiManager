import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { I18nProvider, type Locale } from "../i18n";

const edition = {
  registration_open: true,
  name: "Camp 2026",
  base_fee_cents: 1000,
  per_day_fee_cents: 100,
  hold_days: 3,
  days: [
    {
      date: "2026-07-13",
      slots: [
        {
          id: 1,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 25,
          available: 10,
        },
        {
          id: 2,
          period: "afternoon",
          start_time: "14:00:00",
          end_time: "18:00:00",
          capacity: 25,
          available: 0,
        },
        {
          id: 7,
          period: "evening",
          start_time: "19:00:00",
          end_time: "00:00:00",
          capacity: null,
          available: null,
        },
      ],
    },
    {
      date: "2026-07-14",
      slots: [
        {
          id: 3,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 25,
          available: 25,
        },
      ],
    },
  ],
  payment_channels: [],
  privacy: { version: 1, body: "Privacy" },
  disclaimer: { version: 1, body: "Scarico" },
};

const bilingualEdition = {
  ...edition,
  privacy: {
    version: 2,
    body: "Informativa privacy",
    body_it: "Informativa privacy IT",
    body_en: "Privacy notice EN",
  },
  disclaimer: {
    version: 3,
    body: "Scarico IT",
    body_it: "Scarico IT",
    body_en: "Liability waiver EN",
  },
  attendance_consent: {
    id: 41,
    version: 4,
    texts: { it: "Testo presenza IT", en: "Attendance notice EN" },
  },
  media_consent: {
    id: 42,
    version: 5,
    texts: { it: "Testo immagini IT", en: "Media notice EN" },
  },
};

function mockFetch(responses: Record<string, { status?: number; body: unknown }>) {
  const calls: { url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      const response = responses[url];
      return new Response(JSON.stringify(response.body), { status: response.status ?? 200 });
    }),
  );
  return calls;
}

function renderPage(path = "/register", locale: Locale = "it") {
  render(
    <I18nProvider locale={locale}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </I18nProvider>,
  );
}

async function fillProfile(user: ReturnType<typeof userEvent.setup>) {
  const fields: Record<string, string> = {
    telegram: "@ada",
    linkedin: "Non possiedo",
    city: "Torino",
    province: "TO",
    country: "Italia",
    job_title: "Matematica",
    company: "Nessuna azienda",
    expectations: "Conoscere persone",
  };
  for (const [name, value] of Object.entries(fields)) {
    const input = document.querySelector<HTMLInputElement | HTMLTextAreaElement>(
      `[name="${name}"]`,
    );
    if (input && !input.value) await user.type(input, value);
  }
  const previous = document.querySelector<HTMLSelectElement>('[name="attended_previous"]');
  if (previous && !previous.value) await user.selectOptions(previous, "no");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("Registration page", () => {
  it("explains when optional consent texts have not been published", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    await screen.findByText(/Quota da versare/);
    for (const name of ["Visibilità della presenza nell'area riservata", "Foto e video"]) {
      const consent = screen.getByRole("group", { name });
      expect(within(consent).getByRole("status")).toHaveTextContent(
        "Questo consenso facoltativo non è disponibile al momento.",
      );
      expect(within(consent).queryByRole("radio")).not.toBeInTheDocument();
    }
  });

  it("requires a nonblank phone number", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const phone = await screen.findByLabelText("Telefono");
    expect(phone).toBeRequired();
    expect(phone).toBeInvalid();
    await userEvent.type(phone, "   ");
    expect(phone).toBeInvalid();
    await userEvent.clear(phone);
    await userEvent.type(phone, "+39 333 1234567");
    expect(phone).toBeValid();
  });

  it("keeps the fee and sign-up button in the top registration bar", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    const fee = await screen.findByText(/Quota da versare/);
    const form = fee.closest("form")!;
    const toolbar = form.querySelector(".registration-toolbar")!;
    const summary = within(form).getByRole("complementary", { name: "Il tuo riepilogo" });

    expect(toolbar).toContainElement(fee);
    expect(toolbar).toContainElement(screen.getByRole("button", { name: "Iscriviti" }));
    expect(toolbar).not.toContainElement(summary);
    await user.click(await screen.findByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    expect(within(toolbar as HTMLElement).getByText(/Quota da versare/)).toHaveTextContent("11,00");
  });

  it("measures the bar and the sticky header, and follows them when they change", async () => {
    const heights = { toolbar: 64, header: 56 };
    const observers: { callback: () => void; targets: Element[] }[] = [];
    vi.stubGlobal(
      "ResizeObserver",
      class {
        entry = { callback: () => {}, targets: [] as Element[] };
        constructor(callback: () => void) {
          this.entry.callback = callback;
          observers.push(this.entry);
        }
        observe(target: Element) {
          this.entry.targets.push(target);
        }
        unobserve() {}
        disconnect() {}
      },
    );
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.classList.contains("registration-toolbar")) return heights.toolbar;
      if (this.classList.contains("site-header")) return heights.header;
      return 0;
    });
    const realStyle = window.getComputedStyle.bind(window);
    vi.spyOn(window, "getComputedStyle").mockImplementation((element, pseudo) =>
      element.classList.contains("site-header")
        ? ({ position: "sticky" } as CSSStyleDeclaration)
        : realStyle(element, pseudo),
    );
    try {
      mockFetch({ "/api/public/edition": { body: edition } });
      renderPage();
      const form = (await screen.findByText(/Quota da versare/)).closest("form")!;
      const bar = () => form.style.getPropertyValue("--registration-bar-height");
      const offset = () => form.style.getPropertyValue("--registration-sticky-offset");
      expect([bar(), offset()]).toEqual(["64px", "56px"]);

      // The bar and the header are both watched: the bar wraps on a narrow screen or in English.
      const watched = new Set(observers.flatMap((o) => o.targets));
      expect(watched).toContain(form.querySelector(".registration-toolbar"));
      expect(watched).toContain(document.querySelector(".site-header"));

      heights.toolbar = 112;
      heights.header = 72;
      observers.forEach((o) => o.callback());
      expect([bar(), offset()]).toEqual(["112px", "72px"]);
    } finally {
      vi.restoreAllMocks();
    }
  });

  it("tells people when registrations are closed", async () => {
    mockFetch({
      "/api/public/edition": { body: { registration_open: false, name: null, days: [] } },
    });
    renderPage();
    expect(await screen.findByText(/non sono ancora aperte/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Accedi" })).toHaveAttribute("href", "/login?lang=it");
  });

  it("keeps the sign-in link available if loading fails", async () => {
    mockFetch({ "/api/public/edition": { status: 500, body: { detail: "Unavailable" } } });
    renderPage();
    expect(await screen.findByText(/Non riesco a caricare la pagina/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Accedi" })).toHaveAttribute("href", "/login?lang=it");
  });

  it("keeps the selected language in the sign-in link", async () => {
    mockFetch({ "/api/public/edition": { body: { registration_open: false, days: [] } } });
    renderPage("/register?lang=en", "en");
    expect(await screen.findByText(/Registrations are not open/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login?lang=en");
  });

  it("shows the sign-in link above the registration form", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const link = await screen.findByRole("link", { name: "Accedi" });
    expect(link).toHaveAttribute("href", "/login?lang=it");
    expect(
      link.compareDocumentPosition(screen.getByRole("group", { name: "I tuoi dati" })) & 4,
    ).toBeTruthy();
  });

  it("opens sign-in in a new tab from inside the event iframe", async () => {
    vi.spyOn(window, "top", "get").mockReturnValue({} as Window & typeof globalThis);
    mockFetch({ "/api/public/edition": { body: { registration_open: false, days: [] } } });
    renderPage();
    const link = await screen.findByRole("link", { name: "Accedi" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener");
    expect(screen.getByText(/si apre in una nuova finestra/)).toBeInTheDocument();
  });

  it("shows the paragraph written by the organizers, in the language of the page", async () => {
    mockFetch({
      "/api/public/edition": {
        body: {
          ...edition,
          registration_intro: { it: "Benvenuto!\nScegli i tuoi turni.", en: "Welcome!" },
        },
      },
    });
    renderPage();
    const intro = await screen.findByText(/Benvenuto!/);
    expect(intro).toHaveTextContent("Benvenuto! Scegli i tuoi turni.");
    expect(intro).toHaveClass("intro-text");
    expect(screen.getByRole("link", { name: "Accedi" })).not.toHaveAttribute("target", "_blank");
  });

  it("falls back to the standard paragraph when the server sends none", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    expect(await screen.findByText(/Scegli i momenti in cui vuoi venire/)).toBeInTheDocument();
  });

  it("disables full slots and updates the fee preview", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    expect(await screen.findByText(/Quota da versare/)).toHaveTextContent("10,00");
    expect(screen.getByLabelText(/Pomeriggio 14:00-18:00 · completo/)).toBeDisabled();

    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 25 posti liberi/));
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("12,00");
  });

  it("always allows the evening, with no seat limit", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    const evening = await screen.findByLabelText(/Sera 19:00-00:00 · senza limite di posti/);
    expect(evening).toBeEnabled();
    await user.click(evening);
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("11,00");
  });

  it("asks for at least one slot", async () => {
    const calls = mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Scegli almeno uno slot");
    expect(calls.filter((c) => c.url.includes("registrations"))).toHaveLength(0);
  });

  it("submits the registration and shows the payment summary", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "in_attesa_pagamento",
            amount_due_cents: 1100,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina" }],
            schedule: [
              {
                date: "2026-07-13",
                period: "morning",
                start_time: "09:00:00",
                end_time: "13:00:00",
              },
              {
                date: "2026-07-13",
                period: "afternoon",
                start_time: "14:00:00",
                end_time: "18:00:00",
              },
              {
                date: "2026-07-13",
                period: "evening",
                start_time: "19:00:00",
                end_time: "00:00:00",
              },
            ],
            payment_channels: [{ code: "iban", label: "Bonifico (IBAN)", instructions: "IT00" }],
          },
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    expect(await screen.findByRole("heading", { name: "Iscrizione ricevuta" })).toBeInTheDocument();
    expect(screen.getByText("CSC-7K3P")).toBeInTheDocument();
    expect(screen.getByText("Bonifico (IBAN)")).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([1]);
    expect(sent.privacy_version).toBe(1);
    expect(sent.email).toBe("ada@example.com");
  });

  it("localizes legal notices and submits independent optional consent choices", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: bilingualEdition },
      "/api/public/registrations": {
        status: 201,
        body: { result: "already_registered", message: "Già iscritto" },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);

    const attendanceIt = screen.getByRole("group", {
      name: "Visibilità della presenza nell'area riservata",
    });
    const mediaIt = screen.getByRole("group", { name: "Foto e video" });
    expect(within(attendanceIt).getByLabelText("Sì, acconsento")).not.toBeChecked();
    expect(within(mediaIt).getByLabelText("No, non acconsento")).not.toBeChecked();
    await user.click(within(attendanceIt).getByLabelText("Sì, acconsento"));
    await user.click(screen.getByRole("button", { name: "Inglese" }));

    const attendanceEn = screen.getByRole("group", {
      name: "Show my attendance in the members-only area",
    });
    const mediaEn = screen.getByRole("group", { name: "Photos and video" });
    expect(within(attendanceEn).getByLabelText("Yes, I consent")).toBeChecked();
    expect(screen.getByText("Attendance notice EN")).toBeInTheDocument();
    await user.click(screen.getByText("Read the privacy notice"));
    expect(screen.getByText("Privacy notice EN")).toBeInTheDocument();
    await user.click(within(mediaEn).getByLabelText("No, I do not consent"));

    await user.click(await screen.findByRole("button", { name: "All morning" }));
    await user.type(screen.getByLabelText("First name"), "Ada");
    await user.type(screen.getByLabelText("Last name"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Phone"), "+39 333 1234567");
    await user.type(screen.getByLabelText("What can you bring to the camp?"), "A talk");
    await user.click(screen.getByLabelText("I have read and accept the privacy notice"));
    await user.click(screen.getByLabelText("I have read and accept the liability waiver"));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Sign up" }));

    const sent = calls.find((call) => call.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.optional_consents).toEqual({
      attendance: { granted: true, document_id: 41, version: 4 },
      media: { granted: false, document_id: 42, version: 5 },
    });
    expect(sent.consent_locale).toBe("en");
  });

  it("shows the fee needed to confirm separately from the full total", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "in_attesa_pagamento",
            confirmation_policy: "registration_fee",
            registration_fee_cents: 1100,
            confirmation_due_cents: 1100,
            confirmation_balance_cents: 1100,
            amount_due_cents: 1900,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina" }],
            schedule: [],
            payment_channels: [{ code: "iban", label: "Bonifico", instructions: "IT00" }],
          },
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    const confirmation = await screen.findByRole("main");
    expect(confirmation).toHaveTextContent("Quota di partecipazione: 11,00 €");
    expect(confirmation).toHaveTextContent("Dovuto per confermare la prenotazione: 11,00 €");
    expect(confirmation).toHaveTextContent("Totale dovuto all'organizzazione: 19,00 €");
    expect(confirmation).toHaveTextContent("Pranzi, cene e attività possono essere pagati dopo.");
  });

  it("does not show a payment deadline or payment instructions for a confirmed zero-fee place", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "confermata",
            confirmation_policy: "registration_fee",
            registration_fee_cents: 0,
            confirmation_due_cents: 0,
            confirmation_balance_cents: 0,
            amount_due_cents: 0,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina" }],
            schedule: [],
            payment_channels: [{ code: "iban", label: "Bonifico", instructions: "IT00" }],
          },
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    const confirmation = await screen.findByRole("main");
    expect(confirmation).toHaveTextContent("La prenotazione è confermata.");
    expect(confirmation).not.toHaveTextContent("Il posto è bloccato fino al");
    expect(confirmation).not.toHaveTextContent("Come pagare");
  });

  it("does not repeat a known account's payment reference in the anonymous response", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          message: "Per la causale e i dettagli, controlla l'email che ti abbiamo inviato.",
          booking: {
            personal_code: null,
            status: "in_attesa_pagamento",
            amount_due_cents: 1100,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina" }],
            schedule: [],
            payment_channels: [],
          },
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    expect(
      await screen.findByText(/Per la causale e i dettagli, controlla l'email/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/CSC-/)).not.toBeInTheDocument();
  });

  it("shows the sign-in link when the email is already registered", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 201,
        body: { result: "already_registered", message: "Sei già iscritto." },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));

    expect(await screen.findByRole("heading", { name: "Sei già iscritto" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Accedi" })).toHaveAttribute("href", "/login?lang=it");
  });

  it("shows the server message when a slot became full", async () => {
    mockFetch({
      "/api/public/edition": { body: edition },
      "/api/public/registrations": {
        status: 409,
        body: { detail: "Questi slot sono al completo: lun 13/07 mattina. Scegline altri." },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("al completo"));
  });
});

describe("waitlist in the registration form", () => {
  const withList = {
    ...edition,
    days: edition.days.map((day) => ({
      ...day,
      slots: day.slots.map((s) => (s.id === 2 ? { ...s, waitlist_free: 3 } : s)),
    })),
  };

  async function fillIn(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Cognome"), "Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Telefono"), "+39 333 1234567");
    await user.type(screen.getByLabelText(/Cosa puoi portare/), "Un talk");
    await user.click(screen.getByLabelText(/informativa privacy$/));
    await user.click(screen.getByLabelText(/scarico di responsabilità$/));
  }

  it("lets people tick a full slot with a waitlist, and says there is nothing to pay", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: withList },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "waitlisted",
          personal_code: "CSC-7K3P",
          waitlist: [{ label: "lun 13/07 pomeriggio (14:00-18:00)", position: 1 }],
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    const full = await screen.findByLabelText(/Pomeriggio 14:00-18:00 · completo, spunta/);
    expect(full).toBeEnabled();
    await user.click(full);
    expect(screen.getByText(/Solo lista d'attesa/)).toBeInTheDocument();
    await fillIn(user);
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(
      await screen.findByRole("heading", { name: "Sei in lista d'attesa" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/sei 1° in lista/)).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([]);
    expect(sent.waitlist_slot_ids).toEqual([2]);
  });

  it("books free slots and lists the full ones in the summary", async () => {
    const calls = mockFetch({
      "/api/public/edition": { body: withList },
      "/api/public/registrations": {
        status: 201,
        body: {
          result: "created",
          booking: {
            personal_code: "CSC-7K3P",
            status: "in_attesa_pagamento",
            amount_due_cents: 1100,
            hold_expires_at: "2026-07-04T10:00:00Z",
            slots: [{ date: "2026-07-13", period: "morning", label: "lun 13/07 mattina" }],
            schedule: [
              {
                date: "2026-07-13",
                period: "morning",
                start_time: "09:00:00",
                end_time: "13:00:00",
              },
              {
                date: "2026-07-13",
                period: "afternoon",
                start_time: "14:00:00",
                end_time: "18:00:00",
              },
              {
                date: "2026-07-13",
                period: "evening",
                start_time: "19:00:00",
                end_time: "00:00:00",
              },
            ],
            payment_channels: [],
          },
          waitlist: [{ label: "lun 13/07 pomeriggio (14:00-18:00)", position: 2 }],
        },
      },
    });
    renderPage();
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Pomeriggio 14:00-18:00 · completo, spunta/));
    // The waitlisted slot is not in the fee: only Monday morning is booked.
    expect(screen.getByText(/Quota da versare/)).toHaveTextContent("11,00");
    await fillIn(user);
    await fillProfile(user);
    await user.click(screen.getByRole("button", { name: "Iscriviti" }));
    expect(await screen.findByRole("heading", { name: "In lista d'attesa" })).toBeInTheDocument();
    expect(screen.getByText(/sei 2° in lista/)).toBeInTheDocument();
    const sent = calls.find((c) => c.url === "/api/public/registrations")?.body as Record<
      string,
      unknown
    >;
    expect(sent.slot_ids).toEqual([1]);
    expect(sent.waitlist_slot_ids).toEqual([2]);
  });

  it("groups the chosen slots by day and links back to the calendar", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    const summary = await screen.findByRole("complementary", { name: "Il tuo riepilogo" });
    expect(
      within(summary).queryByRole("link", { name: "Modifica presenze" }),
    ).not.toBeInTheDocument();
    await user.click(await screen.findByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/));
    await user.click(screen.getByLabelText(/Sera 19:00-00:00/));
    expect(within(summary).getAllByRole("listitem")).toHaveLength(1);
    expect(within(summary).getByText("Mattina · Sera")).toBeInTheDocument();
    expect(within(summary).getByRole("heading", { name: /1 giorno/ })).toBeInTheDocument();
    const edit = within(summary).getByRole("link", { name: "Modifica presenze" });
    expect(edit).toHaveAttribute("href", "#when-title");
    expect(within(summary).queryByRole("button", { name: /Togli/ })).not.toBeInTheDocument();
    const calendarHeading = screen.getByRole("heading", { name: "Quando vieni" });
    const scrollIntoView = vi.fn();
    calendarHeading.scrollIntoView = scrollIntoView;
    await user.click(edit);
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "center" });
    expect(screen.getByLabelText(/Mattina 09:00-13:00 · 10 posti liberi/)).toBeChecked();
    expect(screen.getByLabelText(/Sera 19:00-00:00/)).toBeChecked();
    expect(screen.getByRole("heading", { name: "Quando vieni" })).toHaveFocus();
  });

  it("shows only the date for morning and afternoon because the evening is included", async () => {
    mockFetch({ "/api/public/edition": { body: edition } });
    renderPage();
    const user = userEvent.setup();
    await screen.findByText(/Quota da versare/);
    await user.click(screen.getAllByLabelText(/Mattina 09:00-13:00/)[0]);
    await user.click(screen.getAllByLabelText(/Pomeriggio 14:00-18:00/)[0]);
    const summary = screen.getByRole("complementary", { name: "Il tuo riepilogo" });
    expect(within(summary).getByText("lun 13 lug")).toBeInTheDocument();
    expect(within(summary).queryByText("Mattina · Pomeriggio")).not.toBeInTheDocument();
    expect(within(summary).getByText(/Giornate complete/)).toBeInTheDocument();
  });

  it("keeps a full slot locked when its waitlist is full too", async () => {
    const fullList = {
      ...edition,
      days: edition.days.map((day) => ({
        ...day,
        slots: day.slots.map((s) => (s.id === 2 ? { ...s, waitlist_free: 0 } : s)),
      })),
    };
    mockFetch({ "/api/public/edition": { body: fullList } });
    renderPage();
    expect(
      await screen.findByLabelText(/Pomeriggio 14:00-18:00 · completo, anche la lista/),
    ).toBeDisabled();
  });
});
