import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { I18nProvider, useI18n } from "../i18n";
import { exemptionsKey } from "./AdminRegistrationDetail";
import { CollectGuests } from "./CollectGuests";

afterEach(() => vi.unstubAllGlobals());

const row = (id: number, first: string, label = "pranzo di lun 13/07") => ({
  guest_id: id,
  first_name: first,
  last_name: "Test",
  reference: null,
  items: [{ label, price_cents: 800, collectable_cents: 800 }],
  due_cents: 800,
  paid_cents: 0,
  balance_cents: 800,
});

type Pending = { url: string; resolve: (body: unknown) => void };

/** A fetch whose answers are given by hand, in any order. */
function manualFetch() {
  const pending: Pending[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          pending.push({
            url,
            resolve: (body) => resolve(new Response(JSON.stringify(body), { status: 200 })),
          });
        }),
    ),
  );
  return pending;
}

function Switch() {
  const { setLocale } = useI18n();
  return (
    <button type="button" onClick={() => setLocale("en")}>
      to-english
    </button>
  );
}

function mount() {
  return render(
    <I18nProvider locale="it">
      <MemoryRouter>
        <Switch />
        <CollectGuests />
      </MemoryRouter>
    </I18nProvider>,
  );
}

describe("guests to collect from", () => {
  it("keeps the answer of the latest search when an older one arrives late", async () => {
    const pending = manualFetch();
    mount();
    await waitFor(() => expect(pending).toHaveLength(1));
    // First load: someone who owes. Answer it so the search box is on screen.
    await act(async () => pending[0].resolve([row(1, "Anna")]));
    await userEvent.type(await screen.findByLabelText("Cerca un esterno per nome"), "lu");
    await waitFor(() => expect(pending.length).toBeGreaterThanOrEqual(3));
    const [, first, second] = pending;
    expect(first.url).toContain("q=l");
    expect(second.url).toContain("q=lu");
    // The newer search answers first, the older one afterwards.
    await act(async () => second.resolve([row(2, "Luca")]));
    await screen.findByRole("link", { name: "Luca Test" });
    await act(async () => first.resolve([row(1, "Anna"), row(3, "Lara")]));
    expect(screen.getByRole("link", { name: "Luca Test" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Anna Test" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Lara Test" })).toBeNull();
  });

  it("asks again when the language changes, so the server labels follow", async () => {
    const pending = manualFetch();
    mount();
    await waitFor(() => expect(pending).toHaveLength(1));
    await act(async () => pending[0].resolve([row(1, "Anna", "pranzo di lun 13/07")]));
    await screen.findByText(/pranzo di lun 13\/07/);
    await userEvent.click(screen.getByRole("button", { name: "to-english" }));
    await waitFor(() => expect(pending).toHaveLength(2));
    await act(async () => pending[1].resolve([row(1, "Anna", "lunch on Mon 13/07")]));
    expect(await screen.findByText(/lunch on Mon 13\/07/)).toBeInTheDocument();
    expect(screen.queryByText(/pranzo di lun 13\/07/)).toBeNull();
  });
});

describe("exemptions panel key", () => {
  const booking = (meals: object[], activities: object[]) =>
    ({
      id: 7,
      amount_due_cents: 1100,
      paid_cents: 0,
      fee_exempt: false,
      meals,
      activities,
    }) as never;
  const lunch = { date: "2026-07-13", kind: "lunch", exempt: true };
  const hike = { id: 3, exempt: true };

  it("changes when an exempt meal or activity is removed, even if the amount does not", () => {
    const before = exemptionsKey(booking([lunch], [hike]), "ordinary");
    expect(exemptionsKey(booking([], [hike]), "ordinary")).not.toBe(before);
    expect(exemptionsKey(booking([lunch], []), "ordinary")).not.toBe(before);
    expect(exemptionsKey(booking([{ ...lunch, exempt: false }], [hike]), "ordinary")).not.toBe(
      before,
    );
    expect(exemptionsKey(booking([lunch], [hike]), "internal_non_paying")).not.toBe(before);
  });

  it("stays the same when nothing relevant changes", () => {
    expect(exemptionsKey(booking([lunch], [hike]), "ordinary")).toBe(
      exemptionsKey(booking([lunch], [hike]), "ordinary"),
    );
  });
});
