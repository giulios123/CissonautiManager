import { useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import type { Contribution, Me } from "../auth";
import { useT, type MessageKey } from "../i18n";
import { tNow } from "../i18n/messages";
import { ProposalsDialog } from "./ProposalsDialog";

export const KIND_KEYS: Record<Contribution["kind"], MessageKey> = {
  talk: "contrib.talk",
  topic: "contrib.topic",
  skill: "contrib.skill",
  wanted_skill: "contrib.wantedSkill",
};
export const kindLabel = (kind: Contribution["kind"]) => tNow(KIND_KEYS[kind]);

function ContributionForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial?: Contribution;
  onSaved: () => Promise<void>;
  onCancel?: () => void;
}) {
  const t = useT();
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
      setError(t("contrib.titleRequired"));
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
      setError(caught instanceof ApiError ? caught.message : t("common.somethingWrong"));
    }
  }

  return (
    <form
      onSubmit={submit}
      aria-label={
        initial ? t("contrib.editAria", { title: initial.title }) : t("contrib.proposeAria")
      }
    >
      <p className="legal">{t("contrib.visibleNotice")}</p>
      <label>
        {t("contrib.type")}
        <select name="kind" defaultValue={initial?.kind ?? "talk"}>
          {(Object.keys(KIND_KEYS) as Contribution["kind"][]).map((value) => (
            <option key={value} value={value}>
              {t(KIND_KEYS[value])}
            </option>
          ))}
        </select>
      </label>
      <label>
        {t("contrib.title")}
        <input name="title" maxLength={200} required defaultValue={initial?.title ?? ""} />
      </label>
      <label>
        {t("contrib.description")}
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
        <button type="submit">{initial ? t("contrib.save") : t("contrib.add")}</button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            {t("contrib.cancel")}
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
  readOnly = false,
  reload,
}: {
  me: Me;
  editable: boolean;
  readOnly?: boolean;
  reload: () => Promise<void>;
}) {
  const t = useT();
  const [editing, setEditing] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showProposals, setShowProposals] = useState(false);
  const proposalsButton = useRef<HTMLButtonElement | null>(null);
  const items = me.contributions ?? [];

  async function saved(text: string) {
    setEditing(null);
    await reload();
    setMessage(text);
  }

  async function remove(item: Contribution) {
    await api(`/api/me/contributions/${item.id}`, { method: "DELETE" });
    await saved(t("contrib.removed", { title: item.title }));
  }

  return (
    <section className="card" aria-labelledby="contributions-title">
      <h2 id="contributions-title">{t("contrib.heading")}</h2>
      <p>{t("contrib.intro")}</p>
      <p>
        <button
          type="button"
          className="secondary"
          ref={proposalsButton}
          onClick={() => setShowProposals(true)}
        >
          {t("contrib.proposals")}
        </button>
      </p>
      {readOnly && <p className="notice">{t("privacy.blocked")}</p>}
      {me.can_bring && (
        <p className="legal">{t("contrib.wroteAtSignup", { text: me.can_bring })}</p>
      )}
      {items.length > 0 && (
        <ul>
          {items.map((item) =>
            editing === item.id && !readOnly ? (
              <li key={item.id}>
                <ContributionForm
                  initial={item}
                  onSaved={() => saved(t("contrib.updated"))}
                  onCancel={() => setEditing(null)}
                />
              </li>
            ) : (
              <li key={item.id} className="item">
                <span>
                  <strong>{t(KIND_KEYS[item.kind])}</strong>: {item.title}
                  {item.description && ` (${item.description})`}
                </span>
                {!readOnly && (
                  <>
                    <button type="button" className="secondary" onClick={() => setEditing(item.id)}>
                      {t("contrib.edit")}
                    </button>
                    <button type="button" className="secondary" onClick={() => remove(item)}>
                      {t("contrib.remove")}
                    </button>
                  </>
                )}
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
      {editable && <ContributionForm onSaved={() => saved(t("contrib.added"))} />}
      {showProposals && (
        <ProposalsDialog onClose={() => setShowProposals(false)} returnFocusTo={proposalsButton} />
      )}
    </section>
  );
}
