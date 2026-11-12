import { Fragment, useEffect } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ADMIN_GUIDE_LINK } from "../guide/content";
import { useI18n } from "../i18n";
import { ROUTES } from "../routes";

export function AdminLayout() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // On a phone the menu scrolls sideways: keep the current page in view.
  useEffect(() => {
    const current = document.querySelector<HTMLElement>('.admin-nav a[aria-current="page"]');
    current?.scrollIntoView?.({ inline: "center", block: "nearest" });
  }, [pathname]);

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    navigate(ROUTES.login);
  }

  return (
    <>
      <div className="admin-nav">
        <nav aria-label={t("adm.navLabel")}>
          <NavLink to="/admin" end>
            {t("adm.navPeople")}
          </NavLink>
          <NavLink to="/admin/days">{t("adm.navDays")}</NavLink>
          <NavLink to="/admin/week">{t("adm.navWeek")}</NavLink>
          <NavLink to="/admin/meals">{t("adm.navMeals")}</NavLink>
          <NavLink to="/admin/activities">{t("adm.navActivities")}</NavLink>
          <NavLink to="/admin/guests">{t("adm.navGuests")}</NavLink>
          <NavLink to="/admin/deliveries">{t("adm.navDeliveries")}</NavLink>
          <NavLink to="/admin/contributions">{t("adm.navContributions")}</NavLink>
          <NavLink to="/admin/report">{t("adm.navReport")}</NavLink>
          <NavLink to="/admin/to-collect">{t("adm.navToCollect")}</NavLink>
          <NavLink to="/admin/to-review">{t("adm.navToReview")}</NavLink>
          <NavLink to="/admin/admins">{t("adm.navAdmins")}</NavLink>
          <NavLink to="/admin/settings">{t("adm.navSettings")}</NavLink>
          <Link to={ROUTES.me}>{t("adm.navMine")}</Link>
          <Link to={ADMIN_GUIDE_LINK}>{t("adm.navGuide")}</Link>
          <button type="button" className="link" onClick={logout}>
            {t("me.logout")}
          </button>
        </nav>
      </div>
      {/* Pages show labels the server writes in the language of the request: a new language
          means asking again, so they start over. "To collect" is the exception: it shows nothing
          written by the server, and starting over would lose the payments marked a moment ago
          and their 10-second undo, while the confirmation email is still on its way. */}
      <Fragment key={pathname === ROUTES.adminToCollect ? "stable" : locale}>
        <Outlet />
      </Fragment>
    </>
  );
}
