import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { postJson, query } from "../api";
import { useAnalysis } from "../analysis";
import { useSettings } from "../context";
import { money, percent } from "../format";
import { Card, ErrorState, PageHead, Segmented, Skeleton, Slider, Stat, Tip } from "../components/ui";

type AssetClass = "Equity" | "Bond" | "Cash" | "Other";
interface Exposure { asset: string; asset_class: AssetClass; currency: string; duration: number }
interface StressResult {
  nominal_return: number; real_return: number; pnl: number; real_pnl: number; limitations: string;
  assets: { asset: string; weight: number; asset_class: string; currency: string; return: number; contribution: number; pnl: number }[];
}
interface Shocks { equity_shock: number; yield_shift_bps: number; fx_shock: number; inflation: number; other_shock: number }

const PRESETS: { key: string; label: string; shocks: Shocks }[] = [
  { key: "crash", label: "Stock crash", shocks: { equity_shock: -0.3, yield_shift_bps: -100, fx_shock: 0, inflation: 0.02, other_shock: -0.1 } },
  { key: "rates", label: "Rate shock", shocks: { equity_shock: -0.1, yield_shift_bps: 250, fx_shock: -0.05, inflation: 0.04, other_shock: -0.05 } },
  { key: "inflation", label: "High inflation", shocks: { equity_shock: -0.15, yield_shift_bps: 200, fx_shock: -0.1, inflation: 0.08, other_shock: 0.05 } },
  { key: "dollar", label: "Strong dollar", shocks: { equity_shock: -0.05, yield_shift_bps: 50, fx_shock: -0.2, inflation: 0.03, other_shock: -0.05 } },
];

