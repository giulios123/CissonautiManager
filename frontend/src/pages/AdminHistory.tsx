import { formatDeadline } from "../booking";

export type HistoryEntry = { at: string; actor: string; action: string; detail: string };

export function AdminHistory({ history }: { history: HistoryEntry[] }) {
  if (history.length === 0) return null;
  return (
    <section aria-labelledby="history-title">
      <h2 id="history-title">Cronologia</h2>
      <p>Le modifiche fatte a mano dagli organizzatori, la più recente per prima.</p>
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
