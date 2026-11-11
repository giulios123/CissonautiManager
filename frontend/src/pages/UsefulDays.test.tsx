import { act, renderHook, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { renderAt, stubAdminApi, type Call } from "../test-utils";
import { useRefreshOnReturn } from "../useRefreshOnReturn";

afterEach(() => {
  vi.unstubAllGlobals();
  setVisibility("visible");
});

function setVisibility(state: "visible" | "hidden") {
  Object.defineProperty(document, "visibilityState", { value: state, configurable: true });
}

/** The user leaves the tab and comes back to it. */
function returnToTab() {
  setVisibility("hidden");
  document.dispatchEvent(new Event("visibilitychange"));
  setVisibility("visible");
  act(() => {
    document.dispatchEvent(new Event("visibilitychange"));
  });
}

const weekDay = (date: string, people = 0) => ({
  date,
  morning: people,
  afternoon: 0,
  evening: 0,
  evening_derived: 0,
  people,
  lunches: 0,
  dinners: 0,
  activities: 0,
});
const weekBody = (dates: string[], today: string | null) => ({
  days: dates.map((d, i) => weekDay(d, i + 1)),
  total_people: 3,
  today,
});

/** The first column of the table body: the days in the order they are shown. */
function shownDays() {
  return screen
    .getAllByRole("rowheader")
    .filter((cell) => cell.closest("tbody"))
    .map((cell) => cell.textContent ?? "");
}

/** Hold back the answer of the requests that match, until `release()` is called. */
function holdBack(matches: (url: string, init?: RequestInit) => boolean) {
  const real = globalThis.fetch;
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => (release = resolve));
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const response = await real(url, init);
      if (matches(url, init)) await gate;
      return response;
    }),
  );
  return release;
}

describe("the week in the useful order", () => {
  it("shows the days as the server sent them and marks today with a word", async () => {
    stubAdminApi((call: Call) =>
      call.url === "/api/admin/views/week"
        ? { body: weekBody(["2026-07-14", "2026-07-15", "2026-07-13"], "2026-07-14") }
        : undefined,
    );
    renderAt("/admin/week");
    await screen.findAllByRole("rowheader");
    const days = shownDays();
    expect(days).toHaveLength(3);
    expect(days[0]).toContain("14");
    expect(days[0]).toContain("Oggi");
    expect(days[1]).toContain("15");
    expect(days[2]).toContain("13");
    expect(days.filter((d) => d.includes("Oggi"))).toHaveLength(1);
  });

  it("marks no day before the event", async () => {
    stubAdminApi((call: Call) =>
      call.url === "/api/admin/views/week"
        ? { body: weekBody(["2026-07-13", "2026-07-14"], null) }
        : undefined,
    );
    renderAt("/admin/week");
    await screen.findAllByRole("rowheader");
    expect(screen.queryByText("Oggi")).not.toBeInTheDocument();
  });

  it("reloads on return to the tab and moves the new day to the top", async () => {
    let body = weekBody(["2026-07-13", "2026-07-14"], "2026-07-13");
    const calls = stubAdminApi((call: Call) =>
      call.url === "/api/admin/views/week" ? { body } : undefined,
    );
    renderAt("/admin/week");
    await screen.findAllByRole("rowheader");
    expect(shownDays()[0]).toContain("13");
    body = weekBody(["2026-07-14", "2026-07-13"], "2026-07-14");
    returnToTab();
    await waitFor(() => expect(shownDays()[0]).toContain("14"));
    expect(shownDays()[0]).toContain("Oggi");
    expect(calls.filter((c) => c.url === "/api/admin/views/week")).toHaveLength(2);
  });

  it("does not reload while a dialog is open, and does when it is closed", async () => {
    const calls = stubAdminApi((call: Call) => {
      if (call.url === "/api/admin/views/week")
        return { body: weekBody(["2026-07-13", "2026-07-14"], "2026-07-13") };
      if (call.url.startsWith("/api/admin/views/week/detail"))
        return { body: { metric: "morning", date: "2026-07-13", count: 1, rows: [] } };
      return undefined;
    });
    renderAt("/admin/week");
    const button = await screen.findByRole("button", { name: /^Mattina, .*13 luglio: 1/ });
    await userEvent.click(button);
    const dialog = await screen.findByRole("dialog");
    const weekCalls = () => calls.filter((c) => c.url === "/api/admin/views/week").length;
    returnToTab();
    returnToTab();
    expect(weekCalls()).toBe(1);
    // The dialog is still on the day it was opened for.
    expect(within(dialog).getByRole("heading")).toHaveTextContent(/13 luglio/);
    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    returnToTab();
    await waitFor(() => expect(weekCalls()).toBe(2));
  });
});

