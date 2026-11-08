import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import { AdminConsentHistory, ConsentPanel, type ConsentCollection } from "./consents";
import { I18nProvider } from "./i18n";

const document = {
  id: 8,
  version: 2,
  body: "Testo presenza",
  body_it: "Testo presenza",
  body_en: "Attendance text",
  is_legacy: false,
};

const empty = {
  edition_id: 1,
  associated: true,
  consents: [
    {
      kind: "attendance",
      action: "not_expressed",
      event_id: null,
      authorized_for_current_document: false,
      needs_renewal: false,
      current_document: document,
      events: [],
    },
    {
      kind: "media",
      action: "not_expressed",
      event_id: null,
      authorized_for_current_document: false,
      needs_renewal: false,
      current_document: null,
      events: [],
    },
  ],
} satisfies ConsentCollection;

function renderPanel() {
  return render(
    <I18nProvider locale="it">
      <ConsentPanel />
    </I18nProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("optional consent form", () => {
  it("keeps choices separate and sends the displayed version and language", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({ url, init });
        const body =
          calls.length === 1
            ? empty
            : {
                ...empty,
                consents: [
                  {
                    ...empty.consents[0],
                    action: "granted",
                    event_id: 12,
                    authorized_for_current_document: true,
                  },
                  empty.consents[1],
                ],
              };
        return new Response(JSON.stringify(body), { status: 200 });
      }),
    );
    renderPanel();
    const yes = (await screen.findAllByRole("radio", { name: "Sì, acconsento" }))[0];
    expect(yes).toBeEnabled();
    expect(screen.getAllByRole("radio", { name: "No, non acconsento" })[0]).not.toBeChecked();
    fireEvent.click(yes);
    fireEvent.click(screen.getAllByRole("button", { name: "Salva scelta" })[0]);
    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1].url).toBe("/api/me/consents/attendance");
    expect(JSON.parse(String(calls[1].init?.body))).toEqual({
      granted: true,
      document_id: 8,
      version: 2,
      locale: "it",
      expected_event_id: null,
    });
    expect(await screen.findByText("Scelta salvata.")).toBeInTheDocument();
    expect(calls.filter((call) => call.url === "/api/me/consents/media")).toHaveLength(0);
  });

  it("does not allow a new choice until a complete bilingual text exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(empty), { status: 200 })),
    );
    renderPanel();
    expect(await screen.findByText(/Il testo completo in italiano e inglese/)).toBeInTheDocument();
    expect(screen.getAllByRole("radio")[2]).toBeDisabled();
    expect(screen.getAllByRole("radio")[3]).toBeDisabled();
  });

  it("does not preselect a grant when the published text has changed", async () => {
    const stale = {
      ...empty,
      consents: [
        {
          ...empty.consents[0],
          action: "granted",
          event_id: 12,
          authorized_for_current_document: false,
          needs_renewal: true,
          events: [
            {
              id: 12,
              action: "granted",
              locale: "it",
              recorded_at: "2026-07-01T10:00:00Z",
              source: "self_service",
              document: { ...document, id: 7, version: 1 },
            },
          ],
        },
        empty.consents[1],
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(stale), { status: 200 })),
    );
    renderPanel();
    const yes = (await screen.findAllByRole("radio", { name: "Sì, acconsento" }))[0];
    expect(yes).not.toBeChecked();
    expect(screen.getByText(/Il testo è cambiato/)).toBeInTheDocument();
  });
});

describe("organizer privacy history", () => {
  it("shows the recorded language and labels legacy language as unknown", async () => {
    const history = {
      ...empty,
      privacy_current_version: 2,
      privacy_accepted_version: 1,
      privacy_acceptance_required: true,
      privacy_history: [
        {
          id: 1,
          locale: "it",
          recorded_at: "2026-07-01T10:00:00Z",
          source: "self_service",
          document: { ...document, version: 2 },
        },
        {
          id: 2,
          locale: null,
          recorded_at: "2026-07-01T11:00:00Z",
          source: "legacy_import",
          document: { ...document, version: 1 },
        },
      ],
    } satisfies ConsentCollection;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(history), { status: 200 })),
    );
    render(
      <I18nProvider locale="it">
        <AdminConsentHistory participantId={7} />
      </I18nProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Mostra storico consensi" }));

    const rows = await screen.findAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("lingua IT");
    expect(rows[1]).toHaveTextContent("lingua non registrata");
  });
});
