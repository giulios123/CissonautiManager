import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { editionDays, priceLabel, seatsLabel, type Activity } from "../activities";
import { formatDay, periodLabel } from "../booking";
import { centsToInput, parseEuroToCents } from "../money";
import { ConfirmDialog } from "../ConfirmDialog";
import { CsvButton } from "./CsvButton";

type Notice = { ok: boolean; text: string } | null;
const PERIODS = ["morning", "afternoon", "evening"] as const;

function ActivityForm({
  days,
  initial,
  onSaved,
  onCancel,
}: {
  days: string[];
  initial: Activity | null;
  onSaved: (text: string) => Promise<void>;
  onCancel?: () => void;
}) {
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const price = parseEuroToCents(text("price") || "0");
    if (price === null) {
      setError("Il prezzo deve essere un numero, ad esempio 15,00 (0 per gratuita).");
      return;
    }
    const body = {
      title: text("title"),
      description: text("description") || null,
      date: text("date"),
      period: text("period"),
      time_label: text("time_label") || null,
      price_cents: price,
      capacity: text("capacity") ? Number(text("capacity")) : null,
    };
    try {
      await api(initial ? `/api/admin/activities/${initial.id}` : "/api/admin/activities", {
        method: initial ? "PATCH" : "POST",
        json: body,
      });
      if (!initial) form.reset();
      await onSaved(initial ? "Attività aggiornata." : "Attività creata.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Qualcosa è andato storto. Riprova.");
    }
  }

  const title = initial ? `Modifica «${initial.title}»` : "Nuova attività";
  return (
    <form onSubmit={submit} aria-label={title} key={initial?.id ?? "new"}>
      <h2>{title}</h2>
      <label>
        Titolo
        <input name="title" required maxLength={200} defaultValue={initial?.title ?? ""} />
      </label>
      <label>
        Descrizione (facoltativa)
        <textarea name="description" rows={3} defaultValue={initial?.description ?? ""} />
      </label>
      <div className="row">
        <label>
          Giorno
          <select name="date" required defaultValue={initial?.date ?? days[0]}>
            {days.map((day) => (
              <option key={day} value={day}>
                {formatDay(day)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fascia
          <select name="period" defaultValue={initial?.period ?? "morning"}>
            {PERIODS.map((period) => (
              <option key={period} value={period}>
                {periodLabel(period)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="row">
        <label>
          Orario indicativo (facoltativo)
          <input name="time_label" maxLength={50} defaultValue={initial?.time_label ?? ""} />
        </label>
        <label>
          Prezzo (€, 0 se gratuita)
          <input
            name="price"
            inputMode="decimal"
            defaultValue={centsToInput(initial?.price_cents ?? 0)}
          />
        </label>
        <label>
          Posti (vuoto se senza limite)
          <input name="capacity" type="number" min={1} defaultValue={initial?.capacity ?? ""} />
        </label>
      </div>
      {initial && initial.joined > 0 && (
        <p className="legal">
          Ci sono già iscritti: prezzo, giorno e fascia non si possono cambiare.
        </p>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <div className="actions">
        <button type="submit">{initial ? "Salva le modifiche" : "Crea l'attività"}</button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Annulla
          </button>
        )}
      </div>
    </form>
  );
}

function DeleteActivity({ activity, onDone }: { activity: Activity; onDone: (n: Notice) => void }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  async function confirm() {
    try {
      await api(`/api/admin/activities/${activity.id}`, { method: "DELETE" });
      setOpen(false);
      onDone({ ok: true, text: `Attività «${activity.title}» eliminata.` });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Riprova tra poco.");
    }
  }

  return (
    <>
      <button
        type="button"
        className="danger"
        ref={trigger}
        disabled={activity.joined > 0}
        title={activity.joined > 0 ? "Un'attività con iscritti non si elimina" : undefined}
        onClick={() => setOpen(true)}
      >
        Elimina
      </button>
      {open && (
        <ConfirmDialog
          title={`Eliminare «${activity.title}»?`}
          confirmLabel="Sì, elimina"
          error={error}
          onConfirm={confirm}
          onCancel={() => setOpen(false)}
          returnFocusTo={trigger}
        >
          <p>L&apos;attività sparisce dalla pagina dei partecipanti.</p>
        </ConfirmDialog>
      )}
    </>
  );
}

export function AdminActivities() {
  const [activities, setActivities] = useState<Activity[] | null>(null);
  const [days, setDays] = useState<string[]>([]);
  const [failed, setFailed] = useState(false);
  const [editing, setEditing] = useState<Activity | null>(null);
  const [notice, setNotice] = useState<Notice>(null);

  const load = useCallback(
    () =>
      api<Activity[]>("/api/admin/activities")
        .then(setActivities)
        .catch(() => setFailed(true)),
    [],
  );

  useEffect(() => {
    void load();
    api<{ start_date: string | null; end_date: string | null }>("/api/admin/edition")
      .then((edition) => setDays(editionDays(edition.start_date, edition.end_date)))
      .catch(() => setDays([]));
  }, [load]);

  async function saved(text: string) {
    setEditing(null);
    setNotice({ ok: true, text });
    await load();
  }

  return (
    <main className="wide">
      <h1>Attività</h1>
      <p>
        Ogni attività ha un giorno e una fascia: possono aderire solo le persone presenti in quella
        fascia. Le attività a pagamento si aggiungono alla quota.
      </p>
      {failed && <p role="alert">Non riesco a caricare le attività.</p>}
      {notice && (
        <p role={notice.ok ? "status" : "alert"} className={`notice ${notice.ok ? "ok" : "error"}`}>
          {notice.text}
        </p>
      )}
      {activities === null ? (
        <p aria-busy="true">Caricamento…</p>
      ) : activities.length === 0 ? (
        <p>Nessuna attività per ora.</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/activities" />
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Attività</th>
                  <th scope="col">Quando</th>
                  <th scope="col">Prezzo</th>
                  <th scope="col">Iscritti</th>
                  <th scope="col">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((activity) => (
                  <tr key={activity.id}>
                    <th scope="row">
                      <Link to={`/admin/attivita/${activity.id}`}>{activity.title}</Link>
                    </th>
                    <td>
                      {formatDay(activity.date)}, {periodLabel(activity.period).toLowerCase()}
                      {activity.time_label && ` (${activity.time_label})`}
                    </td>
                    <td>{priceLabel(activity.price_cents)}</td>
                    <td>{seatsLabel(activity)}</td>
                    <td>
                      <div className="actions">
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => setEditing(activity)}
                        >
                          Modifica
                        </button>
                        <DeleteActivity
                          activity={activity}
                          onDone={async (n) => {
                            setNotice(n);
                            await load();
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {days.length === 0 ? (
        <p>Configura prima le date dell&apos;edizione nelle Impostazioni.</p>
      ) : (
        <ActivityForm
          days={days}
          initial={editing}
          onSaved={saved}
          onCancel={editing ? () => setEditing(null) : undefined}
        />
      )}
    </main>
  );
}
