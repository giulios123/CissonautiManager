import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each([
    ["in_attesa_pagamento", "In attesa di pagamento"],
    ["confermata", "Confermata"],
    ["scaduta", "Scaduta"],
    ["disdetta_richiesta", "Disdetta richiesta"],
    ["rimborsata", "Rimborsata"],
  ])("shows %s with its label and color class", (status, label) => {
    render(<StatusBadge status={status} />);
    const badge = screen.getByText(label);
    expect(badge).toHaveClass("status", `status-${status}`);
  });

  it("shows an unknown status as it is, without a color class", () => {
    render(<StatusBadge status="sconosciuto" />);
    expect(screen.getByText("sconosciuto")).toHaveAttribute("class", "status");
  });
});
