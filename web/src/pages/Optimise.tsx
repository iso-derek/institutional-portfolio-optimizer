import { CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis } from "recharts";
import { Check } from "lucide-react";
import { query, useApi, type Method, type Weight } from "../api";
import { METHODS, useSettings } from "../context";
import { colorFor, percent, ratio } from "../format";
import { Card, ErrorState, Notice, PageHead, Skeleton, Tip } from "../components/ui";

interface Allocation {
  key: Method; label: string; cagr: number | null; volatility: number | null; sharpe: number | null; max_drawdown: number | null;
  converged: boolean; weights: Weight[];
}
interface OptimiseData {
  frontier: { volatility: number; return: number; sharpe: number }[];
  cloud: { volatility: number; return: number }[];
  allocations: Allocation[];
}

export default function Optimise() {
  const { settings, update } = useSettings();
  const { data, error, loading } = useApi<OptimiseData>(`/api/optimise?${query(settings)}`);
  const friendly = (key: Method) => METHODS.find((item) => item.key === key);

  return (
    <>
      <PageHead title="Find a better mix">
        Thousands of possible splits of the same holdings, and the best ones for each level of risk. Pick a strategy to apply it to your
        portfolio.
      </PageHead>
      {error ? <ErrorState message={error} /> : !data ? (
        <div className="stack">
          <Skeleton height={360} label="Testing thousands of portfolio mixes" />
          {loading && <p className="muted small">Testing thousands of mixes — this takes a few seconds.</p>}
        </div>
      ) : (
        <>
          <Card title="Every possible mix, and the efficient frontier"
            sub="Each faint dot is a random mix. The line is the highest past return available at each level of risk.">
            <div style={{ height: 360 }}>
              <ResponsiveContainer>
                <ComposedChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
                  <CartesianGrid />
                  <XAxis type="number" dataKey="volatility" domain={["auto", "auto"]} tickFormatter={(value) => percent(value, 0)}
                    label={{ value: "Risk (volatility per year)", position: "insideBottom", offset: -8 }} />
                  <YAxis type="number" dataKey="return" domain={["auto", "auto"]} tickFormatter={(value) => percent(value, 0)} width={52}
                    label={{ value: "Average return per year", angle: -90, position: "insideLeft", style: { textAnchor: "middle" } }} />
                  <Tooltip content={({ active, payload }) => {
                    const point = payload?.[0]?.payload as { volatility: number; return: number } | undefined;
                    return active && point ? <Tip rows={[{ label: "Risk", value: percent(point.volatility) }, { label: "Return", value: percent(point.return) }]} /> : null;
                  }} />
                  <Legend iconType="circle" verticalAlign="top" height={32} />
                  <Scatter name="Random mixes" data={data.cloud} fill="var(--faint)" fillOpacity={0.25} shape="circle" legendType="circle" />
                  <Line name="Best possible (frontier)" data={data.frontier} dataKey="return" stroke="var(--brand)" strokeWidth={3}
                    dot={{ r: 3, fill: "var(--brand)" }} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid cols-3 section">
            {data.allocations.map((allocation) => {
              const active = settings.method === allocation.key;
              return (
                <Card key={allocation.key} title={friendly(allocation.key)?.label ?? allocation.label} sub={friendly(allocation.key)?.blurb}
                  action={active ? <span className="button button-primary" style={{ cursor: "default" }}><Check size={16} /> In use</span> : (
                    <button className="button" type="button" onClick={() => update({ ...settings, method: allocation.key })}>Use this</button>
                  )}>
                  {!allocation.converged && <Notice tone="warn">The optimiser didn't converge; equal weights are used.</Notice>}
                  <div className="grid cols-2" style={{ gap: 10, marginBottom: 14 }}>
                    <div><div className="stat-label">Yearly growth</div><strong className="num">{percent(allocation.cagr)}</strong></div>
                    <div><div className="stat-label">Volatility</div><strong className="num">{percent(allocation.volatility)}</strong></div>
                    <div><div className="stat-label">Return per risk</div><strong className="num">{ratio(allocation.sharpe)}</strong></div>
                    <div><div className="stat-label">Deepest fall</div><strong className="num down">{percent(allocation.max_drawdown)}</strong></div>
                  </div>
                  <div className="stack" style={{ gap: 8 }}>
                    {allocation.weights.map((weight, index) => (
                      <div key={weight.asset} className="row" style={{ gap: 8 }}>
                        <span style={{ width: 52, fontWeight: 700, fontSize: 13 }}>{weight.asset}</span>
                        <div className="bar-track" style={{ flex: 1 }}><span style={{ width: `${weight.weight * 100}%`, background: colorFor(index) }} /></div>
                        <span className="num small" style={{ width: 48, textAlign: "right" }}>{percent(weight.weight, 0)}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              );
            })}
          </div>
          <div className="section">
            <Notice tone="warn">
              These mixes are chosen and judged on the same past data, so they look better than they would have in real time. Use the
              Backtest tab for a fair, step-by-step test.
            </Notice>
          </div>
        </>
      )}
    </>
  );
}
