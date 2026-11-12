import { useEffect, useState, type RefObject } from "react";

import { api } from "../api";
import { InfoDialog } from "../InfoDialog";
import { useT } from "../i18n";
import { KIND_KEYS } from "./Contributions";

type Kind = keyof typeof KIND_KEYS;
type Proposal = {
  id: number;
  kind: Kind;
  title: string;
  description: string | null;
  author: { display_name: string } | null;
};

/**
 * What the other participants offer or look for. Read fresh at every opening and never kept: the
 * server decides who is named, so a revoked consent shows up on the next read.
 */
export function ProposalsDialog({
  onClose,
  returnFocusTo,
}: {
  onClose: () => void;
  returnFocusTo: RefObject<HTMLElement | null>;
}) {
  const t = useT();
  const [kind, setKind] = useState("");
  const [attempt, setAttempt] = useState(0);
  const key = `${kind}|${attempt}`;
  // The answer is kept with its request: a new filter or a retry shows "loading" again.
  const [answer, setAnswer] = useState<{ key: string; items: Proposal[] | null } | null>(null);
  const current = answer?.key === key ? answer : null;

  useEffect(() => {
    let live = true;
    const query = new URLSearchParams(kind ? { kind } : {});
    api<Proposal[]>(`/api/me/proposals?${query}`)
      .then((items) => live && setAnswer({ key, items }))
      .catch(() => live && setAnswer({ key, items: null }));
    return () => {
      live = false;
    };
  }, [key, kind]);

  return (
    <InfoDialog title={t("contrib.proposalsTitle")} onClose={onClose} returnFocusTo={returnFocusTo}>
      <p>{t("contrib.proposalsIntro")}</p>
      <label>
        {t("contrib.type")}
        <select value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="">{t("adm.all")}</option>
          {(Object.keys(KIND_KEYS) as Kind[]).map((value) => (
            <option key={value} value={value}>
              {t(KIND_KEYS[value])}
            </option>
          ))}
        </select>
      </label>
      {current === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : current.items === null ? (
        <>
          <p role="alert" className="notice error">
            {t("contrib.proposalsError")}
          </p>
          <p>
            <button type="button" className="secondary" onClick={() => setAttempt(attempt + 1)}>
              {t("common.retry")}
            </button>
          </p>
        </>
      ) : current.items.length === 0 ? (
        <p>{t("contrib.proposalsNone")}</p>
      ) : (
        <ul>
          {current.items.map((item) => (
            <li key={item.id}>
              <strong>{t(KIND_KEYS[item.kind])}</strong>: {item.title}
              {item.description && <> ({item.description})</>}
              <br />
              <small>
                {item.author
                  ? t("contrib.byAuthor", { name: item.author.display_name })
                  : t("contrib.authorHidden")}
              </small>
            </li>
          ))}
        </ul>
      )}
    </InfoDialog>
  );
}
