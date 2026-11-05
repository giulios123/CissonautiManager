import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";

export function AdminLayout() {
  const navigate = useNavigate();

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate("/accedi");
  }

  return (
    <>
      <header className="admin-nav">
        <nav aria-label="Pannello organizzatori">
          <NavLink to="/admin" end>
            Persone
          </NavLink>
          <NavLink to="/admin/giorni">Giorni e slot</NavLink>
          <NavLink to="/admin/impostazioni">Impostazioni</NavLink>
          <button type="button" className="link" onClick={logout}>
            Esci
          </button>
        </nav>
      </header>
      <Outlet />
    </>
  );
}
