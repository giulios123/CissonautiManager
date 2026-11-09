import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import type { BookingView, Me } from "../auth";
import { I18nProvider, type Locale } from "../i18n";

type Reply = { status?: number; body: unknown };

function stubFetch(handler: (url: string, init?: RequestInit) => Reply) {
  const calls: { method: string; url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({
        method: init?.method ?? "GET",
        url,
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      });
      const { status = 200, body } = handler(url, init);
      return new Response(status === 204 ? null : JSON.stringify(body), { status });
    }),
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

const slot = (id: number, period: string, available: number | null) => ({
  id,
  period,
  start_time: period === "morning" ? "09:00:00" : period === "afternoon" ? "14:00:00" : "19:00:00",
  end_time: period === "morning" ? "13:00:00" : period === "afternoon" ? "18:00:00" : "00:00:00",
  capacity: available === null ? null : 25,
  available,
});

const EDITION = {
  registration_open: true,
  base_fee_cents: 1000,
  per_day_fee_cents: 100,
  days: [
    { date: "2026-07-12", past: true, slots: [slot(10, "morning", 20)] },
    {
      date: "2026-07-13",
      past: false,
      // slot 1 is full but it is mine, slot 2 is full and not mine
      slots: [slot(1, "morning", 0), slot(2, "afternoon", 0), slot(3, "evening", null)],
    },
    { date: "2026-07-14", past: false, slots: [slot(4, "morning", 5)] },
  ],
};

function booking(overrides: Partial<BookingView> = {}): BookingView {
  return {
    id: 7,
    status: "in_attesa_pagamento",
    amount_due_cents: 1100,
    paid_cents: 0,
    balance_cents: 1100,
    hold_expires_at: "2026-07-04T10:00:00Z",
    editable: true,
    can_cancel: true,
    slots: [
      { id: 1, date: "2026-07-13", period: "morning", label: "lun 13/07 mattina (09:00-13:00)" },
    ],
    schedule: [
      { date: "2026-07-13", period: "morning", start_time: "09:00:00", end_time: "13:00:00" },
      { date: "2026-07-13", period: "afternoon", start_time: "14:00:00", end_time: "18:00:00" },
      { date: "2026-07-13", period: "evening", start_time: "19:00:00", end_time: "00:00:00" },
    ],
    payments: [],
    ...overrides,
  };
}

function me(bookings: BookingView[]): Me {
  return {
    id: 1,
    first_name: "Ada",
    last_name: "Lovelace",
    email: "ada@example.com",
    role: "participant",
    personal_code: "CSC-7K3P",
    has_password: false,
    bookings,
    payment_channels: [{ code: "iban", label: "Bonifico", instructions: "IT00 X000" }],
  };
}

function openAt(handler: (url: string, init?: RequestInit) => Reply, locale: Locale = "it") {
  const calls = stubFetch(handler);
  render(
    <I18nProvider locale={locale}>
      <MemoryRouter initialEntries={["/me"]}>
        <App />
      </MemoryRouter>
    </I18nProvider>,
  );
  return calls;
}

describe("profile completion", () => {
  it("lists the server-reported fields that need an answer", async () => {
    openAt((url) =>
      url === "/api/me/profile"
        ? { body: { complete: false, missing_fields: ["phone", "company"], profile: null } }
        : { body: me([booking()]) },
    );
    expect(
      await screen.findByText("Dati da completare: Telefono, Azienda (oppure Nessuna azienda)"),
    ).toBeInTheDocument();
  });

  it("updates the Italian province requirement when country changes", async () => {
    const user = userEvent.setup();
    openAt((url) =>
      url === "/api/me/profile"
        ? {
            body: {
              complete: false,
              missing_fields: ["province"],
              profile: {
                city: "Città non censita",
                province: "",
                region: null,
                country: "Italia",
                istat_code: null,
                job_title: "Studente",
                company: "Nessuna azienda",
                expectations: "Conoscere persone",
                attended_previous: false,
              },
            },
          }
        : { body: me([booking()]) },
    );
    const province = await screen.findByLabelText("Provincia (se disponibile)");
    expect(province).toBeRequired();
    const country = screen.getByLabelText("Paese");
    await user.clear(country);
    await user.type(country, "Francia");
    expect(province).not.toBeRequired();
  });
});

