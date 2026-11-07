import { useT } from "./i18n";

const pad = (n: number) => String(n).padStart(2, "0");

/** Native selects deliberately prevent entering arbitrary text, including on mobile. */
export function TimeSelect({
  label,
  value,
  onChange,
  required,
  end = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required: boolean;
  end?: boolean;
}) {
  const t = useT();
  const hour = value ? (end && value === "00:00" ? "24" : value.slice(0, 2)) : "";
  const minute = value ? value.slice(3, 5) : "00";
  return (
    <fieldset>
      <legend>{label}</legend>
      <div className="row">
        <label>
          {t("time.hour", { label })}
          <select
            required={required}
            value={hour}
            onChange={(e) =>
              onChange(
                e.target.value
                  ? `${e.target.value === "24" ? "00" : e.target.value}:${e.target.value === "24" ? "00" : minute}`
                  : "",
              )
            }
          >
            <option value="">—</option>
            {Array.from({ length: end ? 25 : 24 }, (_, i) => (
              <option key={i} value={pad(i)}>
                {pad(i)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("time.minute", { label })}
          <select
            disabled={!value || hour === "24"}
            value={minute}
            onChange={(e) => onChange(`${hour}:${e.target.value}`)}
          >
            {Array.from({ length: 60 }, (_, i) => (
              <option key={i} value={pad(i)}>
                {pad(i)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </fieldset>
  );
}
