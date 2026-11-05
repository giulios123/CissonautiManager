import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi } from "../test-utils";

afterEach(() => vi.unstubAllGlobals());

const slotsView = (waitlist: unknown[]) => ({
  days: [
    {
      date: "2026-07-13",
      slots: [
        {
          id: 1,
          period: "morning",
          start_time: "09:00:00",
          end_time: "13:00:00",
          capacity: 1,
          present: 1,
          free: 0,
          people: [
            {
              booking_id: 7,
              first_name: "Eve",
              last_name: "Adams",
              status: "confermata",
              derived: false,
            },
          ],
          waitlist,
        },
      ],
    },
  ],
});

const bea = {
  entry_id: 5,
  position: 1,
  first_name: "Bea",
  last_name: "Neri",
  email: "bea@example.com",
};

describe("waitlist in the admin panel", () => {
  it("shows the queue of a full slot and removes someone from it", async () => {
    let waitlist: unknown[] = [bea];
    const calls = stubAdminApi((call) => {
      if (call.url === "/api/admin/views/slots") return { body: slotsView(waitlist) };
      if (call.url === "/api/admin/waitlist/5" && call.method === "DELETE") {
        waitlist = [];
        return { status: 204, body: null };
      }
      return undefined;
    });
    renderAt("/admin/giorni");
    const row = (await screen.findByText(/1\. Bea Neri/)).closest("tr") as HTMLElement;
    await userEvent.click(within(row).getByRole("button", { name: "Togli Bea Neri dalla lista" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Non parte nessuna email");
    await waitFor(() => expect(screen.queryByText(/1\. Bea Neri/)).not.toBeInTheDocument());
    expect(calls.some((c) => c.method === "DELETE")).toBe(true);
  });

  it("lists people who are only on a waitlist, without a link to a booking", async () => {
    stubAdminApi((call) =>
      call.url.startsWith("/api/admin/registrations")
        ? {
            body: [
              {
                id: null,
                first_name: "Bea",
                last_name: "Neri",
                email: "bea@example.com",
                phone: null,
                personal_code: "CSC-BBBB",
                days: 0,
                evenings: 0,
                status: "in_lista",
                amount_due_cents: 0,
                paid_cents: 0,
                balance_cents: 0,
                hold_expires_at: null,
                waitlist_slots: 2,
              },
            ],
          }
        : undefined,
    );
    renderAt("/admin");
    const name = await screen.findByText("Bea Neri");
    expect(name.closest("a")).toBeNull();
    const row = name.closest("tr") as HTMLElement;
    expect(within(row).getByText("Solo in lista d'attesa")).toBeInTheDocument();
    expect(within(row).getByText("2 slot")).toBeInTheDocument();
  });
});