describe("personal attendance summary", () => {
  it("shows seven complete days in seven rows", async () => {
    const dates = [
      "2026-11-20",
      "2026-11-21",
      "2026-11-22",
      "2026-11-23",
      "2026-11-24",
      "2026-11-25",
      "2026-11-26",
    ];
    const schedule = dates.flatMap((date) => [
      { date, period: "morning", start_time: "09:00:00", end_time: "13:00:00" },
      { date, period: "afternoon", start_time: "14:00:00", end_time: "18:00:00" },
      { date, period: "evening", start_time: "19:00:00", end_time: "00:00:00" },
    ]);
    const slots = schedule.map((slot, id) => ({ ...slot, id, label: slot.period }));
    openAt((url) =>
      url === "/api/me" ? { body: me([booking({ slots, schedule })]) } : { body: {} },
    );

    const summary = within(await screen.findByRole("region", { name: "Le tue presenze" }));
    expect(summary.getAllByRole("listitem")).toHaveLength(7);
    expect(summary.getByText("ven 20 nov")).toBeInTheDocument();
    expect(summary.getByText("gio 26 nov")).toBeInTheDocument();
    expect(summary.queryByText("Mattina · Pomeriggio")).not.toBeInTheDocument();
  });
});

async function openEditor() {
  await userEvent.click(await screen.findByRole("button", { name: "Modifica presenze" }));
  return within(await screen.findByRole("form", { name: "Modifica i tuoi slot" }));
}