export default function Stress() {
  const { settings } = useSettings();
  const analysis = useAnalysis();
  const [exposures, setExposures] = useState<Exposure[]>([]);
  const [shocks, setShocks] = useState<Shocks>(PRESETS[0].shocks);
  const [result, setResult] = useState<StressResult>();
  const [error, setError] = useState<string>();

  const assets = analysis.data?.sample.assets.join(",") ?? "";
  useEffect(() => {
    if (assets) setExposures(assets.split(",").map((asset) => ({ asset, asset_class: "Equity", currency: "USD", duration: 0 })));
  }, [assets]);

  useEffect(() => {
    if (!exposures.length) return;
    const timer = setTimeout(() => {
      postJson<StressResult>(`/api/stress?${query(settings)}`, { exposures, ...shocks })
        .then((data) => { setResult(data); setError(undefined); })
        .catch((problem: Error) => setError(problem.message));
    }, 150);
    return () => clearTimeout(timer);
  }, [exposures, shocks, settings]);

  const edit = (index: number, patch: Partial<Exposure>) => setExposures((list) => list.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  const shock = (key: keyof Shocks) => (value: number) => setShocks((previous) => ({ ...previous, [key]: value }));
  const preset = PRESETS.find((item) => JSON.stringify(item.shocks) === JSON.stringify(shocks))?.key ?? "";

  if (analysis.error) return <ErrorState message={analysis.error} />;
  if (!analysis.data) return <Skeleton height={480} />;

  return (
    <>
      <PageHead title="Stress test">
        What a one-year shock could do. Tell the app what each holding is, then pick or tune a scenario.
      </PageHead>
      <div className="grid cols-3">
        <Card title="Scenario" sub="Pick a preset or move the sliders">
          <div className="stack">
            <Segmented label="Preset" value={preset} onChange={(key) => { const chosen = PRESETS.find((item) => item.key === key); if (chosen) setShocks(chosen.shocks); }}
              options={PRESETS.map(({ key, label }) => ({ key, label }))} />
            <Slider label="Stock prices" value={shocks.equity_shock} min={-0.6} max={0.4} step={0.05} display={percent(shocks.equity_shock, 0, true)} onChange={shock("equity_shock")} />
            <Slider label="Interest rates" value={shocks.yield_shift_bps} min={-300} max={500} step={25}
              display={`${shocks.yield_shift_bps > 0 ? "+" : ""}${(shocks.yield_shift_bps / 100).toFixed(2)} pts`} onChange={shock("yield_shift_bps")}
              help="Higher rates push bond prices down." />
            <Slider label="Foreign currencies vs. USD" value={shocks.fx_shock} min={-0.4} max={0.4} step={0.05} display={percent(shocks.fx_shock, 0, true)} onChange={shock("fx_shock")} />
            <Slider label="Other assets" value={shocks.other_shock} min={-0.6} max={0.4} step={0.05} display={percent(shocks.other_shock, 0, true)} onChange={shock("other_shock")} />
            <Slider label="Inflation over the year" value={shocks.inflation} min={-0.02} max={0.15} step={0.01} display={percent(shocks.inflation, 0)} onChange={shock("inflation")} />
          </div>
        </Card>

        <div className="span-2 stack">
          {error && <ErrorState message={error} />}
          {!result ? <Skeleton height={300} /> : (
            <>
              <div className="grid cols-2">
                <Stat label="Portfolio change" value={money(result.pnl)} tone={result.pnl >= 0 ? "up" : "down"} note={percent(result.nominal_return, 1, true)} />
                <Stat label="After inflation" value={money(result.real_pnl)} tone={result.real_pnl >= 0 ? "up" : "down"}
                  note={`${percent(result.real_return, 1, true)} in today's money`} />
              </div>
              <Card title="Impact by holding">
                <div style={{ height: Math.max(220, result.assets.length * 38) }}>
                  <ResponsiveContainer>
                    <BarChart data={result.assets} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 0 }}>
                      <CartesianGrid horizontal={false} />
                      <XAxis type="number" domain={[(low: number) => Math.min(low, 0), (high: number) => Math.max(high, 0)]} tickFormatter={(value) => money(value, true)} tickLine={false} axisLine={false} />
                      <YAxis type="category" dataKey="asset" width={150} tickLine={false} axisLine={false} />
                      <ReferenceLine x={0} stroke="var(--faint)" />
                      <Tooltip cursor={{ fill: "var(--surface-2)" }} content={({ active, payload }) => {
                        const row = payload?.[0]?.payload as StressResult["assets"][number] | undefined;
                        return active && row ? <Tip title={`${row.asset} · ${row.asset_class}`} rows={[
                          { label: "Change", value: money(row.pnl) }, { label: "Return", value: percent(row.return, 1, true) },
                        ]} /> : null;
                      }} />
                      <Bar dataKey="pnl" radius={4}>
                        {result.assets.map((row) => <Cell key={row.asset} fill={row.pnl >= 0 ? "var(--up)" : "var(--down)"} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </>
          )}
          <Card title="What each holding is" sub="The app can't tell from a ticker symbol, so set these yourself">
            <div className="scroll-x">
              <table className="table">
                <thead><tr><th>Holding</th><th>Type</th><th>Currency</th><th>Bond duration (years)</th></tr></thead>
                <tbody>
                  {exposures.map((exposure, index) => (
                    <tr key={exposure.asset}>
                      <td><strong>{exposure.asset}</strong></td>
                      <td>
                        <select className="input" value={exposure.asset_class} aria-label={`${exposure.asset} type`}
                          onChange={(event) => edit(index, { asset_class: event.target.value as AssetClass })}>
                          {["Equity", "Bond", "Cash", "Other"].map((kind) => <option key={kind} value={kind}>{kind === "Equity" ? "Stock" : kind}</option>)}
                        </select>
                      </td>
                      <td>
                        <select className="input" value={exposure.currency} aria-label={`${exposure.asset} currency`}
                          onChange={(event) => edit(index, { currency: event.target.value })}>
                          {["USD", "EUR", "GBP", "JPY", "CHF", "CAD"].map((code) => <option key={code}>{code}</option>)}
                        </select>
                      </td>
                      <td>
                        <input className="input" type="number" min={0} max={50} step={0.5} value={exposure.duration} disabled={exposure.asset_class !== "Bond"}
                          aria-label={`${exposure.asset} duration`} onChange={(event) => edit(index, { duration: Math.min(50, Math.max(0, Number(event.target.value))) })} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {result && <p className="small muted">{result.limitations}</p>}
          </Card>
        </div>
      </div>
    </>
  );
}
