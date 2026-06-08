export function Status({ value }: { value: string }) {
  const color = value.includes("blocked") || value.includes("rejected") ? "text-red-700 bg-red-50 border-red-200" : value.includes("approved") || value.includes("safe") || value.includes("passed") || value.includes("loaded") ? "text-teal-700 bg-teal-50 border-teal-200" : "text-amber-700 bg-amber-50 border-amber-200";
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-bold ${color}`}>{value}</span>;
}