describe("organizer on their own page", () => {
  const route =
    (role: "admin" | "participant") =>
    (url: string): Reply =>
      url === "/api/me" ? { body: { ...me([]), role } } : { status: 404, body: {} };

  it("sees their page with a visible way to the panel", async () => {
    openAt(route("admin"));
    expect(await screen.findByRole("heading", { name: "Ciao Ada!" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Vai al pannello organizzatori" })).toHaveAttribute(
      "href",
      "/admin",
    );
  });

  it("does not show the panel link to participants", async () => {
    openAt(route("participant"));
    await screen.findByRole("heading", { name: "Ciao Ada!" });
    expect(screen.queryByRole("link", { name: /pannello/ })).not.toBeInTheDocument();
  });
});

describe("changing slots", () => {
  const routes =
    (state = { me: me([booking()]) }) =>
    (url: string, init?: RequestInit): Reply => {
      if (url === "/api/me") return { body: state.me };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/meals/preview") {
        const request = JSON.parse(String(init?.body ?? "{}")) as { meals?: unknown[] };
        return {
          body: {
            registration_fee_cents: 1000,
            amount_due_cents: request.meals?.length ? 2300 : 1100,
            included_meals: [],
          },
        };
      }
      if (url === "/api/me/booking/slots" && init?.method === "PUT") return { body: booking() };
      return { status: 404, body: {} };
    };

  it("previews the new fee and the difference as slots are chosen", async () => {
    openAt(routes());
    const form = await openEditor();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    expect(await form.findByText(/Nuova quota/)).toHaveTextContent(
      "Nuova quota: 12,00 € (1,00 € in più di ora)",
    );
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    expect(form.getByText(/Nuova quota/)).toHaveTextContent("Nuova quota: 11,00 €");
    expect(form.getByText(/Nuova quota/)).not.toHaveTextContent("di ora");
  });

  it("previews quota and total separately for a booking on the new policy", async () => {
    const routesForFeePolicy = routes({
      me: me([
        booking({
          confirmation_policy: "registration_fee",
          registration_fee_cents: 1100,
          amount_due_cents: 1100,
        }),
      ]),
    });
    openAt(routesForFeePolicy);
    const form = await openEditor();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    expect(form.getByText(/Nuova quota di partecipazione/)).toHaveTextContent(/12,00/);
    expect(form.getByText(/Nuovo totale dovuto all'organizzazione/)).toHaveTextContent(/12,00/);
  });

  it("shows a lower fee when a day is dropped", async () => {
    openAt(routes());
    const form = await openEditor();
    const [, monday] = form.getAllByRole("group");
    await userEvent.click(within(monday).getByRole("checkbox", { name: /Mattina/ }));
    expect(form.getByText(/Nuova quota/)).toHaveTextContent("Nuova quota: 10,00 € (1,00 € in meno");
  });

  it("locks past days and full slots that are not mine, but keeps my own slot editable", async () => {
    openAt(routes());
    const form = await openEditor();
    const [sunday, monday] = form.getAllByRole("group");
    expect(within(sunday).getByRole("checkbox")).toBeDisabled();
    expect(within(sunday).getByRole("checkbox")).toHaveAccessibleName(/giorno passato/);
    expect(within(monday).getByRole("checkbox", { name: /Mattina/ })).toBeEnabled();
    expect(within(monday).getByRole("checkbox", { name: /Mattina/ })).toBeChecked();
    expect(within(monday).getByRole("checkbox", { name: /Mattina/ })).toHaveAccessibleName(
      /il tuo posto/,
    );
    expect(within(monday).getByRole("checkbox", { name: /Pomeriggio/ })).toBeDisabled();
    expect(within(monday).getByRole("checkbox", { name: /Sera/ })).toBeEnabled();
  });

  it("saves only after a change, sends the chosen slots and reloads the page data", async () => {
    const calls = openAt(routes());
    const form = await openEditor();
    const save = form.getByRole("button", { name: "Salva gli slot" });
    expect(save).toBeDisabled();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    expect(save).toBeEnabled();
    await userEvent.click(save);
    expect(await form.findByText("Slot aggiornati.")).toBeInTheDocument();
    const put = calls.find((call) => call.method === "PUT");
    expect(put?.body).toEqual({ slot_ids: [1, 4] });
    expect(calls.filter((call) => call.url === "/api/me")).toHaveLength(2);
  });

  it("refuses an empty selection and points to the cancellation", async () => {
    const calls = openAt(routes());
    const form = await openEditor();
    const [, monday] = form.getAllByRole("group");
    await userEvent.click(within(monday).getByRole("checkbox", { name: /Mattina/ }));
    await userEvent.click(form.getByRole("button", { name: "Salva gli slot" }));
    expect(await form.findByRole("alert")).toHaveTextContent("Per rinunciare usa la disdetta");
    expect(calls.some((call) => call.method === "PUT")).toBe(false);
  });

  it("shows the server error and refreshes the seats when a slot filled up", async () => {
    const handler = routes();
    const calls = openAt((url, init) =>
      url === "/api/me/booking/slots"
        ? { status: 409, body: { detail: "Questi slot sono al completo: mar 14/07 mattina." } }
        : handler(url, init),
    );
    const form = await openEditor();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    const editionLoads = () => calls.filter((call) => call.url === "/api/public/edition").length;
    const before = editionLoads();
    await userEvent.click(form.getByRole("button", { name: "Salva gli slot" }));
    expect(await form.findByRole("alert")).toHaveTextContent("al completo");
    await waitFor(() => expect(editionLoads()).toBe(before + 1));
  });

  it("does not offer the editor on a booking that can no longer change", async () => {
    openAt(
      routes({
        me: me([booking({ status: "scaduta", editable: false, can_cancel: false })]),
      }),
    );
    expect(await screen.findByRole("heading", { name: "Scaduta" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Modifica presenze" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Richiedi disdetta" })).not.toBeInTheDocument();
  });
});

describe("cancelling", () => {
  function cancelRoutes(initial: Me) {
    let current = initial;
    return (url: string, init?: RequestInit): Reply => {
      if (url === "/api/me") return { body: current };
      if (url === "/api/me/booking/cancel" && init?.method === "POST") {
        current = { ...current, bookings: [] };
        return { body: { outcome: "removed" } };
      }
      return { status: 404, body: {} };
    };
  }

  it("asks for confirmation, with focus on the safe choice, and closes with Escape", async () => {
    const calls = openAt(cancelRoutes(me([booking()])));
    const trigger = await screen.findByRole("button", { name: "Richiedi disdetta" });
    await userEvent.click(trigger);
    const dialog = await screen.findByRole("dialog", { name: "Vuoi disdire l'iscrizione?" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveTextContent("I tuoi posti si liberano subito");
    expect(dialog).toHaveTextContent("Non risultano pagamenti");
    expect(screen.getByRole("button", { name: "No, torno indietro" })).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("keeps the focus inside the dialog when tabbing", async () => {
    openAt(cancelRoutes(me([booking()])));
    await userEvent.click(await screen.findByRole("button", { name: "Richiedi disdetta" }));
    const dialog = await screen.findByRole("dialog");
    const keep = within(dialog).getByRole("button", { name: "No, torno indietro" });
    const confirm = within(dialog).getByRole("button", { name: "Sì, disdico" });
    await userEvent.tab();
    expect(confirm).toHaveFocus();
    await userEvent.tab();
    expect(keep).toHaveFocus();
    await userEvent.tab({ shift: true });
    expect(confirm).toHaveFocus();
  });

  it("mentions the refund when something was already paid", async () => {
    openAt(
      cancelRoutes(me([booking({ paid_cents: 500, balance_cents: 600, status: "confermata" })])),
    );
    await userEvent.click(await screen.findByRole("button", { name: "Richiedi disdetta" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Hai già versato 5,00 €");
  });

  it("sends the cancellation and tells what happened", async () => {
    const calls = openAt(cancelRoutes(me([booking()])));
    await userEvent.click(await screen.findByRole("button", { name: "Richiedi disdetta" }));
    await userEvent.click(await screen.findByRole("button", { name: "Sì, disdico" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Disdetta registrata");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText(/Non hai ancora un.iscrizione/)).toBeInTheDocument();
    expect(calls.filter((call) => call.method === "POST")).toHaveLength(1);
  });
});

describe("balance and instructions", () => {
  const route =
    (bookings: BookingView[]) =>
    (url: string): Reply =>
      url === "/api/me" ? { body: me(bookings) } : { status: 404, body: {} };

  it("asks to pay the difference on a confirmed booking after a change", async () => {
    openAt(route([booking({ status: "confermata", paid_cents: 1100, balance_cents: 100 })]));
    expect(await screen.findByText(/Ancora da versare/)).toHaveTextContent("1,00 €");
    expect(screen.getByText(/la differenza si versa/)).toBeInTheDocument();
    expect(screen.getByText("CSC-7K3P")).toBeInTheDocument();
    expect(screen.getByText("IT00 X000")).toBeInTheDocument();
  });

  it("shows the credit when the new amount is lower than what was paid", async () => {
    openAt(route([booking({ status: "confermata", paid_cents: 1200, balance_cents: -100 })]));
    expect(await screen.findByText(/Versato in più/)).toHaveTextContent("1,00 €");
  });

  it("shows fee, confirmation remainder and total separately under the new policy", async () => {
    openAt(
      route([
        booking({
          confirmation_policy: "registration_fee",
          registration_fee_cents: 1200,
          confirmation_due_cents: 1200,
          confirmation_balance_cents: 700,
          amount_due_cents: 2500,
          paid_cents: 500,
          balance_cents: 2000,
        }),
      ]),
    );
    const card = await screen.findByRole("region", { name: /Iscrizione/ });
    expect(card).toHaveTextContent("Quota di partecipazione: 12,00 €");
    expect(card).toHaveTextContent("Dovuto per confermare la prenotazione: 7,00 €");
    expect(card).toHaveTextContent("Totale dovuto all'organizzazione: 25,00 €");
    expect(card).toHaveTextContent("Pranzi, cene e attività possono essere pagati dopo.");
  });

  it("shows a confirmed booking's extra balance without a place-loss deadline", async () => {
    openAt(
      route([
        booking({
          confirmation_policy: "registration_fee",
          registration_fee_cents: 1200,
          confirmation_due_cents: 1200,
          confirmation_balance_cents: 0,
          status: "confermata",
          amount_due_cents: 2500,
          paid_cents: 1200,
          balance_cents: 1300,
        }),
      ]),
    );
    const card = await screen.findByRole("region", { name: /Iscrizione/ });
    expect(card).toHaveTextContent("La prenotazione è confermata.");
    expect(card).toHaveTextContent("Ancora da versare: 13,00 €");
    expect(card).toHaveTextContent("Pranzi, cene e attività possono essere pagati dopo.");
    expect(card).not.toHaveTextContent("Il posto è bloccato fino al");
  });

  it("explains a requested cancellation and offers no actions", async () => {
    openAt(
      route([
        booking({
          status: "disdetta_richiesta",
          editable: false,
          can_cancel: false,
          paid_cents: 500,
        }),
      ]),
    );
    expect(await screen.findByText(/Hai chiesto la disdetta/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /disdetta|slot/i })).not.toBeInTheDocument();
  });
});

describe("seats after saving", () => {
  it("lets a participant pick again a full slot they have just freed", async () => {
    let editions = 0;
    let saved = false;
    const afterSave = booking({
      slots: [
        { id: 4, date: "2026-07-14", period: "morning", label: "mar 14/07 mattina (09:00-13:00)" },
      ],
    });
    openAt((url, init) => {
      if (url === "/api/me") return { body: me([saved ? afterSave : booking()]) };
      if (url === "/api/public/edition") {
        editions += 1;
        // slot 1 is full and mine; once I leave it a seat is free
        const slots =
          editions === 1
            ? EDITION.days[1].slots
            : [slot(1, "morning", 1), ...EDITION.days[1].slots.slice(1)];
        return {
          body: {
            ...EDITION,
            days: [EDITION.days[0], { ...EDITION.days[1], slots }, EDITION.days[2]],
          },
        };
      }
      if (url === "/api/me/booking/slots" && init?.method === "PUT") {
        saved = true;
        return { body: afterSave };
      }
      return { status: 404, body: {} };
    });
    const form = await openEditor();
    const [, monday, tuesday] = form.getAllByRole("group");
    await userEvent.click(within(monday).getByRole("checkbox", { name: /Mattina/ })); // leave it
    await userEvent.click(within(tuesday).getByRole("checkbox")); // take Tuesday instead
    await userEvent.click(form.getByRole("button", { name: "Salva gli slot" }));
    await form.findByText("Slot aggiornati.");
    const morning = within(monday).getByRole("checkbox", { name: /Mattina/ });
    expect(morning).toBeEnabled();
    expect(morning).not.toBeChecked();
  });
});

describe("waitlist", () => {
  const withList = {
    ...EDITION,
    days: EDITION.days.map((day) => ({
      ...day,
      slots: day.slots.map((s) => (s.id === 2 ? { ...s, waitlist_free: 2 } : s)),
    })),
  };
  const entry = {
    id: 9,
    slot_id: 2,
    date: "2026-07-13",
    period: "afternoon",
    label: "lun 13/07 pomeriggio (14:00-18:00)",
    position: 2,
  };

  it("offers the full slots with a waitlist and joins one", async () => {
    const state = { me: me([booking()]) };
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: state.me };
      if (url === "/api/public/edition") return { body: withList };
      if (url === "/api/me/waitlist" && init?.method === "POST") {
        state.me = { ...state.me, waitlist: [entry] };
        return { status: 201, body: entry };
      }
      return { status: 404, body: {} };
    });
    const list = await screen.findByRole("list", { name: "Slot pieni con lista aperta" });
    // Slot 1 is full but mine: it is not offered.
    expect(within(list).getAllByRole("listitem")).toHaveLength(1);
    await userEvent.click(within(list).getByRole("button", { name: "Mettiti in lista" }));
    expect(await screen.findByText(/2° in lista/)).toBeInTheDocument();
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({ slot_id: 2 });
    expect(screen.getByRole("status")).toHaveTextContent("Sei in lista d'attesa.");
  });

  it("shows only the waitlist to someone without a booking, with nothing to pay", async () => {
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: { ...me([]), waitlist: [entry] } };
      if (url === "/api/public/edition") return { body: withList };
      if (url.startsWith("/api/me/waitlist/") && init?.method === "DELETE")
        return { status: 204, body: null };
      return { status: 404, body: {} };
    });
    expect(await screen.findByText(/2° in lista/)).toBeInTheDocument();
    expect(screen.getByText(/non devi pagare nulla/)).toBeInTheDocument();
    expect(screen.queryByText(/Non hai ancora un'iscrizione/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Esci dalla lista" }));
    await waitFor(() =>
      expect(calls.some((c) => c.method === "DELETE" && c.url === "/api/me/waitlist/9")).toBe(true),
    );
  });
});

describe("meals", () => {
  const allowed = [
    { date: "2026-07-13", kind: "lunch" as const, label: "pranzo di lun 13/07", past: false },
    { date: "2026-07-13", kind: "dinner" as const, label: "cena di lun 13/07", past: false },
    { date: "2026-07-12", kind: "lunch" as const, label: "pranzo di dom 12/07", past: true },
  ];
  const withMeals = (meals: typeof allowed = []) => ({
    ...me([booking({ allowed_meals: allowed, meals })]),
    lunch_price_cents: 800,
    dinner_price_cents: 1200,
  });

  it("previews the new amount and saves the chosen meals", async () => {
    const state = { me: withMeals() };
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: state.me };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/meals/preview") {
        const request = JSON.parse(String(init?.body ?? "{}")) as { meals?: unknown[] };
        return {
          body: {
            registration_fee_cents: 1000,
            amount_due_cents: request.meals?.length ? 2300 : 1100,
            included_meals: [],
          },
        };
      }
      if (url === "/api/me/booking/meals" && init?.method === "PUT") {
        state.me = withMeals([allowed[1]]);
        return { body: state.me.bookings[0] };
      }
      return { status: 404, body: {} };
    });
    expect(await screen.findByText("Nessun pasto scelto.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Scegli pranzi e cene" }));
    const form = within(await screen.findByRole("form", { name: "Scegli pranzi e cene" }));
    expect(form.getByRole("checkbox", { name: /Pranzo.*giorno passato/ })).toBeDisabled();
    await userEvent.click(form.getByRole("checkbox", { name: /^Cena/ }));
    expect(await form.findByText(/Nuova quota/)).toHaveTextContent(
      "Nuova quota: 23,00 € (12,00 € in più di ora)",
    );
    await userEvent.click(form.getByRole("button", { name: "Salva i pasti" }));
    expect(await screen.findByText("cena di lun 13/07")).toBeInTheDocument();
    expect(calls.find((c) => c.method === "PUT")?.body).toEqual({
      meals: [{ date: "2026-07-13", kind: "dinner" }],
    });
  });

  it("shows the server error", async () => {
    openAt((url, init) => {
      if (url === "/api/me") return { body: withMeals() };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/meals/preview")
        return {
          body: { registration_fee_cents: 1000, amount_due_cents: 1100, included_meals: [] },
        };
      if (url === "/api/me/booking/meals" && init?.method === "PUT")
        return {
          status: 422,
          body: { detail: "Puoi scegliere un pasto solo quando sei presente" },
        };
      return { status: 404, body: {} };
    });
    await userEvent.click(await screen.findByRole("button", { name: "Scegli pranzi e cene" }));
    const form = within(await screen.findByRole("form", { name: "Scegli pranzi e cene" }));
    await userEvent.click(form.getAllByRole("checkbox", { name: /^Pranzo/ })[0]);
    const save = form.getByRole("button", { name: "Salva i pasti" });
    await waitFor(() => expect(save).toBeEnabled());
    await userEvent.click(save);
    expect(await form.findByRole("alert")).toHaveTextContent("solo quando sei presente");
  });
});

describe("dietary needs", () => {
  const consent = { version: 1, body: "Testo del consenso" };

  it("refuses allergies without the consent and saves them with it", async () => {
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: { ...me([booking()]), health_consent: consent } };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/dietary" && init?.method === "PUT") return { body: booking() };
      return { status: 404, body: {} };
    });
    const form = within(await screen.findByRole("form", { name: "Esigenze alimentari" }));
    await userEvent.selectOptions(form.getByLabelText("Regime alimentare"), "vegan");
    await userEvent.type(form.getByLabelText("Allergie e intolleranze"), "Arachidi");
    await userEvent.click(form.getByRole("button", { name: "Salva esigenze alimentari" }));
    expect(await form.findByRole("alert")).toHaveTextContent("spunta il consenso");
    expect(calls.some((c) => c.url === "/api/me/booking/dietary")).toBe(false);
    await userEvent.click(form.getByRole("checkbox", { name: /Acconsento/ }));
    await userEvent.click(form.getByRole("button", { name: "Salva esigenze alimentari" }));
    expect(await form.findByRole("status")).toHaveTextContent("salvate");
    expect(calls.find((c) => c.url === "/api/me/booking/dietary")?.body).toEqual({
      diet: "vegan",
      allergies: "Arachidi",
      consent: true,
      consent_version: 1,
    });
  });

  it("without a published consent text only the diet can be given", async () => {
    openAt((url) => {
      if (url === "/api/me") return { body: me([booking()]) };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    });
    const form = within(await screen.findByRole("form", { name: "Esigenze alimentari" }));
    expect(form.queryByLabelText("Allergie e intolleranze")).not.toBeInTheDocument();
    expect(form.getByText(/scrivi a chi organizza/)).toBeInTheDocument();
  });

  it("shows the health notice in the interface language", async () => {
    const consent = {
      version: 2,
      body: "Italian original notice",
      body_it: "Avviso salute italiano",
      body_en: "English health notice",
      is_legacy: false,
    };
    openAt((url) => {
      if (url === "/api/me") return { body: { ...me([booking()]), health_consent: consent } };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    }, "en");
    const form = within(await screen.findByRole("form", { name: "Dietary needs" }));
    await userEvent.click(form.getByText("Read the consent for health data"));
    expect(form.getByText("English health notice")).toBeInTheDocument();
    expect(form.queryByText("Avviso salute italiano")).not.toBeInTheDocument();
    expect(form.queryByText(/original text is shown/)).not.toBeInTheDocument();
  });

  it("marks the original health notice when the selected translation is missing", async () => {
    const consent = {
      version: 2,
      body: "Italian original notice",
      body_it: "Italian original notice",
      body_en: null,
      is_legacy: true,
    };
    openAt((url) => {
      if (url === "/api/me") return { body: { ...me([booking()]), health_consent: consent } };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    }, "en");
    const form = within(await screen.findByRole("form", { name: "Dietary needs" }));
    await userEvent.click(form.getByText("Read the consent for health data"));
    expect(form.getByText("Italian original notice")).toBeInTheDocument();
    expect(form.getByText(/original text is shown/)).toBeInTheDocument();
  });
});

