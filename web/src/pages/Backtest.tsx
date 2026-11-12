import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Play } from "lucide-react";
import { postJson, query } from "../api";
import { useSettings } from "../context";
import { colorFor, longDate, money, percent, ratio, shortDate } from "../format";
import { Card, ErrorState, Notice, PageHead, Segmented, Skeleton, Slider, Tip } from "../components/ui";

interface Strategy {
  name: string; net_cagr: number | null; gross_cagr: number | null; volatility: number | null; sharpe: number | null;
  max_drawdown: number | null; cvar: number | null; turnover: number | null; largest_weight: number | null;
  excess: number | null; excess_low: number | null; excess_high: number | null;
}
interface Result {
  start: string; end: string; observations: number; growth: { date: string; [name: string]: number | string | null }[];
  strategies: Strategy[]; failures: { date: string; strategy: string; message: string }[];
}
type Lookback = 63 | 126 | 252;
type Rebalance = 1 | 5 | 21 | 63;

export default function Backtest() {
  const { settings } = useSettings();
  const [lookback, setLookback] = useState<Lookback>(126);
  const [rebalance, setRebalance] = useState<Rebalance>(21);
  const [maxWeight, setMaxWeight] = useState(0.35);
  const [cost, setCost] = useState(10);
  const [extended, setExtended] = useState(true);
  const [result, setResult] = useState<Result>();
  const [error, setError] = useState<string>();
  const [running, setRunning] = useState(false);
  const minimumCap = 1 / settings.tickers.length;

  const run = async () => {
    setRunning(true);
    setError(undefined);
    try {
      setResult(await postJson<Result>(`/api/research?${query(settings)}`, {
        lookback, rebalance_every: rebalance, max_weight: Math.max(maxWeight, minimumCap), cost_bps: cost, extended,
      }));
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <PageHead title="Backtest: would it have worked in real time?">
        Each strategy only uses information available at the time, rebalances on a schedule and pays trading costs. This is the fair way to
        compare them.
      </PageHead>

      <Card title="Test settings" action={
        <button className="button button-primary" type="button" onClick={run} disabled={running}>
          <Play size={16} aria-hidden /> {running ? "Running…" : result ? "Run again" : "Run backtest"}
        </button>
      }>
        <div className="grid cols-2">
          <div className="stack">
            <div className="field"><span>Learn from the previous</span>
              <Segmented label="Training window" value={lookback} onChange={setLookback}
                options={[{ key: 63, label: "3 months" }, { key: 126, label: "6 months" }, { key: 252, label: "1 year" }]} />
            </div>
            <div className="field"><span>Rebalance</span>
              <Segmented label="Rebalance" value={rebalance} onChange={setRebalance}
                options={[{ key: 1, label: "Daily" }, { key: 5, label: "Weekly" }, { key: 21, label: "Monthly" }, { key: 63, label: "Quarterly" }]} />
            </div>
            <label className="row" style={{ gap: 8 }}>
              <input type="checkbox" checked={extended} onChange={(event) => setExtended(event.target.checked)} />
              <span>Include advanced strategies (shrinkage, risk parity, volatility-adaptive)</span>
            </label>
          </div>
          <div className="stack">
            <Slider label="Largest allowed holding" value={Math.max(maxWeight, minimumCap)} min={Math.ceil(minimumCap * 100) / 100} max={1} step={0.05}
              display={percent(Math.max(maxWeight, minimumCap), 0)} onChange={setMaxWeight} help="Caps any single position when rebalancing." />
            <Slider label="Trading cost" value={cost} min={0} max={50} step={1} display={`${cost} bps`} onChange={setCost}
              help={`${(cost / 100).toFixed(2)}% of every amount bought or sold.`} />
          </div>
        </div>
      </Card>

      <div className="section">
        {error ? <ErrorState message={error} /> : running && !result ? <Skeleton height={360} label="Replaying the market day by day" /> : !result ? (
          <Notice>Choose your settings and run the backtest. It replays the market day by day, so it takes a few seconds.</Notice>
        ) : (
          <div className="stack" style={{ opacity: running ? 0.5 : 1 }}>
            {result.observations < 252 && <Notice tone="warn">Less than a year of test data. Treat the results as exploratory.</Notice>}
            {result.failures.length > 0 && (
              <Notice tone="warn">{result.failures.length} optimisation steps failed and fell back to equal weights.</Notice>
            )}
            <Card title="Growth of $100 after costs" sub={`${longDate(result.start)} – ${longDate(result.end)} · ${result.observations.toLocaleString()} trading days`}>
              <div style={{ height: 320 }}>
                <ResponsiveContainer>
                  <LineChart data={result.growth} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tickLine={false} axisLine={false} />
                    <YAxis tickFormatter={(value) => `$${Math.round(value)}`} domain={["auto", "auto"]} width={52} tickLine={false} axisLine={false} />
                    <Tooltip content={({ active, payload, label }) => active && payload?.length ? (
                      <Tip title={longDate(String(label))} rows={[...payload].sort((a, b) => Number(b.value) - Number(a.value))
                        .map((item) => ({ label: String(item.dataKey), value: money(Number(item.value)), color: String(item.color) }))} />
                    ) : null} />
                    <Legend iconType="circle" />
                    {result.strategies.map((strategy, index) => (
                      <Line key={strategy.name} dataKey={strategy.name} stroke={colorFor(index)} strokeWidth={index === 0 ? 2.5 : 1.6} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card title="Scorecard" sub="Vs. equal weight: the yearly return difference and its likely range (95%)">
              <div className="scroll-x">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Strategy</th><th className="right">Yearly growth</th><th className="right">Volatility</th>
                      <th className="right">Return per risk</th><th className="right">Deepest fall</th>
                      <th className="right">Traded per year</th><th className="right">Vs. equal weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.strategies.map((s, index) => (
                      <tr key={s.name}>
                        <td><span className="row" style={{ gap: 8 }}><span className="dot" style={{ background: colorFor(index) }} />{s.name}</span></td>
                        <td className="right">{percent(s.net_cagr)}</td>
                        <td className="right">{percent(s.volatility)}</td>
                        <td className="right">{ratio(s.sharpe)}</td>
                        <td className="right down">{percent(s.max_drawdown)}</td>
                        <td className="right">{percent(s.turnover, 0)}</td>
                        <td className="right">
                          {index === 0 ? "—" : <>
                            <strong className={(s.excess ?? 0) >= 0 ? "up" : "down"}>{percent(s.excess, 1, true)}</strong>
                            <div className="small muted">{percent(s.excess_low, 1, true)} to {percent(s.excess_high, 1, true)}</div>
                          </>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="small muted">
                If the range crosses 0%, the test can't tell the strategy apart from equal weight. Changing settings after seeing results
                makes them look better than they would in real life.
              </p>
            </Card>
          </div>
        )}
      </div>
    </>
  );
}
