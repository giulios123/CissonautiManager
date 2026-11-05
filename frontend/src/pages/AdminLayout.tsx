import { useEffect } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { adminGuideLink } from "../guide/content";

export function AdminLayout() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // On a phone the menu scrolls sideways: keep the current page in view.
  useEffect(() => {
    const current = document.querySelector<HTMLElement>('.admin-nav a[aria-current="page"]');
    current?.scrollIntoView?.({ inline: "center", block: "nearest" });
  }, [pathname]);

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate("/login");
  }

  return (
    <>
      <div className="admin-nav">
        <nav aria-label="Pannello organizzatori">
          <NavLink to="/admin" end>
            Persone
          </NavLink>
          <NavLink to="/admin/days">Giorni e slot</NavLink>
          <NavLink to="/admin/week">Settimana</NavLink>
          <NavLink to="/admin/meals">Pasti</NavLink>
          <NavLink to="/admin/activities">Attività</NavLink>
          <NavLink to="/admin/contributions">Contributi</NavLink>
          <NavLink to="/admin/report">Report</NavLink>
          <NavLink to="/admin/to-collect">Da incassare</NavLink>
          <NavLink to="/admin/to-review">Da verificare</NavLink>
          <NavLink to="/admin/admins">Admin</NavLink>
          <NavLink to="/admin/settings">Impostazioni</NavLink>
          <Link to={adminGuideLink(pathname)}>Guida</Link>
          <button type="button" className="link" onClick={logout}>
            Esci
          </button>
        </nav>
      </div>
      <Outlet />
    </>
  );
}
