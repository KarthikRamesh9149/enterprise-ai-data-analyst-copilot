"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function Chart({ spec }: { spec: any }) {
  if (!spec?.data) return <div className="panel p-5 text-sm text-muted">No chart available.</div>;
  return (
    <div className="panel p-3">
      <Plot data={spec.data} layout={{ ...spec.layout, autosize: true, margin: { t: 44, r: 16, b: 44, l: 52 } }} useResizeHandler style={{ width: "100%", height: "340px" }} />
    </div>
  );
}
