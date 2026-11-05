/** Download link for the CSV version of a view. The session cookie authenticates the request. */
export function CsvButton({ path, params }: { path: string; params?: URLSearchParams }) {
  const query = new URLSearchParams(params);
  query.set("format", "csv");
  return (
    <a className="button secondary" href={`${path}?${query}`} download>
      Scarica CSV
    </a>
  );
}
