import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SampleNotes, useAnalysis } from "../analysis";
import { percent, ratio } from "../format";
import { Card, ErrorState, Notice, PageHead, Skeleton, Stat, Tip } from "../components/ui";

export default function Diversification() {
  const { data, error } = useAnalysis();
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton height={480} />;
  const d = data.diversification;
  const rows = d.rows.map((row) => ({ ...row, gap: row.risk == null ? null : row.risk - row.capital }));
  const top = [...rows].filter((row) => row.risk != null).sort((a, b) => (b.risk ?? 0) - (a.risk ?? 0))[0];

  return (
    <>
      <PageHead title="Is your risk really spread out?">
        Where your money sits isn't the same as where your risk comes from. A volatile holding can dominate risk even with a small share of
        the money.
      </PageHead>
      <SampleNotes data={data} />

      <div className="grid cols-3">
        <Stat label="Holdings that really count" value={ratio(d.effective_holdings, 1)}
          note={`Effective number out of ${rows.length} · lower means more concentrated`} />
        <Stat label="Biggest single holding" value={percent(d.largest_weight)} note="Share of the money" />
        <Stat label="Risk cut by mixing holdings" value={percent(d.reduction)} tone="up"
          note="Compared with holdings that always moved together" />
      </div>

      {top && (
        <div className="section">
          <Notice>
            <strong>{top.asset}</strong> holds {percent(top.capital)} of the money but drives {percent(top.risk)} of the portfolio's ups and
            downs.
          </Notice>
        </div>
      )}

      <Card title="Share of money vs. share of risk" className="section">
        <div style={{ height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="asset" tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(value) => percent(value, 0)} width={48} tickLine={false} axisLine={false} />
              <Tooltip cursor={{ fill: "var(--surface-2)" }} content={({ active, payload, label }) => active && payload?.length ? (
                <Tip title={String(label)} rows={payload.map((item) => ({ label: String(item.name), value: percent(Number(item.value)), color: String(item.color) }))} />
              ) : null} />
              <Legend iconType="circle" />
              <Bar dataKey="capital" name="Share of money" fill="var(--brand)" radius={[6, 6, 0, 0]} />
              <Bar dataKey="risk" name="Share of risk" fill="#F2994A" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Notice tone="warn">
        Owning more stocks doesn't guarantee diversification. Holdings in the same sector, country or currency can still fall together, and
        this view doesn't classify those exposures yet.
      </Notice>
    </>
  );
}
