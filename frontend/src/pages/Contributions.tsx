import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { Contribution, Me } from "../auth";

export const KIND_LABELS: Record<Contribution["kind"], string> = {
  talk: "Talk",
  topic: "Tema per l'unconference",
  skill: "Competenza da condividere",
};

function ContributionForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial?: Contribution;
  onSaved: () => Promise<void>;
  onCancel?: () => void;
}) {
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const json = {
      kind: String(data.get("kind")),
      title: String(data.get("title") ?? "").trim(),
      description: String(data.get("description") ?? "").trim() || null,
    };
    if (!json.title) {
      setError("Scrivi un titolo per il tuo contributo.");
      return;
    }
    try {
      await api(initial ? `/api/me/contributions/${initial.id}` : "/api/me/contributions", {
        method: initial ? "PATCH" : "POST",
        json,
      });
      if (!initial) form.reset();
      await onSaved();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
    }
  }

  return (
    <form
      onSubmit={submit}
      aria-label={initial ? `Modifica «${initial.title}»` : "Proponi un contributo"}
    >
      <label>
        Tipo
        <select name="kind" defaultValue={initial?.kind ?? "talk"}>
          {Object.entries(KIND_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Titolo
        <input name="title" maxLength={200} required defaultValue={initial?.title ?? ""} />
      </label>
      <label>
        Descrizione (facoltativa)
        <textarea
          name="description"
          rows={2}
          maxLength={2000}
          defaultValue={initial?.description ?? ""}
        />
      </label>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button type="submit">{initial ? "Salva" : "Aggiungi"}</button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Annulla
          </button>
        )}
      </div>
    </form>
  );
}

/** Talks, unconference themes and skills the person offers. */
export function Contributions({
  me,
  editable,
  reload,
}: {
  me: Me;
  editable: boolean;
  reload: () => Promise<void>;
}) {
  const [editing, setEditing] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const items = me.contributions ?? [];

  async function saved(text: string) {
    setEditing(null);
    await reload();
    setMessage(text);
  }

  async function remove(item: Contribution) {
    await api(`/api/me/contributions/${item.id}`, { method: "DELETE" });
    await saved(`«${item.title}» tolto.`);
  }

  return (
    <section className="card" aria-labelledby="contributions-title">
      <h2 id="contributions-title">Cosa porti al camp</h2>
      <p>Proponi un talk, un tema per l&apos;unconference o una competenza da condividere.</p>
      {me.can_bring && <p className="legal">All&apos;iscrizione hai scritto: «{me.can_bring}»</p>}
      {items.length > 0 && (
        <ul>
          {items.map((item) =>
            editing === item.id ? (
              <li key={item.id}>
                <ContributionForm
                  initial={item}
                  onSaved={() => saved("Contributo aggiornato.")}
                  onCancel={() => setEditing(null)}
                />
              </li>
            ) : (
              <li key={item.id}>
                <strong>{KIND_LABELS[item.kind]}</strong>: {item.title}
                {item.description && ` (${item.description})`}{" "}
                <button type="button" className="secondary" onClick={() => setEditing(item.id)}>
                  Modifica
                </button>{" "}
                <button type="button" className="secondary" onClick={() => remove(item)}>
                  Togli
                </button>
              </li>
            ),
          )}
        </ul>
      )}
      {message && (
        <p role="status" className="notice ok">
          {message}
        </p>
      )}
      {editable && <ContributionForm onSaved={() => saved("Contributo aggiunto.")} />}
    </section>
  );
}
