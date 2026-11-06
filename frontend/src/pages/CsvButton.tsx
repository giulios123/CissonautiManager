import { useI18n } from "../i18n";

/** Download link for the CSV version of a view. The session cookie authenticates the request.
 * `warning` is shown before the download starts (for files with sensitive data). */
export function CsvButton({
  path,
  params,
  warning,
}: {
  path: string;
  params?: URLSearchParams;
  warning?: string;
}) {
  const { t, locale } = useI18n();
  const query = new URLSearchParams(params);
  query.set("format", "csv");
  // A plain link sends no Accept-Language header: the language goes in the address.
  query.set("lang", locale);
  return (
    <a
      className="button secondary"
      href={`${path}?${query}`}
      download
      onClick={(event) => {
        if (warning && !window.confirm(warning)) event.preventDefault();
      }}
    >
      {t("adm.csv")}
    </a>
  );
}
