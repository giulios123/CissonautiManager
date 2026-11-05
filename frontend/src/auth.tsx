import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { api } from "./api";

export type MealView = { date: string; kind: "lunch" | "dinner"; label: string; past?: boolean };

export type BookingView = {
  id: number;
  status: string;
  amount_due_cents: number;
  paid_cents: number;
  balance_cents: number;
  hold_expires_at: string;
  editable: boolean;
  can_cancel: boolean;
  slots: { id: number; date: string; period: string; label: string }[];
  payments: {
    id: number;
    amount_cents: number;
    channel: string;
    paid_on: string;
    note?: string | null;
    voided?: boolean;
    void_reason?: string | null;
  }[];
  meals?: MealView[];
  allowed_meals?: MealView[];
  dropped_meals?: string[];
  diet?: string | null;
  allergies?: string | null;
  health_consent_version?: number | null;
};

export type WaitlistItem = {
  id: number;
  slot_id: number;
  date: string;
  period: string;
  label: string;
  position: number;
};

export type Me = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: "participant" | "admin";
  personal_code: string;
  has_password: boolean;
  bookings: BookingView[];
  payment_channels: { code: string; label: string; instructions: string }[];
  waitlist?: WaitlistItem[];
  lunch_price_cents?: number | null;
  dinner_price_cents?: number | null;
  health_consent?: { version: number; body: string } | null;
};

type MeState = { status: "loading" } | { status: "anonymous" } | { status: "user"; me: Me };

export function useMe(): MeState {
  const [state, setState] = useState<MeState>({ status: "loading" });
  useEffect(() => {
    api<Me>("/api/me")
      .then((me) => setState({ status: "user", me }))
      .catch(() => setState({ status: "anonymous" }));
  }, []);
  return state;
}

export function RequireLogin({
  admin = false,
  children,
}: {
  admin?: boolean;
  children: ReactNode;
}) {
  const state = useMe();
  if (state.status === "loading") return <main aria-busy="true">Caricamento…</main>;
  if (state.status === "anonymous") return <Navigate to="/accedi" replace />;
  if (admin && state.me.role !== "admin") {
    return (
      <main>
        <h1>Accesso riservato</h1>
        <p>Questa pagina è riservata agli organizzatori.</p>
      </main>
    );
  }
  return <>{children}</>;
}
