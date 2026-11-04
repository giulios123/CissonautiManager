import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { api } from "./api";

export type Me = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: "participant" | "admin";
  personal_code: string;
  has_password: boolean;
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
