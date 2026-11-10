import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { emptyGuest, type Guest, type GuestInput } from "../guests";
import { useT } from "../i18n";
import { adminGuestPath } from "../routes";
import { CsvButton } from "./CsvButton";
import { GuestForm } from "./GuestForm";

/** External guests: people without an account who join meals and activities. */
export function AdminGuests() {
  const t = useT();
  const [guests, setGuests] = useState<Guest[] | null>(null);
  const [failed, setFailed] = useState(false);
  // A new form after each creation, so the fields start empty again.
  const [formKey, setFormKey] = useState(0);

  const load = useCallback(
    () =>
      api<Guest[]>("/api/admin/guests")
        .then(setGuests)
        .catch(() => setFailed(true)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load]);

  async function create(input: GuestInput) {
    await api<Guest>("/api/admin/guests", { method: "POST", json: input });
    setFormKey((key) => key + 1);
    await load();
  }

  return (
    <main className="wide">
      <h1>{t("guests.title")}</h1>
      <p>{t("guests.intro")}</p>
      {failed && <p role="alert">{t("slots.loadError")}</p>}
      <section aria-labelledby="guest-add">
        <h2 id="guest-add">{t("guests.add")}</h2>
        <GuestForm
          key={formKey}
          initial={emptyGuest}
          submitLabel={t("guests.create")}
          onSubmit={create}
        />
      </section>
      {guests === null ? (
        <p aria-busy="true">{t("common.loading")}</p>
      ) : guests.length === 0 ? (
        <p>{t("guests.none")}</p>
      ) : (
        <>
          <p>
            <CsvButton path="/api/admin/guests" />
            <span className="legal"> {t("guests.csvNote")}</span>
          </p>
          <div className="table-wrap">
            <table>
              <caption>{t("guests.title")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("guests.colName")}</th>
                  <th scope="col">{t("guests.colPayer")}</th>
                  <th scope="col">{t("guests.colMeals")}</th>
                  <th scope="col">{t("guests.colActivities")}</th>
                </tr>
              </thead>
              <tbody>
                {guests.map((guest) => (
                  <tr key={guest.id}>
                    <th scope="row">
                      <Link to={adminGuestPath(guest.id)}>
                        {guest.first_name} {guest.last_name}
                      </Link>
                      {guest.reference && (
                        <>
                          <br />
                          <small>{guest.reference}</small>
                        </>
                      )}
                    </th>
                    <td>
                      {guest.payer === "paying" ? t("guests.payerPaying") : t("guests.payerNon")}
                    </td>
                    <td>{guest.meals.length}</td>
                    <td>{guest.activities.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
