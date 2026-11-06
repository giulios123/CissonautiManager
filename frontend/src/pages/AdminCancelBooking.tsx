import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { ConfirmDialog } from "../ConfirmDialog";
import { useT } from "../i18n";
import { formatEuro } from "../money";
import type { Detail } from "./AdminRegistrationDetail";

export type AdminCancelResult = { outcome: "removed" | "requested"; detail: Detail | null };

export function AdminCancelBooking({
  bookingId,
  booking,
  onDone,
}: {
  bookingId: number;
  booking: BookingView;
  onDone: (result: AdminCancelResult) => void;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  async function confirm() {
    setWorking(true);
    setError(null);
    try {
      const result = await api<AdminCancelResult>(`/api/admin/registrations/${bookingId}/cancel`, {
        method: "POST",
      });
      setOpen(false);
      onDone(result);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("common.retryShortly"));
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <button type="button" className="danger" ref={triggerRef} onClick={() => setOpen(true)}>
        {t("dsub.cancelButton")}
      </button>
      {open && (
        <ConfirmDialog
          title={t("dsub.cancelTitle")}
          confirmLabel={t("dsub.cancelConfirm")}
          working={working}
          error={error}
          onConfirm={confirm}
          onCancel={() => {
            setOpen(false);
            setError(null);
          }}
          returnFocusTo={triggerRef}
        >
          <p>{t("dsub.cancelBody")}</p>
          {booking.paid_cents > 0 ? (
            <p>{t("dsub.cancelPaid", { amount: formatEuro(booking.paid_cents) })}</p>
          ) : (
            <p>{t("dsub.cancelUnpaid")}</p>
          )}
        </ConfirmDialog>
      )}
    </>
  );
}