describe("activities", () => {
  const offer = (over: Record<string, unknown>) => ({
    id: 1,
    title: "Escursione",
    description: "Sul monte",
    date: "2026-07-13",
    period: "morning",
    time_label: "9:30-12",
    start_time: "09:30",
    end_time: "12:00",
    payment_mode: "organizer",
    payment_instructions: null,
    price_cents: 1500,
    collectable_cents: 1500,
    capacity: 2,
    free: 1,
    joined: false,
    past: false,
    ...over,
  });

  it("joins a paid activity with a preview, and a full one is locked", async () => {
    const offers = [offer({}), offer({ id: 2, title: "Kayak", free: 0, price_cents: 0 })];
    const state = { me: { ...me([booking()]), activities: offers } };
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: state.me };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/activities" && init?.method === "PUT") {
        state.me = {
          ...me([
            booking({
              activities: [
                {
                  id: 1,
                  title: "Escursione",
                  description: "Sul monte",
                  label: "Escursione (lun 13/07 mattina)",
                  date: "2026-07-13",
                  period: "morning",
                  time_label: "9:30-12",
                  start_time: "09:30",
                  end_time: "12:00",
                  payment_mode: "organizer",
                  payment_instructions: null,
                  price_cents: 1500,
                  collectable_cents: 1500,
                },
              ],
            }),
          ]),
          activities: [offer({ joined: true, free: 0 }), offers[1]],
        };
        return { body: state.me.bookings[0] };
      }
      return { status: 404, body: {} };
    });
    expect(await screen.findByText("Nessuna attività scelta.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Scegli le attività" }));
    const form = within(await screen.findByRole("form", { name: "Scegli le attività" }));
    expect(form.getByRole("checkbox", { name: /Kayak/ })).toBeDisabled();
    await userEvent.click(form.getByRole("checkbox", { name: /Escursione/ }));
    expect(form.getByText(/Nuova quota/)).toHaveTextContent("26,00 € (15,00 € in più di ora)");
    await userEvent.click(form.getByRole("button", { name: "Salva le attività" }));
    const detailSummary = (await screen.findAllByText("Dettagli attività"))[0];
    const selected = detailSummary.closest("li");
    expect(selected).toHaveTextContent("Escursione (lun 13/07 mattina)");
    await userEvent.click(detailSummary);
    expect(within(selected as HTMLElement).getByText("Sul monte")).toBeInTheDocument();
    expect(calls.find((c) => c.url === "/api/me/booking/activities")?.body).toEqual({
      activity_ids: [1],
    });
  });

  it("says when there are no activities for the moments booked", async () => {
    openAt((url) => {
      if (url === "/api/me") return { body: { ...me([booking()]), activities: [] } };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    });
    await userEvent.click(await screen.findByRole("button", { name: "Scegli le attività" }));
    expect(await screen.findByText(/non ci sono attività/)).toBeInTheDocument();
  });
});

