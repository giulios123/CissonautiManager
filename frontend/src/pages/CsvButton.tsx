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
  const query = new URLSearchParams(params);
  query.set("format", "csv");
  return (
    <a
      className="button secondary"
      href={`${path}?${query}`}
      download
      onClick={(event) => {
        if (warning && !window.confirm(warning)) event.preventDefault();
      }}
    >
      Scarica CSV
    </a>
  );
}
