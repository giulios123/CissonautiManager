import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT } from "../i18n";

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
  const t = useT();
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
        text: t(result.created ? "aadm.added" : "aadm.nowAdmin", {
          name: `${result.first_name} ${result.last_name}`,
        }),
      });
      await load();
    } catch (caught) {
      setNotice({
        ok: false,
        text: caught instanceof ApiError ? caught.message : t("common.retryShortly"),
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
        text: t("aadm.removed", { name: `${removing.first_name} ${removing.last_name}` }),
      });
      setRemoving(null);
      await load();
    } catch (caught) {
      setDialogError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <main className="wide">
      <h1>{t("aadm.title")}</h1>
      <p>{t("aadm.intro")}</p>
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
      {failed && <p role="alert">{t("aadm.loadError")}</p>}
      {admins === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <caption>{t("aadm.caption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("aadm.colName")}</th>
                <th scope="col">{t("login.email")}</th>
                <th scope="col">{t("aact.colActions")}</th>
              </tr>
            </thead>
            <tbody>
              {admins.map((admin) => (
                <tr key={admin.id}>
                  <th scope="row">
                    {admin.first_name} {admin.last_name}
                    {admin.is_you && <small>{t("aadm.you")}</small>}
                  </th>
                  <td>{admin.email}</td>
                  <td>
                    {admin.removable ? (
                      <button
                        type="button"
                        className="secondary"
                        aria-label={t("aadm.removeAria", {
                          name: `${admin.first_name} ${admin.last_name}`,
                        })}
                        onClick={(event) => {
                          clickedRef.current = event.currentTarget;
                          setRemoving(admin);
                        }}
                      >
                        {t("aadm.remove")}
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
        <h2 id="add-title">{t("aadm.addTitle")}</h2>
        <label>
          {t("login.email")}
          <input type="email" name="email" autoComplete="off" required />
        </label>
        <p className="legal">{t("aadm.addHint")}</p>
        <div className="row">
          <label>
            {t("reg.firstName")}
            <input name="first_name" autoComplete="off" maxLength={100} />
          </label>
          <label>
            {t("reg.lastName")}
            <input name="last_name" autoComplete="off" maxLength={100} />
          </label>
        </div>
        <button type="submit">{t("aadm.addButton")}</button>
      </form>

      {removing && (
        <ConfirmDialog
          title={t("aadm.removeTitle", { name: `${removing.first_name} ${removing.last_name}` })}
          confirmLabel={t("aadm.removeConfirm")}
          working={working}
          error={dialogError}
          onConfirm={remove}
          onCancel={() => {
            setRemoving(null);
            setDialogError(null);
          }}
          returnFocusTo={clickedRef}
        >
          <p>{t("aadm.removeBody")}</p>
        </ConfirmDialog>
      )}
    </main>
  );
}
