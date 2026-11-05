import { useId, useState } from "react";
import { api, ApiError } from "../api";
import { formatDeadline } from "../booking";

type Props = {
  participantId: number;
  /** What the person wrote in «chi ti ha invitato?». */
  invitedBy: string | null;
  verifiedAt: string | null;
  verifiedBy: string | null;
  /** Called after the server accepted the change, so the page can reload what depends on it. */
  onChanged: () => void;
};

/** The admin confirms that a person is really the +1 of who they named: they go first on the
 * waitlists. Without a name there is nothing to confirm. */
export function PlusOneToggle({
  participantId,
  invitedBy,
  verifiedAt,
  verifiedBy,
  onChanged,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const helpId = useId();
  const hasInvite = Boolean(invitedBy?.trim());

  async function change(verified: boolean) {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/admin/participants/${participantId}/plus-one`, {
        method: "PUT",
        json: { verified },
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
          checked={verifiedAt !== null}
          disabled={busy || (!hasInvite && verifiedAt === null)}
          aria-describedby={helpId}
          onChange={(event) => void change(event.target.checked)}
        />
        +1 verificato
      </label>
      <small id={helpId}>
        {!hasInvite && verifiedAt === null
          ? "Serve che la persona abbia indicato chi l'ha invitata."
          : verifiedAt !== null
            ? `Verificato${verifiedBy ? ` da ${verifiedBy}` : ""} il ${formatDeadline(verifiedAt)}. Passa davanti nelle liste d'attesa.`
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