describe("contributions", () => {
  it("adds a contribution and lists it", async () => {
    const state = { me: { ...me([booking()]), contributions: [], can_bring: "Una torta" } };
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: state.me };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/contributions" && init?.method === "POST") {
        const item = { id: 5, kind: "topic", title: "Lavoro remoto", description: null };
        state.me = { ...state.me, contributions: [item] as never[] };
        return { status: 201, body: item };
      }
      return { status: 404, body: {} };
    });
    const section = within(
      (await screen.findByRole("heading", { name: "Cosa porti al camp" })).closest(
        "section",
      ) as HTMLElement,
    );
    expect(section.getByText(/«Una torta»/)).toBeInTheDocument();
    const form = within(section.getByRole("form", { name: "Proponi un contributo" }));
    await userEvent.selectOptions(form.getByLabelText("Tipo"), "topic");
    await userEvent.type(form.getByLabelText("Titolo"), "Lavoro remoto");
    await userEvent.click(form.getByRole("button", { name: "Aggiungi" }));
    expect(await section.findByText(/Lavoro remoto/)).toBeInTheDocument();
    expect(section.getByRole("listitem")).toHaveTextContent(
      "Tema per l'unconference: Lavoro remoto",
    );
    expect(calls.find((c) => c.url === "/api/me/contributions")?.body).toEqual({
      kind: "topic",
      title: "Lavoro remoto",
      description: null,
    });
  });
});

