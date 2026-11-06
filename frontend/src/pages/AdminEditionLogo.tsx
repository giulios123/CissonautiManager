import { useState, type ChangeEvent } from "react";
import { api, ApiError } from "../api";
import bundledLogoUrl from "../assets/logo-cissone.png";
import { useEventName, useRefreshEventName } from "../eventName";
import { useT } from "../i18n";

type Notice = { kind: "ok" | "error"; text: string } | null;

export function AdminEditionLogo({
  logoUrl,
  onSaved,
}: {
  logoUrl: string | null;
  onSaved: (logoUrl: string | null) => void;
}) {
  const t = useT();
  const eventName = useEventName();
  const refreshEdition = useRefreshEventName();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const [previewFailed, setPreviewFailed] = useState(false);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;

    setBusy(true);
    setNotice(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const edition = await api<{ logo_url: string | null }>("/api/admin/edition/logo", {
        method: "PUT",
        body: form,
      });
      setPreviewFailed(false);
      onSaved(edition.logo_url);
      refreshEdition();
      setNotice({ kind: "ok", text: t("set.logoSaved") });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : t("common.somethingWrong");
      setNotice({ kind: "error", text: message });
    } finally {
      input.value = "";
      setBusy(false);
    }
  }

  async function restore() {
    setBusy(true);
    setNotice(null);
    try {
      const edition = await api<{ logo_url: string | null }>("/api/admin/edition/logo", {
        method: "DELETE",
      });
      setPreviewFailed(false);
      onSaved(edition.logo_url);
      refreshEdition();
      setNotice({ kind: "ok", text: t("set.logoRestored") });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : t("common.somethingWrong");
      setNotice({ kind: "error", text: message });
    } finally {
      setBusy(false);
    }
  }

  const previewUrl = previewFailed ? bundledLogoUrl : logoUrl || bundledLogoUrl;

  return (
    <section aria-labelledby="edition-logo-title" className="edition-logo">
      <h2 id="edition-logo-title">{t("set.logoTitle")}</h2>
      <p>{t("set.logoIntro")}</p>
      <img
        className="edition-logo-preview"
        src={previewUrl}
        alt={t("set.logoPreviewAlt", { name: eventName })}
        onError={() => setPreviewFailed(true)}
      />
      <label>
        {t("set.logoFile")}
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          disabled={busy}
          onChange={upload}
        />
      </label>
      {logoUrl && (
        <button type="button" className="secondary" onClick={restore} disabled={busy}>
          {t("set.logoRestore")}
        </button>
      )}
      {notice && (
        <p role={notice.kind === "error" ? "alert" : "status"} className={`notice ${notice.kind}`}>
          {notice.text}
        </p>
      )}
    </section>
  );
}
