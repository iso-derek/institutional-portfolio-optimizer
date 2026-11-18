import { Fragment } from "react";
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SampleNotes, useAnalysis } from "../analysis";
import { useSettings } from "../context";
import { longDate, money, percent, ratio, shortDate } from "../format";
import { Card, ErrorState, Notice, PageHead, Skeleton, Stat, Tip } from "../components/ui";

function heatColor(value: number | null): string {
  if (value == null) return "var(--surface-2)";
  const strength = Math.round(Math.min(Math.abs(value), 1) * 70);
  return value >= 0
    ? `color-mix(in srgb, var(--brand) ${strength}%, var(--surface-2))`
    : `color-mix(in srgb, var(--up) ${strength}%, var(--surface-2))`;
}

export default function Risk() {
  const { settings } = useSettings();
  const { data, error } = useAnalysis();
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton height={480} />;
  const { tail, correlation, kpis } = data;
  const [historical, , shortfall] = tail.rows;
  const benchmark = settings.benchmark && data.rolling ? data.sample.benchmark_name ?? settings.benchmark : null;

  return (
    <>
      <PageHead title="How much could you lose?">
        Bad-day losses, the deepest fall from a peak, and how the holdings move together.
      </PageHead>
      <SampleNotes data={data} />

      <div className="grid cols-4">
        <Stat label={`A bad day (1 in ${Math.round(1 / (1 - tail.confidence))})`} value={money(historical.dollars)} tone="down"
          note={`${percent(historical.fraction)} loss or worse on ${percent(1 - tail.confidence, 1)} of days`} />
        <Stat label="Average of those bad days" value={money(shortfall.dollars)} tone="down"
          note={`Expected shortfall · ${percent(shortfall.fraction)}`} />
        <Stat label="Deepest fall from a peak" value={percent(kpis.max_drawdown)} tone="down" note="Maximum drawdown" />
        <Stat label="Downside-adjusted return" value={ratio(kpis.sortino)} note="Sortino ratio · only counts losses" />
      </div>
      {tail.observations < 20 && (
        <div className="section"><Notice tone="warn">Only {tail.observations} days support these bad-day figures, so treat them as rough.</Notice></div>
      )}

      <div className="grid cols-2 section">
        <Card title="Falls from the previous high" sub="How far below its best value the portfolio was on each day">
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <AreaChart data={data.drawdown} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="ddFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--down)" stopOpacity={0.05} />
                    <stop offset="100%" stopColor="var(--down)" stopOpacity={0.35} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => percent(value, 0)} width={52} tickLine={false} axisLine={false} />
                <Tooltip content={({ active, payload, label }) => active && payload?.length ? (
                  <Tip title={longDate(String(label))} rows={[{ label: "Below peak", value: percent(Number(payload[0].value)) }]} />
                ) : null} />
                <Area dataKey="drawdown" stroke="var(--down)" fill="url(#ddFill)" strokeWidth={1.8} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {data.rolling ? (
          <Card title="Risk over time" sub="Volatility measured over the previous three months (63 trading days)">
            <div style={{ height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={data.rolling} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tickLine={false} axisLine={false} />
                  <YAxis tickFormatter={(value) => percent(value, 0)} width={52} tickLine={false} axisLine={false} />
                  <Tooltip content={({ active, payload, label }) => active && payload?.length ? (
                    <Tip title={longDate(String(label))} rows={payload.map((item) => ({ label: String(item.name), value: percent(Number(item.value)), color: String(item.color) }))} />
                  ) : null} />
                  <Legend iconType="circle" />
                  <Line dataKey="portfolio_volatility" name="Your portfolio" stroke="var(--brand)" strokeWidth={2} dot={false} />
                  <Line dataKey="benchmark_volatility" name={benchmark ?? "Benchmark"} stroke="var(--faint)" strokeDasharray="5 4" dot={false} />
                  <Line dataKey="tracking_error" name="Difference from benchmark" stroke="#F2994A" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        ) : (
          <Card title="Risk over time"><p className="muted">Add a benchmark to see rolling risk comparisons.</p></Card>
        )}
      </div>

      <Card title="Do your holdings move together?" className="section"
        sub={<>1 means they always move together (little protection), 0 means unrelated, negative means they tend to offset. Average: <strong>{ratio(data.diversification.average_correlation)}</strong></>}>
        <div className="scroll-x">
          <div className="heatmap" style={{ gridTemplateColumns: `64px repeat(${correlation.assets.length}, minmax(52px, 1fr))`, minWidth: 64 + correlation.assets.length * 56 }}>
            <div className="label" />
            {correlation.assets.map((asset) => <div key={asset} className="label">{asset}</div>)}
            {correlation.values.map((row, i) => (
              <Fragment key={correlation.assets[i]}>
                <div className="label" style={{ textAlign: "right" }}>{correlation.assets[i]}</div>
                {row.map((value, j) => (
                  <div key={`${i}-${j}`} style={{ background: heatColor(value), color: Math.abs(value ?? 0) > 0.55 ? "#fff" : "var(--ink)" }}
                    title={`${correlation.assets[i]} & ${correlation.assets[j]}: ${ratio(value)}`}>
                    {ratio(value)}
                  </div>
                ))}
              </Fragment>
            ))}
          </div>
        </div>
      </Card>
      <p className="small muted section">
        Bad-day figures use the actual worst {percent(1 - tail.confidence, 1)} of past days. They are thresholds, not a maximum possible loss,
        and past relationships can change in a crisis.
      </p>
    </>
  );
}
