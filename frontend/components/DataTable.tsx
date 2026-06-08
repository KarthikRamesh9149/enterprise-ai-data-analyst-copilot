export function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows?.length) return <div className="panel p-5 text-sm text-muted">No rows to show.</div>;
  const cols = Object.keys(rows[0]).slice(0, 12);
  return (
    <div className="overflow-auto panel">
      <table className="table">
        <thead>
          <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 100).map((row, idx) => (
            <tr key={idx}>{cols.map((c) => <td key={c}>{String(row[c] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
