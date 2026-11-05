import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { formatDeadline, toRomeLocalInput } from "../booking";
import { useT } from "../i18n";
import type { Detail } from "./AdminRegistrationDetail";

type Props = {
  bookingId: number;
  status: string;
  holdExpiresAt: string;
  onDone: (detail: Detail, text: string) => void;
};

/** Extend a pending hold, or bring an expired booking back. */
export function AdminHoldActions({ bookingId, status, holdExpiresAt, onDone }: Props) {
  const t = useT();
  const [error, setError] = useState<string | null>(null);

  async function call(request: Promise<Detail>, text: string) {
    setError(null);
    try {
      onDone(await request, text);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    }
  }

  function extend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const hold = String(new FormData(event.currentTarget).get("hold") ?? "");
    // Without a time zone, the server reads the value as Rome time.
    void call(
      api<Detail>(`/api/admin/registrations/${bookingId}`, {
        method: "PATCH",
        json: { hold_expires_at: hold },
      }),
      t("dsub.holdExtended"),
    );
  }

  if (status === "in_attesa_pagamento") {
    return (
      <form onSubmit={extend} aria-labelledby="extend-title" key={holdExpiresAt}>
        <h2 id="extend-title">{t("dsub.extendTitle")}</h2>
        <p>{t("dsub.extendBody", { date: formatDeadline(holdExpiresAt) })}</p>
        <label>
          {t("dsub.newDeadline")}
          <input
            type="datetime-local"
            name="hold"
            defaultValue={toRomeLocalInput(holdExpiresAt)}
            required
          />
        </label>
        <button type="submit">{t("dsub.extend")}</button>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
      </form>
    );
  }

  if (status === "scaduta") {
    return (
      <section aria-labelledby="revive-title">
        <h2 id="revive-title">{t("dsub.reviveTitle")}</h2>
        <p>{t("dsub.reviveBody")}</p>
        <button
          type="button"
          onClick={() =>
            void call(
              api<Detail>(`/api/admin/registrations/${bookingId}/reactivate`, { method: "POST" }),
              t("dsub.reactivated"),
            )
          }
        >
          {t("dsub.reviveTitle")}
        </button>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
      </section>
    );
  }
  return null;
}
