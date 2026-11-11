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

type Linked = { id: number; title: string; date: string; period: string };

function setup(options: { failFirst?: boolean; gate?: Promise<void> } = {}) {
  const posts: Record<string, unknown>[] = [];
  const linked: Linked[] = [];
  let failures = options.failFirst ? 1 : 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
      if (url === "/api/admin/edition") {
        return new Response(JSON.stringify({ start_date: "2026-07-13", end_date: "2026-07-17" }), {
          status: 200,
        });
      }
      if (url === "/api/admin/activities" && init?.method === "POST") {
        const body = JSON.parse(String(init.body)) as Record<string, unknown>;
        posts.push(body);
        await options.gate;
        if (failures > 0) {
          failures -= 1;
          return new Response(JSON.stringify({ detail: "Errore di prova" }), { status: 500 });
        }
        linked.push({
          id: 40 + linked.length,
          title: String(body.title_it),
          date: String(body.date),
          period: String(body.period),
        });
        return new Response(JSON.stringify({ id: 40 }), { status: 201 });
      }
      return new Response(
        JSON.stringify([
          {
            id: 5,
            kind: "talk",
            title: "Macchine",
            description: "Un talk sulle macchine",
            booking_id: 7,
            first_name: "Ada",
            last_name: "Lovelace",
            email: "ada@example.com",
            status: "confermata",
            active: true,
            hidden: false,
            activities: linked,
          },
        ]),
        { status: 200 },
      );
    }),
  );
  render(
    <MemoryRouter initialEntries={["/admin/contributions"]}>
      <App />
    </MemoryRouter>,
  );
  return posts;
}

afterEach(() => vi.unstubAllGlobals());

const open = async () =>
  userEvent.click(await screen.findByRole("button", { name: "Crea un'attività da «Macchine»" }));

async function fillEnglish(dialog: HTMLElement) {
  await userEvent.type(within(dialog).getByLabelText("Titolo · EN"), "Machines");
  await userEvent.type(within(dialog).getByLabelText("Descrizione · EN"), "A talk");
}

const save = (dialog: HTMLElement) =>
  userEvent.click(within(dialog).getByRole("button", { name: "Crea l'attività" }));

describe("creating an activity from a proposal", () => {
  it("opens the form with the text of the proposal in the language in use, the other empty", async () => {
    const posts = setup();
    await open();
    const dialog = await screen.findByRole("dialog", { name: "Nuova attività da «Macchine»" });
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    expect(within(dialog).getByLabelText("Titolo · IT")).toHaveValue("Macchine");
    expect(within(dialog).getByLabelText("Descrizione · IT")).toHaveValue("Un talk sulle macchine");
    expect(within(dialog).getByLabelText("Titolo · EN")).toHaveValue("");
    expect(within(dialog).getByLabelText("Descrizione · EN")).toHaveValue("");
    expect(within(dialog).getByText(/solo un punto di partenza/)).toBeInTheDocument();
    expect(posts).toEqual([]);
  });

  it("creates nothing when it is cancelled, and gives the focus back to the button", async () => {
    const posts = setup();
    await open();
    const button = screen.getByRole("button", { name: "Crea un'attività da «Macchine»" });
    const dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    await userEvent.click(within(dialog).getByRole("button", { name: "Annulla" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts).toEqual([]);
    expect(button).toHaveFocus();
  });

  it("saves with the proposal and a request key, then lists the new activity", async () => {
    const posts = setup();
    await open();
    const dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    await fillEnglish(dialog);
    await save(dialog);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts).toHaveLength(1);
    expect(posts[0]).toMatchObject({
      source_contribution_id: 5,
      title_it: "Macchine",
      title_en: "Machines",
      description_it: "Un talk sulle macchine",
      description_en: "A talk",
    });
    expect(String(posts[0].request_key)).toMatch(/^[0-9a-f-]{36}$/);
    expect(await screen.findByText("Attività creata.")).toBeInTheDocument();
    expect(screen.getByText("Attività create")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Macchine" })).toHaveAttribute(
      "href",
      "/admin/activities/40",
    );
  });

  it("sends one request when the save is pressed twice", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    const posts = setup({ gate });
    await open();
    const dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    await fillEnglish(dialog);
    await save(dialog);
    await save(dialog);
    expect(posts).toHaveLength(1);
    release();
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts).toHaveLength(1);
  });

  it("retries with the same key after an error, and uses a new key for a new conversion", async () => {
    const posts = setup({ failFirst: true });
    await open();
    let dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    await fillEnglish(dialog);
    await save(dialog);
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Errore di prova");
    await save(dialog);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts).toHaveLength(2);
    expect(posts[1].request_key).toBe(posts[0].request_key);

    await open();
    dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(within(dialog).getByLabelText("Giorno")).toBeInTheDocument());
    await fillEnglish(dialog);
    await save(dialog);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(posts).toHaveLength(3);
    expect(posts[2].request_key).not.toBe(posts[0].request_key);
  });
});

describe("the source on the activity page", () => {
  function showActivity(source: { contribution_id: number | null; title: string } | null) {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/me") return new Response(JSON.stringify(admin), { status: 200 });
        return new Response(
          JSON.stringify({
            id: 40,
            title: "Macchine",
            description: null,
            date: "2026-07-14",
            period: "morning",
            time_label: "09:00-13:00",
            price_cents: 0,
            capacity: null,
            joined: 0,
            free: null,
            payment_mode: "organizer",
            collectable_cents: 0,
            payment_instructions: null,
            internal_note: null,
            note_history: [],
            people: [],
            source,
          }),
          { status: 200 },
        );
      }),
    );
    render(
      <MemoryRouter initialEntries={["/admin/activities/40"]}>
        <App />
      </MemoryRouter>,
    );
  }

  it("links to the proposals while the proposal exists", async () => {
    showActivity({ contribution_id: 5, title: "Macchine analitiche" });
    const link = await screen.findByRole("link", { name: "Dalla proposta «Macchine analitiche»" });
    expect(link).toHaveAttribute("href", "/admin/contributions");
  });

  it("keeps the title, without a link, when the proposal is gone", async () => {
    showActivity({ contribution_id: null, title: "Macchine analitiche" });
    expect(
      await screen.findByText("Dalla proposta «Macchine analitiche» (non più disponibile)"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Dalla proposta/ })).not.toBeInTheDocument();
  });

  it("shows nothing for an activity that did not come from a proposal", async () => {
    showActivity(null);
    await screen.findByRole("heading", { name: "Macchine" });
    expect(screen.queryByText(/Dalla proposta/)).not.toBeInTheDocument();
  });
});
