import { Link, Route, Routes } from "react-router-dom";
import { RequireLogin } from "./auth";
import { AdminSettings } from "./pages/AdminSettings";
import { Login } from "./pages/Login";
import { Personal } from "./pages/Personal";
import { Registration } from "./pages/Registration";
import { Verify } from "./pages/Verify";

function Home() {
  return (
    <main>
      <h1>Cisonauti Summer Camp</h1>
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
        path="/admin/impostazioni"
        element={
          <RequireLogin admin>
            <AdminSettings />
          </RequireLogin>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
