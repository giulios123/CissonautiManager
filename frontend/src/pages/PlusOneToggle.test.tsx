import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { PlusOneToggle } from "./PlusOneToggle";

afterEach(() => vi.unstubAllGlobals());

function stub(status = 200, body: unknown = {}) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const base = {
  participantId: 12,
  invitedBy: "Ada",
  verified: false,
};

describe("PlusOneToggle", () => {
  it("verifies the person and tells the page to reload", async () => {
    const fetchMock = stub();
    const onChanged = vi.fn();
    render(<PlusOneToggle {...base} onChanged={onChanged} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "+1 verificato" }));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/participants/12/plus-one",
      expect.objectContaining({ method: "PUT", body: JSON.stringify({ verified: true }) }),
    );
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it("shows who verified and when, and lets the admin take it back", async () => {
    const fetchMock = stub();
    render(
      <PlusOneToggle
        {...base}
        verified
        verifiedAt="2026-11-05T09:04:00Z"
        verifiedBy="Boss Admin"
        onChanged={vi.fn()}
      />,
    );
    const box = screen.getByRole("checkbox", { name: "+1 verificato" });
    expect(box).toBeChecked();
    expect(box).toHaveAccessibleDescription(/Verificato da Boss Admin il 5 novembre 2026/);
    await userEvent.click(box);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/participants/12/plus-one",
      expect.objectContaining({ body: JSON.stringify({ verified: false }) }),
    );
  });

  it("is not available when nobody is named as the one who invited", () => {
    render(<PlusOneToggle {...base} invitedBy="  " onChanged={vi.fn()} />);
    const box = screen.getByRole("checkbox", { name: "+1 verificato" });
    expect(box).toBeDisabled();
    expect(box).toHaveAccessibleDescription(
      "Serve che la persona abbia indicato chi l'ha invitata.",
    );
  });

  it("shows the server refusal and does not reload", async () => {
    stub(422, { detail: "Per verificare un +1 serve il nome di chi lo ha invitato" });
    const onChanged = vi.fn();
    render(<PlusOneToggle {...base} onChanged={onChanged} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "+1 verificato" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Per verificare un +1");
    expect(onChanged).not.toHaveBeenCalled();
  });
});
