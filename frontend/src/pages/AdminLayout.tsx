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
    navigate("/accedi");
  }

  return (
    <>
      <div className="admin-nav">
        <nav aria-label="Pannello organizzatori">
          <NavLink to="/admin" end>
            Persone
          </NavLink>
          <NavLink to="/admin/giorni">Giorni e slot</NavLink>
          <NavLink to="/admin/settimana">Settimana</NavLink>
          <NavLink to="/admin/pasti">Pasti</NavLink>
          <NavLink to="/admin/attivita">Attività</NavLink>
          <NavLink to="/admin/contributi">Contributi</NavLink>
          <NavLink to="/admin/report">Report</NavLink>
          <NavLink to="/admin/da-incassare">Da incassare</NavLink>
          <NavLink to="/admin/da-verificare">Da verificare</NavLink>
          <NavLink to="/admin/amministratori">Admin</NavLink>
          <NavLink to="/admin/testi">Testi</NavLink>
          <NavLink to="/admin/impostazioni">Impostazioni</NavLink>
          <Link to="/io">La mia pagina</Link>
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
