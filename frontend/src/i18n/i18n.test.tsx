import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { formatDay, formatDeadline } from "../booking";
import { formatEuro } from "../money";
import { SiteHeader } from "../SiteHeader";
import { I18nProvider, useT } from ".";
import { en } from "./en";
import { it as italian } from "./it";
import { detectLocale, getLocale } from "./locale";

describe("detectLocale", () => {
  it("prefers ?lang over the stored choice and the browser", () => {
    expect(detectLocale({ search: "?lang=en", stored: "it", languages: ["it-IT"] })).toBe("en");
    expect(detectLocale({ search: "?lang=it", stored: "en", languages: ["en-US"] })).toBe("it");
  });

  it("uses the stored choice before the browser language", () => {
    expect(detectLocale({ stored: "en", languages: ["it-IT"] })).toBe("en");
  });

  it("ignores values that are not a language", () => {
    expect(detectLocale({ search: "?lang=fr", stored: "de", languages: ["it"] })).toBe("it");
  });

  it("follows the browser: Italian for it*, English otherwise", () => {
    expect(detectLocale({ languages: ["it-IT", "en"] })).toBe("it");
    expect(detectLocale({ languages: ["en-GB"] })).toBe("en");
    expect(detectLocale({ languages: ["fr-FR", "it"] })).toBe("en");
  });

  it("defaults to Italian when nothing is known", () => {
    expect(detectLocale({})).toBe("it");
  });
});

describe("dictionaries", () => {
  it("have the same keys and the same placeholders in both languages", () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(italian).sort());
    const names = (text: string) => (text.match(/\{\w+\}/g) ?? []).sort();
    for (const key of Object.keys(italian) as (keyof typeof italian)[]) {
      expect(names(en[key]), key).toEqual(names(italian[key]));
    }
  });
});

function Probe() {
  const t = useT();
  return <p>{t("notFound.title")}</p>;
}

describe("I18nProvider", () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("speaks Italian without a provider", () => {
    render(<Probe />);
    expect(screen.getByText("Pagina non trovata")).toBeInTheDocument();
  });

  it("can be forced to English, and sets the page language", () => {
    render(
      <I18nProvider locale="en">
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByText("Page not found")).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
    expect(getLocale()).toBe("en");
  });

  it("formats money and dates in the current language", () => {
    const { unmount } = render(
      <I18nProvider locale="en">
        <Probe />
      </I18nProvider>,
    );
    expect(formatEuro(1200)).toBe("€12.00");
    expect(formatDay("2027-07-10")).toBe("Saturday 10 July");
    expect(formatDeadline("2027-07-10T10:00:00Z")).toMatch(/10 July 2027/);
    unmount();
    render(
      <I18nProvider locale="it">
        <Probe />
      </I18nProvider>,
    );
    expect(formatEuro(1200).replace(/\s/g, " ")).toBe("12,00 €");
    expect(formatDay("2027-07-10")).toBe("sabato 10 luglio");
  });
});

describe("language switch", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );
  });
  afterEach(() => {
    window.localStorage.clear();
    vi.unstubAllGlobals();
  });

  function renderHeader() {
    render(
      <I18nProvider locale="it">
        <MemoryRouter>
          <SiteHeader compact={false} />
        </MemoryRouter>
      </I18nProvider>,
    );
  }

  it("marks the current language and switches on click", () => {
    renderHeader();
    const group = screen.getByRole("group", { name: "Lingua" });
    expect(group).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Italiano" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    fireEvent.click(screen.getByRole("button", { name: "Inglese" }));
    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
    expect(document.documentElement.lang).toBe("en");
    expect(window.localStorage.getItem("cissonauti.locale")).toBe("en");
  });

  it("tells the server the choice, with the language header", () => {
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: "Inglese" }));
    const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("/api/me/locale");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body)).toEqual({ locale: "en" });
    expect(init.headers["Accept-Language"]).toBe("en");
  });

  it("works when the storage is blocked", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: "Inglese" }));
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
    vi.restoreAllMocks();
  });
});
