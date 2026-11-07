import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { api } from "./api";
import { useT } from "./i18n";
import { ROUTES } from "./routes";
import type { CollectionTerms } from "./collection";
import type { LegalDocumentText } from "./legalText";

export type MealView = CollectionTerms & {
  date: string;
  kind: "lunch" | "dinner";
  label: string;
  past?: boolean;
};

export type BookingView = {
  id: number;
  status: string;
  confirmation_policy?: "legacy_total" | "registration_fee";
  registration_fee_cents?: number | null;
  confirmation_due_cents?: number | null;
  confirmation_balance_cents?: number | null;
  amount_due_cents: number;
  paid_cents: number;
  balance_cents: number;
  hold_expires_at: string;
  editable: boolean;
  can_cancel: boolean;
  slots: { id: number; date: string; period: string; label: string }[];
  schedule: { date: string; period: string; start_time: string; end_time: string }[];
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
  activities?: (CollectionTerms & {
    id: number;
    title: string;
    label: string;
    price_cents: number;
    time_label?: string | null;
  })[];
  dropped_meals?: string[];
  dropped_activities?: string[];
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
  locale?: "it" | "en";
  bookings: BookingView[];
  payment_channels: { code: string; label: string; instructions: string }[];
  waitlist?: WaitlistItem[];
  lunch_price_cents?: number | null;
  dinner_price_cents?: number | null;
  health_consent?: (LegalDocumentText & { version: number }) | null;
  activities?: ActivityOffer[];
  contributions?: Contribution[];
  can_bring?: string | null;
};

export type Contribution = {
  id: number;
  kind: "talk" | "topic" | "skill";
  title: string;
  description: string | null;
};

export type ActivityOffer = CollectionTerms & {
  id: number;
  title: string;
  description: string | null;
  date: string;
  period: string;
  time_label: string | null;
  price_cents: number;
  capacity: number | null;
  free: number | null;
  joined: boolean;
  past: boolean;
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
  const t = useT();
  const state = useMe();
  if (state.status === "loading") return <main aria-busy="true">{t("common.loading")}</main>;
  if (state.status === "anonymous") return <Navigate to={ROUTES.login} replace />;
  if (admin && state.me.role !== "admin") {
    return (
      <main>
        <h1>{t("auth.restrictedTitle")}</h1>
        <p>{t("auth.restrictedBody")}</p>
      </main>
    );
  }
  return <>{children}</>;
}
