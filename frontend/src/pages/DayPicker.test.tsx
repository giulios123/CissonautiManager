import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import type { PickerDay } from "../daySelection";
import { DayPicker } from "./DayPicker";

const slot = (id: number, period: string, extra = {}) => ({
  id,
  period,
  start_time: period === "morning" ? "09:00:00" : period === "afternoon" ? "14:00:00" : "19:00:00",
  end_time: period === "morning" ? "13:00:00" : period === "afternoon" ? "18:00:00" : "00:00:00",
  hint: "10 posti liberi",
  disabled: false,
  full: false,
  ...extra,
});

const DAYS: PickerDay[] = [
  { date: "2026-11-20", slots: [slot(1, "morning"), slot(2, "afternoon"), slot(3, "evening")] },
  {
    date: "2026-11-21",
    slots: [slot(4, "morning"), slot(5, "afternoon", { disabled: true }), slot(6, "evening")],
  },
];

function Harness() {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  return (
    <>
      <DayPicker days={DAYS} selected={selected} onChange={setSelected} />
      <output>{[...selected].sort().join(",")}</output>
    </>
  );
}

const picked = () => screen.getByRole("status").textContent;

describe("DayPicker", () => {
  it("selects a slot by clicking its tile", async () => {
    render(<Harness />);
    await userEvent.click(screen.getAllByText("Pomeriggio", { selector: ".tile-title" })[0]);
    expect(picked()).toBe("2");
  });

  it("selects the whole day, skipping what is locked, and clears it on a second click", async () => {
    render(<Harness />);
    const second = screen.getAllByRole("group")[1];
    const all = within(second).getByRole("button", { name: /Tutta la giornata/ });
    await userEvent.click(all);
    expect(picked()).toBe("4,6");
    expect(all).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(all);
    expect(picked()).toBe("");
  });

  it("selects a part of the day on every day", async () => {
    render(<Harness />);
    await userEvent.click(screen.getByRole("button", { name: "Tutta la mattina" }));
    expect(picked()).toBe("1,4");
    await userEvent.click(screen.getByRole("button", { name: "Tutta la sera" }));
    expect(picked()).toBe("1,3,4,6");
  });

  it("selects and clears everything", async () => {
    render(<Harness />);
    await userEvent.click(screen.getByRole("button", { name: "Seleziona tutto" }));
    expect(picked()).toBe("1,2,3,4,6");
    await userEvent.click(screen.getByRole("button", { name: "Deseleziona tutto" }));
    expect(picked()).toBe("");
    expect(screen.getByRole("button", { name: "Deseleziona tutto" })).toBeDisabled();
  });

  it("keeps the readable name of each slot for screen readers", () => {
    render(<Harness />);
    expect(
      screen.getAllByRole("checkbox", { name: "Mattina 09:00-13:00 · 10 posti liberi" }),
    ).toHaveLength(2);
    expect(screen.getAllByRole("checkbox", { name: /Pomeriggio/ })[1]).toBeDisabled();
  });
});
