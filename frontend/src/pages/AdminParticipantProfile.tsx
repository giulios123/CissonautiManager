import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useT } from "../i18n";

type ParticipantProfile = {
  phone: string | null;
  telegram: string | null;
  linkedin: string | null;
  profile: Record<string, string | boolean | null> | null;
};

export function AdminParticipantProfile({ participantId }: { participantId: number }) {
  const t = useT();
  const [data, setData] = useState<ParticipantProfile | null>(null);
  const [location, setLocation] = useState({
    country: "",
    province: "",
    region: "",
    istat_code: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    void api<ParticipantProfile>(`/api/admin/participants/${participantId}/profile`)
      .then((loaded) => {
        setData(loaded);
        setLocation({
          country: String(loaded.profile?.country ?? ""),
          province: String(loaded.profile?.province ?? ""),
          region: String(loaded.profile?.region ?? ""),
          istat_code: String(loaded.profile?.istat_code ?? ""),
        });
      })
      .catch(() => setError(t("common.somethingWrong")));
  }, [participantId, t]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const value = (name: string) => String(values.get(name) ?? "").trim();
    try {
      await api(`/api/admin/participants/${participantId}/profile`, {
        method: "PUT",
        json: {
          phone: value("phone"),
          telegram: value("telegram"),
          linkedin: value("linkedin"),
          city: value("city"),
          province: value("province") || null,
          region: value("region") || null,
          country: value("country"),
          istat_code: value("istat_code") || null,
          job_title: value("job_title"),
          company: value("company"),
          expectations: value("expectations"),
          attended_previous: value("attended_previous") === "yes",
        },
      });
      setSaved(true);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : t("common.somethingWrong"));
    }
  }
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p aria-busy="true">{t("common.loading")}</p>;
  const fields = [
    ["phone", "reg.phone"],
    ["telegram", "profile.telegram"],
    ["linkedin", "profile.linkedin"],
    ["city", "profile.city"],
    ["province", "profile.province"],
    ["region", "profile.region"],
    ["country", "profile.country"],
    ["istat_code", "profile.istatCode"],
    ["job_title", "profile.jobTitle"],
    ["company", "profile.company"],
    ["expectations", "profile.expectations"],
  ] as const;
  const initial: Record<string, string> = {
    phone: data.phone ?? "",
    telegram: data.telegram ?? "",
    linkedin: data.linkedin ?? "",
  };
  for (const [key, value] of Object.entries(data.profile ?? {})) initial[key] = String(value ?? "");
  return (
    <section className="card">
      <h2>{t("profile.adminTitle")}</h2>
      <form onSubmit={submit}>
        {fields.map(([name, label]) => (
          <label key={name}>
            {t(label)}
            <input
              name={name}
              required={
                name !== "region" &&
                name !== "istat_code" &&
                (name !== "province" ||
                  (["italia", "italy"].includes(location.country.trim().toLowerCase()) &&
                    !location.istat_code))
              }
              {...(["country", "province", "region", "istat_code"].includes(name)
                ? {
                    value: location[name as keyof typeof location],
                    onChange: (event: ChangeEvent<HTMLInputElement>) => {
                      const value = event.currentTarget.value;
                      setLocation((current) =>
                        name === "country"
                          ? { country: value, province: "", region: "", istat_code: "" }
                          : { ...current, [name]: value },
                      );
                    },
                  }
                : { defaultValue: initial[name] ?? "" })}
            />
          </label>
        ))}
        <label>
          {t("profile.previous")}
          <select
            name="attended_previous"
            required
            defaultValue={
              initial.attended_previous === "true"
                ? "yes"
                : initial.attended_previous === "false"
                  ? "no"
                  : ""
            }
          >
            <option value="" disabled>
              {t("profile.choose")}
            </option>
            <option value="yes">{t("common.yes")}</option>
            <option value="no">{t("common.no")}</option>
          </select>
        </label>
        <button type="submit">{t("profile.save")}</button>
      </form>
      {saved && <p role="status">{t("profile.saved")}</p>}
    </section>
  );
}
