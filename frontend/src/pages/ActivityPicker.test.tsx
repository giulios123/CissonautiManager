import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import type { ActivityOffer, BookingView } from "../auth";
import { ActivityPicker } from "./ActivityPicker";

afterEach(() => vi.unstubAllGlobals());

const booking = {
  id: 7,
  status: "confermata",
  amount_due_cents: 2600,
  paid_cents: 0,
  balance_cents: 2600,
  hold_expires_at: "2026-07-04T10:00:00Z",
  editable: true,
  can_cancel: true,
  slots: [],
  schedule: [],
  payments: [],
} as BookingView;

const offer = (id: number, title: string, joined: boolean): ActivityOffer => ({
  id,
  title,
  description: null,
  date: "2026-07-13",
  period: "morning",
  time_label: null,
  start_time: null,
  end_time: null,
  price_cents: 1500,
  capacity: null,
  free: null,
  joined,
  past: false,
});

it("never sends an activity that is no longer offered", async () => {
  const calls: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_url: string, init?: RequestInit) => {
      calls.push(JSON.parse(String(init?.body)));
      return new Response(JSON.stringify({}), { status: 200 });
    }),
  );
  const { rerender } = render(
    <ActivityPicker
      booking={booking}
      offers={[offer(1, "Escursione", true), offer(2, "Yoga", false)]}
      onSaved={() => {}}
    />,
  );
  // A slot change dropped the hike while the picker was open.
  rerender(
    <ActivityPicker booking={booking} offers={[offer(2, "Yoga", false)]} onSaved={() => {}} />,
  );
  await userEvent.click(screen.getByRole("checkbox", { name: /Yoga/ }));
  await userEvent.click(screen.getByRole("button", { name: "Salva le attività" }));
  expect(calls).toEqual([{ activity_ids: [2] }]);
});
