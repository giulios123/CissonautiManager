import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { RequireLogin } from "./auth";
import { AdminAdmins } from "./pages/AdminAdmins";
import { AdminDeliveries } from "./pages/AdminDeliveries";
import { AdminActivities } from "./pages/AdminActivities";
import { AdminActivityDetail } from "./pages/AdminActivityDetail";
import { AdminGuestDetail } from "./pages/AdminGuestDetail";
import { AdminGuests } from "./pages/AdminGuests";
import { AdminContributions } from "./pages/AdminContributions";
import { AdminMeals } from "./pages/AdminMeals";
import { AdminLayout } from "./pages/AdminLayout";
import { AdminRegistrationDetail } from "./pages/AdminRegistrationDetail";
import { AdminReport } from "./pages/AdminReport";
import { AdminRegistrations } from "./pages/AdminRegistrations";
import { AdminCollect } from "./pages/AdminCollect";
import { AdminCancellations } from "./pages/AdminCancellations";
import { AdminReview } from "./pages/AdminReview";
import { AdminSlots } from "./pages/AdminSlots";
import { AdminWeek } from "./pages/AdminWeek";
import { AdminSettings } from "./pages/AdminSettings";
import { Guide } from "./pages/Guide";
import { Login } from "./pages/Login";
import { Personal } from "./pages/Personal";
import { Registration } from "./pages/Registration";
import { Verify } from "./pages/Verify";
import { EventNameProvider, useEventName } from "./eventName";
import { useT } from "./i18n";
import { usePageTitle } from "./pageTitle";
import { canonicalGuideHash, canonicalPath, canonicalSearch, ROUTES } from "./routes";
import { SiteHeader } from "./SiteHeader";

function Home() {
  const t = useT();
  const eventName = useEventName();
  return (
    <main>
      <h1>{eventName}</h1>
      <p>
        <Link to={ROUTES.register}>{t("home.register")}</Link>
      </p>
    </main>
  );
}

/** Italian addresses typed by hand lead to the English ones, keeping query and hash. */
function NotFound() {
  const t = useT();
  const { pathname, search, hash } = useLocation();
  const english = canonicalPath(pathname);
  if (english) {
    // The old guide had Italian section anchors: they follow the renamed sections.
    const anchor = english === ROUTES.guide ? canonicalGuideHash(hash) : hash;
    return <Navigate to={`${english}${canonicalSearch(search)}${anchor}`} replace />;
  }
  return (
    <main>
      <h1>{t("notFound.title")}</h1>
      <p>
        <Link to="/">{t("notFound.home")}</Link>
      </p>
    </main>
  );
}

export function App() {
  return (
    <EventNameProvider>
      <AppRoutes />
    </EventNameProvider>
  );
}

function AppRoutes() {
  usePageTitle();
  return (
    <>
      <SiteHeader />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path={ROUTES.register} element={<Registration />} />
        <Route path={ROUTES.login} element={<Login />} />
        <Route path={ROUTES.loginVerify} element={<Verify />} />
        <Route path={ROUTES.me} element={<Personal />} />
        <Route path={ROUTES.guide} element={<Guide />} />
        <Route
          path="/admin"
          element={
            <RequireLogin admin>
              <AdminLayout />
            </RequireLogin>
          }
        >
          <Route index element={<AdminRegistrations />} />
          <Route path="cancellations" element={<AdminCancellations />} />
          <Route path="registrations/:id" element={<AdminRegistrationDetail />} />
          <Route path="days" element={<AdminSlots />} />
          <Route path="week" element={<AdminWeek />} />
          <Route path="meals" element={<AdminMeals />} />
          <Route path="activities" element={<AdminActivities />} />
          <Route path="activities/:id" element={<AdminActivityDetail />} />
          <Route path="guests" element={<AdminGuests />} />
          <Route path="guests/:id" element={<AdminGuestDetail />} />
          <Route path="deliveries" element={<AdminDeliveries />} />
          <Route path="contributions" element={<AdminContributions />} />
          <Route path="report" element={<AdminReport />} />
          <Route path="to-collect" element={<AdminCollect />} />
          <Route path="to-review" element={<AdminReview />} />
          <Route path="admins" element={<AdminAdmins />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
