import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
import { ConfirmDialog } from "../ConfirmDialog";
import { formatEuro } from "../money";

export type CancelOutcome = "removed" | "requested";

export function CancelBooking({
  booking,
  onDone,
}: {
  booking: BookingView;
  onDone: (outcome: CancelOutcome) => Promise<void> | void;
}) {
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
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <>
      <button type="button" className="danger" ref={triggerRef} onClick={() => setOpen(true)}>
        Richiedi disdetta
      </button>
      {open && (
        <ConfirmDialog
          title="Vuoi disdire l'iscrizione?"
          confirmLabel="Sì, disdico"
          working={working}
          error={error}
          onConfirm={confirm}
          onCancel={close}
          returnFocusTo={triggerRef}
        >
          <p>I tuoi posti si liberano subito e non potrai riaverli senza iscriverti di nuovo.</p>
          {booking.paid_cents > 0 ? (
            <p>
              Hai già versato {formatEuro(booking.paid_cents)}: chi organizza ti scriverà per il
              rimborso.
            </p>
          ) : (
            <p>Non risultano pagamenti, quindi l&apos;iscrizione viene annullata.</p>
          )}
        </ConfirmDialog>
      )}
    </>
  );
}