describe("a slow refresh", () => {
  it("is dropped when a dialog opens while the answer is on its way", async () => {
    let body = weekBody(["2026-07-13", "2026-07-14"], "2026-07-13");
    const calls = stubAdminApi((call: Call) => {
      if (call.url === "/api/admin/views/week") return { body };
      if (call.url.startsWith("/api/admin/views/week/detail"))
        return { body: { metric: "morning", date: "2026-07-13", count: 1, rows: [] } };
      return undefined;
    });
    renderAt("/admin/week");
    const button = await screen.findByRole("button", { name: /^Mattina, .*13 luglio: 1/ });
    const weekCalls = () => calls.filter((c) => c.url === "/api/admin/views/week").length;
    // The refresh starts, and its answer is held back.
    const release = holdBack((url) => url === "/api/admin/views/week");
    body = weekBody(["2026-07-14", "2026-07-13"], "2026-07-14");
    returnToTab();
    await waitFor(() => expect(weekCalls()).toBe(2));
    // Meanwhile the organiser opens a dialog; the late answer must not reorder the page.
    await userEvent.click(button);
    await screen.findByRole("dialog");
    release();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(shownDays()[0]).toContain("13");
    expect(screen.queryByText("Oggi")).toBeInTheDocument();
    expect(shownDays()[0]).toContain("Oggi");
    // Once the dialog is closed, the next return applies the new order.
    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    returnToTab();
    await waitFor(() => expect(shownDays()[0]).toContain("14"));
  });

  it("is not started while a waitlist removal is pending", async () => {
    const waiting = {
      entry_id: 5,
      position: 1,
      first_name: "Ada",
      last_name: "Lovelace",
      email: "ada@example.com",
    };
    const slot = {
      id: 1,
      period: "morning",
      start_time: "09:00:00",
      end_time: "13:00:00",
      capacity: 1,
      present: 1,
      free: 0,
      people: [],
      waitlist: [waiting],
    };
    const calls = stubAdminApi((call: Call) => {
      if (call.url === "/api/admin/views/slots")
        return { body: { today: null, days: [{ date: "2026-07-13", slots: [slot] }] } };
      if (call.method === "DELETE") return { status: 204, body: null };
      return undefined;
    });
    renderAt("/admin/days");
    const remove = await screen.findByRole("button", { name: /Ada Lovelace/ });
    const reads = () => calls.filter((c) => c.url === "/api/admin/views/slots").length;
    const release = holdBack((_, init) => init?.method === "DELETE");
    await userEvent.click(remove);
    await waitFor(() => expect(calls.some((c) => c.method === "DELETE")).toBe(true));
    returnToTab();
    expect(reads()).toBe(1);
    release();
    // The page reloads by itself after the removal, and the next return works again.
    await waitFor(() => expect(reads()).toBe(2));
    returnToTab();
    await waitFor(() => expect(reads()).toBe(3));
  });
});

describe("the days and slots and the meals in the useful order", () => {
  it("shows the slots days as sent, with Oggi in the caption of today", async () => {
    stubAdminApi((call: Call) =>
      call.url === "/api/admin/views/slots"
        ? {
            body: {
              today: "2026-07-14",
              days: [
                { date: "2026-07-14", slots: [] },
                { date: "2026-07-15", slots: [] },
                { date: "2026-07-13", slots: [] },
              ],
            },
          }
        : undefined,
    );
    renderAt("/admin/days");
    await screen.findByRole("table", { name: /14 .*Oggi/ });
    const captions = screen
      .getAllByRole("table")
      .map((t) => t.querySelector("caption")?.textContent);
    expect(captions.map((c) => c?.match(/\d+/)?.[0])).toEqual(["14", "15", "13"]);
    expect(screen.getAllByText("Oggi")).toHaveLength(1);
  });

  it("shows the meals days as sent and reloads on return", async () => {
    let today = "2026-07-13";
    let dates = ["2026-07-13", "2026-07-14"];
    const calls = stubAdminApi((call: Call) =>
      call.url === "/api/admin/views/meals"
        ? { body: { today, days: dates.map((date) => ({ date, meals: [] })) } }
        : undefined,
    );
    renderAt("/admin/meals");
    await screen.findByRole("table", { name: /13 .*Oggi/ });
    today = "2026-07-14";
    dates = ["2026-07-14", "2026-07-13"];
    returnToTab();
    await screen.findByRole("table", { name: /14 .*Oggi/ });
    expect(calls.filter((c) => c.url === "/api/admin/views/meals")).toHaveLength(2);
  });
});

describe("useRefreshOnReturn", () => {
  it("loads on return, not while hidden, and stops listening when unmounted", () => {
    const load = vi.fn();
    const { unmount } = renderHook(() => useRefreshOnReturn(load));
    setVisibility("hidden");
    document.dispatchEvent(new Event("visibilitychange"));
    expect(load).not.toHaveBeenCalled();
    returnToTab();
    expect(load).toHaveBeenCalledTimes(1);
    unmount();
    returnToTab();
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("skips the refresh while blocked, with a field in focus or with an editor open", () => {
    const load = vi.fn();
    let blocked = true;
    renderHook(() => useRefreshOnReturn(load, () => blocked));
    returnToTab();
    expect(load).not.toHaveBeenCalled();
    blocked = false;
    const field = document.createElement("input");
    document.body.append(field);
    field.focus();
    returnToTab();
    expect(load).not.toHaveBeenCalled();
    field.remove();
    const main = document.createElement("main");
    main.innerHTML = "<details open><summary>Configura</summary></details>";
    document.body.append(main);
    returnToTab();
    expect(load).not.toHaveBeenCalled();
    main.remove();
    returnToTab();
    expect(load).toHaveBeenCalledTimes(1);
  });
});
