import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";

type AdminRow = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  is_you: boolean;
  removable: boolean;
  blocked_reason: string | null;
};
type Notice = { ok: boolean; text: string };

export function AdminAdmins() {
  const [admins, setAdmins] = useState<AdminRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [removing, setRemoving] = useState<AdminRow | null>(null);
  const [dialogError, setDialogError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const clickedRef = useRef<HTMLButtonElement | null>(null);

  const load = useCallback(
    () =>
      api<AdminRow[]>("/api/admin/admins")
        .then(setAdmins)
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    try {
      const result = await api<{ created: boolean; first_name: string; last_name: string }>(
        "/api/admin/admins",
        {
          method: "POST",
          json: {
            email: text("email"),
            first_name: text("first_name") || null,
            last_name: text("last_name") || null,
          },
        },
      );
      form.reset();
      setNotice({
        ok: true,
        text: result.created
          ? `${result.first_name} ${result.last_name} è stato aggiunto come admin. Può entrare da «Accedi» con il link via email.`
          : `${result.first_name} ${result.last_name} ora è admin.`,
      });
      await load();
    } catch (caught) {
      setNotice({
        ok: false,
        text: caught instanceof ApiError ? caught.message : "Riprova tra poco.",
      });
    }
  }

  async function remove() {
    if (!removing) return;
    setWorking(true);
    setDialogError(null);
    try {
      await api(`/api/admin/admins/${removing.id}`, { method: "DELETE" });
      setNotice({
        ok: true,
        text: `${removing.first_name} ${removing.last_name} non è più admin.`,
      });
      setRemoving(null);
      await load();
    } catch (caught) {
      setDialogError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <main className="wide">
      <h1>Admin</h1>
      <p>Gli admin vedono e modificano tutto. Non c&apos;è un limite al loro numero.</p>
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
      {failed && <p role="alert">Non riesco a caricare gli admin.</p>}
      {admins === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : (
        <div className="table-wrap">
          <table>
            <caption>Admin attuali</caption>
            <thead>
              <tr>
                <th scope="col">Nome</th>
                <th scope="col">Email</th>
                <th scope="col">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {admins.map((admin) => (
                <tr key={admin.id}>
                  <th scope="row">
                    {admin.first_name} {admin.last_name}
                    {admin.is_you && <small> (tu)</small>}
                  </th>
                  <td>{admin.email}</td>
                  <td>
                    {admin.removable ? (
                      <button
                        type="button"
                        className="secondary"
                        aria-label={`Rimuovi ${admin.first_name} ${admin.last_name}`}
                        onClick={(event) => {
                          clickedRef.current = event.currentTarget;
                          setRemoving(admin);
                        }}
                      >
                        Rimuovi
                      </button>
                    ) : (
                      <small>{admin.blocked_reason}</small>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={add} aria-labelledby="add-title">
        <h2 id="add-title">Aggiungi un admin</h2>
        <label>
          Email
          <input type="email" name="email" autoComplete="off" required />
        </label>
        <p className="legal">
          Se la persona è già iscritta basta l&apos;email. Se è nuova servono anche nome e cognome.
        </p>
        <div className="row">
          <label>
            Nome
            <input name="first_name" autoComplete="off" maxLength={100} />
          </label>
          <label>
            Cognome
            <input name="last_name" autoComplete="off" maxLength={100} />
          </label>
        </div>
        <button type="submit">Aggiungi admin</button>
      </form>

      {removing && (
        <ConfirmDialog
          title={`Rimuovere ${removing.first_name} ${removing.last_name} dagli admin?`}
          confirmLabel="Sì, rimuovo"
          working={working}
          error={dialogError}
          onConfirm={remove}
          onCancel={() => {
            setRemoving(null);
            setDialogError(null);
          }}
          returnFocusTo={clickedRef}
        >
          <p>
            Resta una persona normale e la sua eventuale iscrizione non cambia, ma perde subito
            l&apos;accesso al pannello.
          </p>
        </ConfirmDialog>
      )}
    </main>
  );
}
