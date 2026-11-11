import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";

const admin = {
  id: 1,
  first_name: "Boss",
  last_name: "",
  email: "boss@example.com",
  role: "admin",
  personal_code: "CSC-0001",
  has_password: true,
  bookings: [],
  payment_channels: [],
};

const row = (id: number, title: string, hidden: boolean) => ({
  id,
  kind: "talk",
  title,
  description: null,
  booking_id: 7,
  first_name: "Ada",
  last_name: "Lovelace",
  email: "ada@example.com",
  status: "confermata",
  active: true,
  hidden,
  activities: [],
});

function setup(rows: ReturnType<typeof row>[], gate?: Promise<void>) {
  const state = { rows };
  const calls: { url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      if (url === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
      const match = url.match(/^\/api\/admin\/contributions\/(\d+)\/(hide|unhide)$/);
      if (match) {
        await gate;
        state.rows = state.rows.map((r) =>
          r.id === Number(match[1]) ? { ...r, hidden: match[2] === "hide" } : r,
        );
        return new Response(JSON.stringify({ id: Number(match[1]), hidden: match[2] === "hide" }), {
          status: 200,
        });
      }
      return new Response(JSON.stringify(state.rows), { status: 200 });
    }),
  );
  render(
    <MemoryRouter initialEntries={["/admin/contributions"]}>
      <App />
    </MemoryRouter>,
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe("hiding proposals", () => {
  it("hides one with a reason after a confirmation, and shows it again", async () => {
    const calls = setup([row(1, "Macchine", false)]);
    await userEvent.click(await screen.findByRole("button", { name: "Nascondi agli altri" }));
    const dialog = await screen.findByRole("dialog", { name: /Nascondere la proposta «Macchine»/ });
    await userEvent.type(within(dialog).getByLabelText("Motivo (facoltativo)"), "Contiene un nome");
    await userEvent.click(within(dialog).getByRole("button", { name: "Nascondi" }));
    expect(await screen.findByRole("button", { name: "Mostra di nuovo" })).toBeInTheDocument();
    expect(screen.getByText("Nascosta")).toBeInTheDocument();
    expect(calls.find((c) => c.url === "/api/admin/contributions/1/hide")?.body).toEqual({
      reason: "Contiene un nome",
    });
    await userEvent.click(screen.getByRole("button", { name: "Mostra di nuovo" }));
    expect(await screen.findByRole("button", { name: "Nascondi agli altri" })).toBeInTheDocument();
    expect(calls.some((c) => c.url === "/api/admin/contributions/1/unhide")).toBe(true);
  });

  it("changes nothing when the confirmation is cancelled", async () => {
    const calls = setup([row(1, "Macchine", false)]);
    const button = await screen.findByRole("button", { name: "Nascondi agli altri" });
    await userEvent.click(button);
    await userEvent.click(await screen.findByRole("button", { name: "No, torno indietro" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(calls.some((c) => c.url.includes("/hide"))).toBe(false);
    expect(button).toHaveFocus();
  });
});

describe("while a change is being saved", () => {
  it("blocks the other buttons and the cancel, so a pending request cannot close a new dialog", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    setup([row(1, "Macchine", false), row(2, "Open source", false)], gate);
    const buttons = await screen.findAllByRole("button", { name: "Nascondi agli altri" });
    await userEvent.click(buttons[0]);
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Nascondi" }));
    expect(within(dialog).getByRole("button", { name: "No, torno indietro" })).toBeDisabled();
    for (const button of screen.getAllByRole("button", { name: "Nascondi agli altri" })) {
      expect(button).toBeDisabled();
    }
    release();
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});
