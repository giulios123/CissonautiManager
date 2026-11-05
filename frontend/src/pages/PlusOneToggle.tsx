import { useId, useState } from "react";
import { api, ApiError } from "../api";
import { formatDeadline } from "../booking";

type Props = {
  participantId: number;
  /** What the person wrote in «chi ti ha invitato?». */
  invitedBy: string | null;
  verified: boolean;
  verifiedAt?: string | null;
  verifiedBy?: string | null;
  /** In a table cell: the explanation stays for screen readers and is not drawn. */
  compact?: boolean;
  /** Called after the server accepted the change, so the page can reload what depends on it. */
  onChanged: () => void;
};

/** The admin confirms that a person is really the +1 of who they named: they go first on the
 * waitlists. Without a name there is nothing to confirm. */
export function PlusOneToggle({
  participantId,
  invitedBy,
  verified,
  verifiedAt = null,
  verifiedBy = null,
  compact = false,
  onChanged,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const helpId = useId();
  const hasInvite = Boolean(invitedBy?.trim());

  async function change(next: boolean) {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/admin/participants/${participantId}/plus-one`, {
        method: "PUT",
        json: { verified: next },
      });
      onChanged();
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "Non riesco a salvare. Riprova.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <label className="check">
        <input
          type="checkbox"
          checked={verified}
          disabled={busy || (!hasInvite && !verified)}
          aria-describedby={helpId}
          onChange={(event) => void change(event.target.checked)}
        />
        +1 verificato
      </label>
      <small id={helpId} className={compact ? "sr-only" : undefined}>
        {!hasInvite && !verified
          ? "Serve che la persona abbia indicato chi l'ha invitata."
          : verified
            ? `Verificato${verifiedBy ? ` da ${verifiedBy}` : ""}${verifiedAt ? ` il ${formatDeadline(verifiedAt)}` : ""}. Passa davanti nelle liste d'attesa.`
            : "Se confermi che è davvero un invitato, passa davanti nelle liste d'attesa."}
      </small>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </>
  );
}