describe("dietary needs after review", () => {
  const consent = { version: 2, body: "Testo del consenso v2" };
  const withAllergy = (version: number) =>
    booking({ allergies: "Arachidi", health_consent_version: version });

  it("withdraws the consent and the allergies without clearing the field by hand", async () => {
    const calls = openAt((url, init) => {
      if (url === "/api/me") return { body: { ...me([withAllergy(2)]), health_consent: consent } };
      if (url === "/api/public/edition") return { body: EDITION };
      if (url === "/api/me/booking/dietary" && init?.method === "PUT") return { body: booking() };
      return { status: 404, body: {} };
    });
    const form = within(await screen.findByRole("form", { name: "Esigenze alimentari" }));
    await userEvent.click(form.getByRole("checkbox", { name: /Acconsento/ }));
    await userEvent.click(form.getByRole("button", { name: "Salva esigenze alimentari" }));
    expect(await form.findByRole("status")).toHaveTextContent("salvate");
    expect(calls.find((c) => c.url === "/api/me/booking/dietary")?.body).toEqual({
      diet: null,
      allergies: null,
      consent: false,
      consent_version: null,
    });
  });

  it("asks to accept again a consent text that changed", async () => {
    openAt((url) => {
      if (url === "/api/me") return { body: { ...me([withAllergy(1)]), health_consent: consent } };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    });
    const form = within(await screen.findByRole("form", { name: "Esigenze alimentari" }));
    expect(form.getByRole("checkbox", { name: /Acconsento/ })).not.toBeChecked();
    expect(form.getByText(/Il testo del consenso è cambiato/)).toBeInTheDocument();
  });
});

