import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { App } from "./App";

export const adminMe = {
  id: 1,
  first_name: "Boss",
  last_name: "Admin",
  email: "boss@example.com",
  role: "admin",
  personal_code: "CSC-0001",
  has_password: true,
  bookings: [],
  payment_channels: [],
};

export type Reply = { status?: number; body: unknown };
export type Call = { method: string; url: string; body?: unknown };

/** Stubs fetch for an admin session. `handler` answers everything except /api/me. */
export function stubAdminApi(handler: (call: Call) => Reply | undefined): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call: Call = {
        method: init?.method ?? "GET",
        url,
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      if (url === "/api/me") return new Response(JSON.stringify(adminMe), { status: 200 });
      const { status = 200, body } = handler(call) ?? { status: 404, body: {} };
      return new Response(status === 204 ? null : JSON.stringify(body), { status });
    }),
  );
  return calls;
}

export function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
