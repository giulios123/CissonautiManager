import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, vi } from "vitest";
import { App } from "../App";

const me = {
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

const boss = {
  id: 1,
  first_name: "Boss",
  last_name: "Admin",
  email: "boss@example.com",
  is_you: true,
  removable: false,
  blocked_reason: "Non puoi rimuovere te stesso: chiedi a un altro admin.",
};
const second = {
  id: 2,
  first_name: "Sara",
  last_name: "Second",
  email: "sara@example.com",
  is_you: false,
  removable: true,
  blocked_reason: null,
};

type Reply = { status?: number; body: unknown };

function setup(handler: (method: string, url: string, body?: unknown) => Reply | undefined) {
  const calls: { method: string; url: string; body?: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ method, url, body });
      if (url === "/api/me") return new Response(JSON.stringify(me), { status: 200 });
      const reply = handler(method, url, body) ?? { status: 404, body: {} };
      const { status = 200, body: payload } = reply;
      return new Response(status === 204 ? null : JSON.stringify(payload), { status });
    }),
  );
  render(
    <MemoryRouter initialEntries={["/admin/amministratori"]}>
      <App />
    </MemoryRouter>,
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe("admin management", () => {
  const list = (method: string, url: string): Reply | undefined =>
    method === "GET" && url === "/api/admin/admins" ? { body: [boss, second] } : undefined;

  it("lists admins, explains who cannot be removed and offers removal for the others", async () => {
    setup(list);
    const table = await screen.findByRole("table", { name: "Admin attuali" });
    const bossRow = within(within(table).getByRole("row", { name: /Boss Admin/ }));
    expect(bossRow.getByText(/te stesso/)).toBeInTheDocument();
    expect(bossRow.queryByRole("button")).not.toBeInTheDocument();
    expect(within(table).getByRole("button", { name: "Rimuovi Sara Second" })).toBeInTheDocument();
  });

  it("adds a registered person by email alone", async () => {
    const calls = setup((method, url) =>
      method === "POST" ? { status: 201, body: { ...second, created: false } } : list(method, url),
    );
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Email"), "sara@example.com");
    await user.click(screen.getByRole("button", { name: "Aggiungi admin" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Sara Second ora è admin");
    const post = calls.find((call) => call.method === "POST")!;
    expect(post.body).toEqual({ email: "sara@example.com", first_name: null, last_name: null });
    expect(
      calls.filter((call) => call.url === "/api/admin/admins" && call.method === "GET"),
    ).toHaveLength(2);
  });

  it("tells the new person how to sign in", async () => {
    setup((method, url) =>
      method === "POST" ? { status: 201, body: { ...second, created: true } } : list(method, url),
    );
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Email"), "sara@example.com");
    await user.type(screen.getByLabelText("Nome"), "Sara");
    await user.type(screen.getByLabelText("Cognome"), "Second");
    await user.click(screen.getByRole("button", { name: "Aggiungi admin" }));
    expect(await screen.findByRole("status")).toHaveTextContent("link via email");
  });

  it("shows the server's explanation when a new person has no name", async () => {
    setup((method, url) =>
      method === "POST"
        ? {
            status: 422,
            body: { detail: "Questa email non è ancora registrata: scrivi anche nome e cognome." },
          }
        : list(method, url),
    );
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Email"), "new@example.com");
    await user.click(screen.getByRole("button", { name: "Aggiungi admin" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("nome e cognome");
  });

  it("asks for confirmation before removing and does nothing if you go back", async () => {
    const calls = setup(list);
    const user = userEvent.setup();
    const button = await screen.findByRole("button", { name: "Rimuovi Sara Second" });
    await user.click(button);
    const dialog = await screen.findByRole("dialog", {
      name: "Rimuovere Sara Second dagli admin?",
    });
    expect(dialog).toHaveTextContent("perde subito l'accesso");
    await user.click(within(dialog).getByRole("button", { name: "No, torno indietro" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(button).toHaveFocus();
    expect(calls.some((call) => call.method === "DELETE")).toBe(false);
  });

  it("removes the admin once confirmed and reloads the list", async () => {
    let removed = false;
    const calls = setup((method, url) => {
      if (method === "DELETE") {
        removed = true;
        return { status: 204, body: null };
      }
      return method === "GET" && url === "/api/admin/admins"
        ? { body: removed ? [boss] : [boss, second] }
        : undefined;
    });
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Rimuovi Sara Second" }));
    await user.click(await screen.findByRole("button", { name: "Sì, rimuovo" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Sara Second non è più admin");
    expect(calls.find((call) => call.method === "DELETE")?.url).toBe("/api/admin/admins/2");
    expect(screen.queryByRole("button", { name: "Rimuovi Sara Second" })).not.toBeInTheDocument();
  });

  it("keeps the dialog open and shows the refusal if the server says no", async () => {
    setup((method, url) =>
      method === "DELETE"
        ? { status: 409, body: { detail: "Deve restare almeno un admin." } }
        : list(method, url),
    );
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Rimuovi Sara Second" }));
    await user.click(await screen.findByRole("button", { name: "Sì, rimuovo" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("alert")).toHaveTextContent("almeno un admin");
  });
});