describe("slot preview with meals and activities", () => {
  it("keeps the price of the extras still allowed and drops the others", async () => {
    const withExtras = {
      ...me([
        booking({
          amount_due_cents: 1100 + 800 + 1500,
          meals: [{ date: "2026-07-13", kind: "lunch", label: "pranzo di lun 13/07" }],
        }),
      ]),
      lunch_price_cents: 800,
      dinner_price_cents: 1200,
      activities: [
        {
          id: 1,
          title: "Escursione",
          description: null,
          date: "2026-07-13",
          period: "morning",
          time_label: null,
          price_cents: 1500,
          capacity: null,
          free: null,
          joined: true,
          past: false,
        },
      ],
    };
    openAt((url) => {
      if (url === "/api/me") return { body: withExtras };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    });
    const form = await openEditor();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    // Monday morning stays: lunch and hike stay too; one more day adds 1 euro.
    expect(form.getByText(/Nuova quota/)).toHaveTextContent("Nuova quota: 35,00 € (1,00 € in più");
    const [, monday] = form.getAllByRole("group");
    await userEvent.click(within(monday).getByRole("checkbox", { name: /Mattina/ }));
    // Without Monday morning, lunch and hike go: only Tuesday is left.
    expect(form.getByText(/Nuova quota/)).toHaveTextContent("Nuova quota: 11,00 €");
  });

  it("excludes provider-paid extras from the slot preview", async () => {
    const withExtras = {
      ...me([
        booking({
          amount_due_cents: 1100,
          meals: [
            {
              date: "2026-07-13",
              kind: "lunch" as const,
              label: "pranzo di lun 13/07",
              price_cents: 2300,
              payment_mode: "provider" as const,
              payment_instructions: "Pagamento al ristorante",
              collectable_cents: 0,
            },
          ],
        }),
      ]),
      lunch_price_cents: 800,
      dinner_price_cents: 1200,
      activities: [
        {
          id: 1,
          title: "Escursione",
          description: null,
          date: "2026-07-13",
          period: "morning",
          time_label: null,
          price_cents: 1500,
          payment_mode: "provider" as const,
          payment_instructions: "Pagamento alla guida",
          collectable_cents: 0,
          capacity: null,
          free: null,
          joined: true,
          past: false,
        },
      ],
    };
    openAt((url) => {
      if (url === "/api/me") return { body: withExtras };
      if (url === "/api/public/edition") return { body: EDITION };
      return { status: 404, body: {} };
    });

    const form = await openEditor();
    const [, , tuesday] = form.getAllByRole("group");
    await userEvent.click(within(tuesday).getByRole("checkbox"));
    expect(form.getByText(/Nuova quota/)).toHaveTextContent(
      "Nuova quota: 12,00 € (1,00 € in più di ora)",
    );
  });
});
