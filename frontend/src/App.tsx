import { Link, Route, Routes } from "react-router-dom";
import { RequireLogin } from "./auth";
import { AdminLayout } from "./pages/AdminLayout";
import { AdminRegistrationDetail } from "./pages/AdminRegistrationDetail";
import { AdminRegistrations } from "./pages/AdminRegistrations";
import { AdminSlots } from "./pages/AdminSlots";
import { AdminSettings } from "./pages/AdminSettings";
import { Login } from "./pages/Login";
import { Personal } from "./pages/Personal";
import { Registration } from "./pages/Registration";
import { Verify } from "./pages/Verify";

function Home() {
  return (
    <main>
      <h1>Cissonauti Summer Camp</h1>
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
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/iscrizione" element={<Registration />} />
      <Route path="/accedi" element={<Login />} />
      <Route path="/accedi/verifica" element={<Verify />} />
      <Route path="/io" element={<Personal />} />
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
        <Route path="impostazioni" element={<AdminSettings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
