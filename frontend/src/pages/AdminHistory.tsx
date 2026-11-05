import { formatDeadline } from "../booking";
import { useT } from "../i18n";

export type HistoryEntry = { at: string; actor: string; action: string; detail: string };

export function AdminHistory({ history }: { history: HistoryEntry[] }) {
  const t = useT();
  if (history.length === 0) return null;
  return (
    <section aria-labelledby="history-title">
      <h2 id="history-title">{t("dsub.historyTitle")}</h2>
      <p>{t("dsub.historyIntro")}</p>
      <ul>
        {history.map((entry, index) => (
          <li key={index}>
            <small>
              {formatDeadline(entry.at)} · {entry.actor}
            </small>
            <br />
            {entry.detail}
          </li>
        ))}
      </ul>
    </section>
  );
}
