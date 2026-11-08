import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import { I18nProvider } from "./i18n";
import { PrivacyAcceptancePanel } from "./privacy";

const current = {
  id: 8,
  version: 2,
  body: "Informativa privacy v2",
  body_it: "Informativa privacy v2",
  body_en: "Privacy notice v2",
  is_legacy: false,
};

const initial = {
  edition_id: 1,
  associated: true,
  required: true,
  current_document: current,
  accepted_document_id: 7,
  history: [
    {
      id: 3,
      locale: "it",
      recorded_at: "2026-07-01T10:00:00Z",
      source: "legacy_import",
      document: {
        ...current,
        id: 7,
        version: 1,
        body: "Informativa privacy v1",
        body_it: null,
        body_en: null,
      },
    },
  ],
};

function renderPanel(onAccepted = vi.fn<() => Promise<void>>()) {
  return {
    onAccepted,
    ...render(
      <I18nProvider locale="it">
        <PrivacyAcceptancePanel onAccepted={onAccepted} />
      </I18nProvider>,
    ),
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("privacy renewal", () => {
  it("shows the current text and records a checked acceptance for its version", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({ url, init });
        const body = calls.some((call) => call.url === "/api/me/privacy/accept")
          ? {
              ...initial,
              required: false,
              accepted_document_id: current.id,
              history: [
                ...initial.history,
                {
                  id: 4,
                  locale: "it",
                  recorded_at: "2026-07-01T11:00:00Z",
                  source: "self_service",
                  document: current,
                },
              ],
            }
          : initial;
        return new Response(JSON.stringify(body), { status: 200 });
      }),
    );
    const { onAccepted } = renderPanel();

    expect(await screen.findByText("Informativa privacy v2")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox", { name: /Ho letto e accetto/ });
    expect(checkbox).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Conferma lettura" })).toBeDisabled();
    fireEvent.click(checkbox);
    fireEvent.click(screen.getByRole("button", { name: "Conferma lettura" }));

    await waitFor(() => expect(onAccepted).toHaveBeenCalledOnce());
    const accepted = calls.find((call) => call.url === "/api/me/privacy/accept");
    expect(JSON.parse(String(accepted?.init?.body))).toEqual({
      document_id: 8,
      version: 2,
      locale: "it",
      accepted: true,
    });
  });

  it("does not offer acceptance until both legal texts are available", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ ...initial, current_document: { ...current, body_en: null } }),
            { status: 200 },
          ),
      ),
    );
    renderPanel();
    expect(await screen.findByText(/non è disponibile in italiano e inglese/)).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows the original text of an accepted legacy notice", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              ...initial,
              required: false,
              current_document: {
                ...current,
                body: "Testo originale",
                body_it: null,
                body_en: null,
                is_legacy: true,
              },
            }),
            { status: 200 },
          ),
      ),
    );
    renderPanel();
    expect(await screen.findByText("Testo originale")).toBeInTheDocument();
    expect(screen.queryByText(/non è disponibile in italiano e inglese/)).not.toBeInTheDocument();
  });
});
