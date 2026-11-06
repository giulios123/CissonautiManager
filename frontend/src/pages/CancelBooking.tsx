import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT } from "../i18n";
import { formatEuro } from "../money";

export type CancelOutcome = "removed" | "requested";

export function CancelBooking({
  booking,
  onDone,
}: {
  booking: BookingView;
  onDone: (outcome: CancelOutcome) => Promise<void> | void;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  function close() {
    setOpen(false);
    setError(null);
  }

  async function confirm() {
    setError(null);
    setWorking(true);
    try {
      const result = await api<{ outcome: CancelOutcome }>("/api/me/booking/cancel", {
        method: "POST",
      });
      setOpen(false);
      await onDone(result.outcome);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <button type="button" className="danger" ref={triggerRef} onClick={() => setOpen(true)}>
        {t("cancel.button")}
      </button>
      {open && (
        <ConfirmDialog
          title={t("cancel.title")}
          confirmLabel={t("cancel.confirm")}
          working={working}
          error={error}
          onConfirm={confirm}
          onCancel={close}
          returnFocusTo={triggerRef}
        >
          <p>{t("cancel.warning")}</p>
          {booking.paid_cents > 0 ? (
            <p>{t("cancel.paid", { amount: formatEuro(booking.paid_cents) })}</p>
          ) : (
            <p>{t("cancel.unpaid")}</p>
          )}
        </ConfirmDialog>
      )}
    </>
  );
}
