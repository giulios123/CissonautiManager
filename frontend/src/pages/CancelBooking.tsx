import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { api, ApiError } from "../api";
import type { BookingView } from "../auth";
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
  const keepRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const wasOpen = useRef(false);

  // Focus moves into the dialog on the harmless choice, and goes back to the trigger on close.
  useEffect(() => {
    if (open) keepRef.current?.focus();
    else if (wasOpen.current) triggerRef.current?.focus();
    wasOpen.current = open;
  }, [open]);

  function close() {
    setOpen(false);
    setError(null);
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.stopPropagation();
      close();
      return;
    }
    if (event.key !== "Tab") return;
    const buttons = [...(dialogRef.current?.querySelectorAll("button") ?? [])];
    const first = buttons[0];
    const last = buttons[buttons.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
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
        <div className="backdrop">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-title"
            aria-describedby="cancel-text"
            ref={dialogRef}
            onKeyDown={onKeyDown}
          >
            <h2 id="cancel-title">Vuoi disdire l&apos;iscrizione?</h2>
            <div id="cancel-text">
              <p>
                I tuoi posti si liberano subito e non potrai riaverli senza iscriverti di nuovo.
              </p>
              {booking.paid_cents > 0 ? (
                <p>
                  Hai già versato {formatEuro(booking.paid_cents)}: chi organizza ti scriverà per il
                  rimborso.
                </p>
              ) : (
                <p>Non risultano pagamenti, quindi l&apos;iscrizione viene annullata.</p>
              )}
            </div>
            {error && (
              <p role="alert" className="notice error">
                {error}
              </p>
            )}
            <div className="actions">
              <button type="button" className="secondary" ref={keepRef} onClick={close}>
                No, torno indietro
              </button>
              <button type="button" className="danger" onClick={confirm} disabled={working}>
                Sì, disdico
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
