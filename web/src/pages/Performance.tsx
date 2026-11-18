import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SampleNotes, useAnalysis } from "../analysis";
import { METHODS, useSettings } from "../context";
import { colorFor, longDate, money, percent, ratio, shortDate } from "../format";
import { Card, ErrorState, PageHead, Skeleton, Stat, Tip } from "../components/ui";

export default function Performance() {
  const { settings } = useSettings();
  const { data, error } = useAnalysis();
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton height={480} label="Crunching your portfolio" />;
  const { kpis } = data;
  const finalValue = kpis.total_return == null ? null : settings.value * (1 + kpis.total_return);
  const benchmark = settings.benchmark && kpis.benchmark_total_return != null ? data.sample.benchmark_name ?? settings.benchmark : null;
  const assets = data.sample.assets;
  const contributions = [...data.attribution].sort((a, b) => b.contribution - a.contribution);

  return (
    <>
      <PageHead title="How your portfolio did">
        Growth, returns and the trade-off between reward and risk over the period you chose.
      </PageHead>
      <SampleNotes data={data} />

      <div className="grid cols-4">
        <Stat label={`${money(settings.value, true)} became`} value={money(finalValue)}
          tone={(kpis.total_return ?? 0) >= 0 ? "up" : "down"} note={`${percent(kpis.total_return, 1, true)} in total`} />
        <Stat label="Yearly growth (CAGR)" value={percent(kpis.cagr)} note="Average compound return per year" />
        <Stat label="Volatility" value={percent(kpis.volatility)} note="Typical yearly swing in value" />
        <Stat label="Return per unit of risk" value={ratio(kpis.sharpe)} note="Sharpe ratio · above 1 is strong" />
      </div>

      <div className="grid cols-3 section">
        <Card title="Growth of $100" className="span-2"
          sub={benchmark ? <>Your portfolio vs. {benchmark}: {percent(kpis.total_return, 1, true)} vs. {percent(kpis.benchmark_total_return, 1, true)}</> : "Value of $100 invested at the start"}>
          <div style={{ height: 300 }}>
            <ResponsiveContainer>
              <AreaChart data={data.growth} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--brand)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => `$${Math.round(value)}`} domain={["auto", "auto"]} width={52} tickLine={false} axisLine={false} />
                <Tooltip content={({ active, payload, label }) => active && payload?.length ? (
                  <Tip title={longDate(String(label))} rows={payload.map((item) => ({
                    label: item.dataKey === "portfolio" ? "Your portfolio" : benchmark ?? "Benchmark",
                    value: money(Number(item.value)).replace(/\.\d+$/, ""), color: String(item.color),
                  }))} />
                ) : null} />
                <Area dataKey="portfolio" stroke="var(--brand)" strokeWidth={2.5} fill="url(#growthFill)" dot={false} />
                {benchmark && <Area dataKey="benchmark" stroke="var(--faint)" strokeWidth={1.5} strokeDasharray="5 4" fill="transparent" dot={false} />}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Holdings" sub={METHODS.find((item) => item.key === settings.method)?.label ?? data.method}>
          <div className="stack" style={{ gap: 12 }}>
            {data.weights.map((item, index) => (
              <div key={item.asset}>
                <div className="row between">
                  <span className="row" style={{ gap: 8 }}><span className="dot" style={{ background: colorFor(index) }} /><strong>{item.asset}</strong></span>
                  <span className="num">{percent(item.weight)} · {money(item.weight * settings.value, true)}</span>
                </div>
                <div className="bar-track" style={{ marginTop: 6 }}>
                  <span style={{ width: `${item.weight * 100}%`, background: colorFor(index) }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid cols-2 section">
        <Card title="Each holding on its own" sub="Total return of every asset over the period">
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={data.assets_growth} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => percent(value, 0)} width={52} tickLine={false} axisLine={false} />
                <Tooltip content={({ active, payload, label }) => active && payload?.length ? (
                  <Tip title={longDate(String(label))} rows={[...payload].sort((a, b) => Number(b.value) - Number(a.value))
                    .map((item) => ({ label: String(item.dataKey), value: percent(Number(item.value), 1, true), color: String(item.color) }))} />
                ) : null} />
                <Legend iconType="circle" />
                {assets.map((asset, index) => (
                  <Line key={asset} dataKey={asset} stroke={colorFor(index)} strokeWidth={1.8} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="What drove the result" sub="Each holding's share of the total return — together they add up exactly">
          <div style={{ height: Math.max(240, contributions.length * 40) }}>
            <ResponsiveContainer>
              <BarChart data={contributions} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 0 }}>
                <CartesianGrid horizontal={false} />
                <XAxis type="number" tickFormatter={(value) => percent(value, 0)} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="asset" width={150} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: "var(--surface-2)" }} content={({ active, payload }) => {
                  const row = payload?.[0]?.payload as (typeof contributions)[number] | undefined;
                  return active && row ? <Tip title={row.asset} rows={[
                    { label: "Contribution", value: percent(row.contribution, 2, true) },
                    { label: "Weight", value: percent(row.weight) },
                  ]} /> : null;
                }} />
                <Bar dataKey="contribution" radius={[0, 6, 6, 0]}>
                  {contributions.map((row) => <Cell key={row.asset} fill={row.contribution >= 0 ? "var(--up)" : "var(--down)"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {benchmark && (
        <div className="grid cols-4 section">
          <Stat label={`Sensitivity to ${benchmark}`} value={ratio(kpis.beta)} note="Beta · 1 moves in step with it" />
          <Stat label="Extra return (alpha)" value={percent(kpis.alpha, 1, true)} note="Per year, after adjusting for beta" />
          <Stat label="Difference from benchmark" value={percent(kpis.tracking_error)} note="Tracking error per year" />
          <Stat label="Reward for that difference" value={ratio(kpis.information_ratio)} note="Information ratio" />
        </div>
      )}
      <p className="small muted section">Past results come from historical or simulated prices. They are estimates, not forecasts or advice.</p>
    </>
  );
}
