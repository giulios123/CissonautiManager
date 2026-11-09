import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import type { ActivityOffer, BookingView } from "../auth";
import { I18nProvider } from "../i18n";
import { adminMe, renderAt, stubAdminApi } from "../test-utils";
import { ActivityPicker } from "./ActivityPicker";
import { MealEditor, mealsPreview } from "./MealEditor";

afterEach(() => vi.unstubAllGlobals());

const booking: BookingView = {
  id: 1,
  status: "confermata",
  amount_due_cents: 1100,
  paid_cents: 1100,
  balance_cents: 0,
  hold_expires_at: "2026-07-10T10:00:00Z",
  editable: true,
  can_cancel: true,
  slots: [],
  schedule: [],
  payments: [],
};
const direct = {
  price_cents: 2300,
  payment_mode: "provider" as const,
  collectable_cents: 0,
  payment_instructions: "Paga al ristorante con carta",
};

it("keeps provider instructions visible on a settled personal page", async () => {
  const me = {
    ...adminMe,
    role: "participant",
    first_name: "Ada",
    bookings: [
      {
        ...booking,
        meals: [{ ...direct, date: "2026-07-13", kind: "lunch", label: "Pranzo del 13 luglio" }],
        activities: [
          {
            ...direct,
            id: 4,
            title: "Trekking",
            description: "Una camminata nella natura",
            label: "Trekking del 13 luglio",
            date: "2026-07-13",
            period: "morning",
            time_label: "09:30-12:00",
            start_time: "09:30",
            end_time: "12:00",
          },
        ],
      },
    ],
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(JSON.stringify(url === "/api/me" ? me : {}), { status: 200 }),
    ),
  );
  renderAt("/me");
  expect(await screen.findByText(/Saldo a posto\./)).toBeInTheDocument();
  expect(screen.getAllByText(direct.payment_instructions)).toHaveLength(2);
  expect(screen.queryByText(/Ancora da versare/)).not.toBeInTheDocument();
});

it.each(["it", "en"] as const)(
  "shows direct activity instructions without increasing the fee (%s)",
  async (locale) => {
    const offer: ActivityOffer = {
      ...direct,
      id: 4,
      title: "Trekking",
      description: null,
      date: "2026-07-13",
      period: "morning",
      time_label: "09:30-12:00",
      start_time: "09:30",
      end_time: "12:00",
      capacity: null,
      free: null,
      joined: false,
      past: false,
    };
    render(
      <I18nProvider locale={locale}>
        <ActivityPicker booking={booking} offers={[offer]} onSaved={() => {}} />
      </I18nProvider>,
    );
    expect(screen.getByText(direct.payment_instructions)).toBeInTheDocument();
    const fee = document.querySelector(".fee")!;
    const before = fee.textContent;
    await userEvent.click(screen.getByRole("checkbox"));
    expect(fee.textContent).toBe(before);
  },
);

it("does not add or subtract a delegated meal in the preview", () => {
  const lunch = { ...direct, date: "2026-07-13", kind: "lunch" as const, label: "Pranzo" };
  expect(
    mealsPreview({ ...booking, allowed_meals: [lunch] }, new Set(["2026-07-13:lunch"]), 800, 1200),
  ).toBe(1100);
  expect(
    mealsPreview({ ...booking, meals: [lunch], allowed_meals: [lunch] }, new Set(), 800, 1200),
  ).toBe(1100);
});

it("shows a delegated meal's specific cost and instructions before sign-up", () => {
  render(
    <MealEditor
      booking={{
        ...booking,
        allowed_meals: [{ ...direct, date: "2026-07-13", kind: "lunch", label: "Pranzo" }],
      }}
      lunchCents={800}
      dinnerCents={1200}
      onSaved={() => {}}
    />,
  );
  expect(screen.getByText(direct.payment_instructions)).toBeInTheDocument();
  expect(screen.getByRole("checkbox").closest("label")).toHaveTextContent("23,00");
});

it("saves a specific meal's provider and price with an existing-signup warning", async () => {
  let terms = {
    payment_mode: "organizer",
    price_cents: 800,
    payment_instructions: null as string | null,
  };
  const calls = stubAdminApi((call) => {
    if (call.url === "/api/admin/views/meals")
      return {
        body: {
          days: [
            {
              date: "2026-07-13",
              meals: [{ ...terms, kind: "lunch", count: 1, diets: {}, people: [] }],
            },
          ],
        },
      };
    if (call.url === "/api/admin/meals/2026-07-13/lunch") {
      terms = call.body as typeof terms;
      return { body: terms };
    }
    return undefined;
  });
  renderAt("/admin/meals");
  await userEvent.click(await screen.findByText("Configura pagamento"));
  const form = within(screen.getByRole("form"));
  await userEvent.selectOptions(form.getByLabelText("Chi incassa"), "provider");
  expect(form.getByText(/i saldi degli iscritti vengono ricalcolati/)).toBeInTheDocument();
  await userEvent.clear(form.getByLabelText(/Prezzo/));
  await userEvent.type(form.getByLabelText(/Prezzo/), "23");
  await userEvent.type(
    form.getByLabelText("Istruzioni di pagamento e destinatario"),
    direct.payment_instructions,
  );
  await userEvent.click(form.getByRole("button", { name: "Salva pagamento" }));
  await waitFor(() =>
    expect(calls.find((c) => c.method === "PUT")?.body).toEqual({
      payment_mode: "provider",
      price_cents: 2300,
      payment_instructions: direct.payment_instructions,
    }),
  );
});

it("uses selectors for activity start and end, including minutes and midnight", async () => {
  const calls = stubAdminApi((call) => {
    if (call.url === "/api/admin/activities") return { body: call.method === "GET" ? [] : {} };
    if (call.url === "/api/admin/edition")
      return { body: { start_date: "2026-07-13", end_date: "2026-07-13" } };
    return undefined;
  });
  renderAt("/admin/activities");
  const form = within(await screen.findByRole("form", { name: "Nuova attività" }));
  expect(form.queryByRole("textbox", { name: /Orario/ })).not.toBeInTheDocument();
  await userEvent.type(form.getByLabelText("Titolo · IT"), "Evening yoga");
  await userEvent.type(form.getByLabelText("Titolo · EN"), "Evening yoga");
  await userEvent.type(form.getByLabelText("Descrizione · IT"), "Una pratica serale");
  await userEvent.type(form.getByLabelText("Descrizione · EN"), "An evening practice");
  await userEvent.selectOptions(form.getByLabelText("Fascia"), "evening");
  await userEvent.selectOptions(form.getByLabelText("Inizio: ore"), "21");
  await userEvent.selectOptions(form.getByLabelText("Inizio: minuti"), "35");
  await userEvent.selectOptions(form.getByLabelText("Fine: ore"), "24");
  await userEvent.click(form.getByRole("button", { name: "Crea l'attività" }));
  await waitFor(() =>
    expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
      start_time: "21:35",
      end_time: "00:00",
    }),
  );
});
