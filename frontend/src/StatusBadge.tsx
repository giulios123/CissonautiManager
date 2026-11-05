import { statusLabel } from "./booking";

const KNOWN = new Set([
  "in_attesa_pagamento",
  "confermata",
  "scaduta",
  "disdetta_richiesta",
  "rimborsata",
]);

/** Booking status as a colored label. The text is always there: color only helps. */
export function StatusBadge({ status }: { status: string }) {
  const className = KNOWN.has(status) ? `status status-${status}` : "status";
  return <span className={className}>{statusLabel(status)}</span>;
}
