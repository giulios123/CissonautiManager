import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { ConfirmDialog } from "../ConfirmDialog";
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
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <button type="button" className="danger" ref={triggerRef} onClick={() => setOpen(true)}>
        Disdici a nome della persona
      </button>
      {open && (
        <ConfirmDialog
          title="Disdire l'iscrizione a nome della persona?"
          confirmLabel="Sì, disdico"
          working={working}
          error={error}
          onConfirm={confirm}
          onCancel={() => {
            setOpen(false);
            setError(null);
          }}
          returnFocusTo={triggerRef}
        >
          <p>I posti si liberano subito e alla persona arriva l&apos;email di conferma.</p>
          {booking.paid_cents > 0 ? (
            <p>
              Ha già versato {formatEuro(booking.paid_cents)}: la disdetta resta aperta finché non
              registri il rimborso.
            </p>
          ) : (
            <p>Non risultano pagamenti, quindi l&apos;iscrizione viene rimossa.</p>
          )}
        </ConfirmDialog>
      )}
    </>
  );
}
