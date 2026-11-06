import { Link, Route, Routes } from "react-router-dom";
import { RequireLogin } from "./auth";
import { AdminAdmins } from "./pages/AdminAdmins";
import { AdminActivities } from "./pages/AdminActivities";
import { AdminActivityDetail } from "./pages/AdminActivityDetail";
import { AdminContributions } from "./pages/AdminContributions";
import { AdminMeals } from "./pages/AdminMeals";
import { AdminLayout } from "./pages/AdminLayout";
import { AdminRegistrationDetail } from "./pages/AdminRegistrationDetail";
import { AdminReport } from "./pages/AdminReport";
import { AdminRegistrations } from "./pages/AdminRegistrations";
import { AdminCollect } from "./pages/AdminCollect";
import { AdminReview } from "./pages/AdminReview";
import { AdminSlots } from "./pages/AdminSlots";
import { AdminWeek } from "./pages/AdminWeek";
import { AdminSettings } from "./pages/AdminSettings";
import { AdminTexts } from "./pages/AdminTexts";
import { Guide } from "./pages/Guide";
import { Login } from "./pages/Login";
import { Personal } from "./pages/Personal";
import { Registration } from "./pages/Registration";
import { Verify } from "./pages/Verify";
import { EventNameProvider, useEventName } from "./eventName";
import { usePageTitle } from "./pageTitle";
import { SiteHeader } from "./SiteHeader";

function Home() {
  const eventName = useEventName();
  return (
    <main>
      <h1>{eventName}</h1>
      <p>
        <Link to="/iscrizione">Iscriviti al camp</Link>
      </p>
    </main>
  );
}

function NotFound() {
  return (
    <main>
      <h1>Pagina non trovata</h1>
      <p>
        <Link to="/">Torna alla home</Link>
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
        <Route path="/iscrizione" element={<Registration />} />
        <Route path="/accedi" element={<Login />} />
        <Route path="/accedi/verifica" element={<Verify />} />
        <Route path="/io" element={<Personal />} />
        <Route path="/guida" element={<Guide />} />
        <Route
          path="/admin"
          element={
            <RequireLogin admin>
              <AdminLayout />
            </RequireLogin>
          }
        >
          <Route index element={<AdminRegistrations />} />
          <Route path="iscrizioni/:id" element={<AdminRegistrationDetail />} />
          <Route path="giorni" element={<AdminSlots />} />
          <Route path="settimana" element={<AdminWeek />} />
          <Route path="pasti" element={<AdminMeals />} />
          <Route path="attivita" element={<AdminActivities />} />
          <Route path="attivita/:id" element={<AdminActivityDetail />} />
          <Route path="contributi" element={<AdminContributions />} />
          <Route path="report" element={<AdminReport />} />
          <Route path="da-incassare" element={<AdminCollect />} />
          <Route path="da-verificare" element={<AdminReview />} />
          <Route path="amministratori" element={<AdminAdmins />} />
          <Route path="testi" element={<AdminTexts />} />
          <Route path="impostazioni" element={<AdminSettings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
