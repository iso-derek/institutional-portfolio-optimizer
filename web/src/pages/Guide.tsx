import { Download } from "lucide-react";
import { query, useApi } from "../api";
import { useSettings } from "../context";
import { longDate } from "../format";
import { Card, ErrorState, PageHead, Skeleton } from "../components/ui";

const TOPICS = [
  { title: "Returns and benchmarks", text: "Returns include price moves and dividends (adjusted prices). A broad index gives context, but it is not a guaranteed return or the right yardstick for every portfolio." },
  { title: "Diversification", text: "Weights show where your money sits; how holdings move together decides where the risk sits. Compare the two before assuming many holdings means safety." },
  { title: "Risk and reward", text: "Higher risk offers a chance of more reward, not a promise. Look at growth, swings, the deepest fall and bad-day losses together." },
  { title: "Evidence quality", text: "Check the source, dates, missing holdings and assumptions. Simulated demo data and optimiser problems are always labelled." },
];
const TERMS = [
  ["Yearly growth (CAGR)", "The steady yearly rate that would turn the starting value into the final value."],
  ["Volatility", "How much the value typically swings in a year (standard deviation of daily returns × √252)."],
  ["Return per unit of risk (Sharpe)", "Return above the safe interest rate, divided by volatility."],
  ["Sortino", "Like Sharpe, but only counts downside swings as risk."],
  ["Bad-day loss (value at risk)", "A loss that was matched or exceeded on the worst few percent of days. Not the worst case."],
  ["Expected shortfall", "The average loss on those worst days."],
  ["Share of risk", "How much each holding adds to the portfolio's overall swings, taking co-movement into account."],
  ["Alpha", "Return per year beyond what the benchmark's moves explain."],
];

export default function Guide() {
  const { settings } = useSettings();
  const prices = useApi<{ assets: string[]; rows: { date: string; prices: (number | null)[] }[] }>(`/api/prices?${query(settings)}`);
  return (
    <>
      <PageHead title="Guide & data">How to read the numbers, and the prices behind them.</PageHead>
      <div className="grid cols-2">
        {TOPICS.map((topic) => (
          <Card key={topic.title} title={topic.title}><p className="muted" style={{ margin: 0 }}>{topic.text}</p></Card>
        ))}
      </div>
      <Card title="Try this" className="section">
        <p style={{ margin: 0 }}>
          Switch between <strong>Equal weight</strong> and <strong>Lowest volatility</strong> on the Optimise tab. Which holding loses weight,
          and how does its share of risk change on the Diversification tab?
        </p>
      </Card>
      <Card title="Glossary" className="section">
        <dl style={{ margin: 0, display: "grid", gap: 12 }}>
          {TERMS.map(([term, meaning]) => (
            <div key={term}><dt style={{ fontWeight: 700 }}>{term}</dt><dd style={{ margin: 0 }} className="muted">{meaning}</dd></div>
          ))}
        </dl>
      </Card>
      <Card title="Most recent prices" className="section" sub="Adjusted closing prices, newest first"
        action={<a className="button" href={`/api/downloads/prices?${query(settings)}`}><Download size={16} aria-hidden /> Download all prices</a>}>
        {prices.error ? <ErrorState message={prices.error} /> : !prices.data ? <Skeleton height={240} /> : (
          <div className="scroll-x">
            <table className="table">
              <thead><tr><th>Date</th>{prices.data.assets.map((asset) => <th key={asset} className="right">{asset}</th>)}</tr></thead>
              <tbody>
                {prices.data.rows.map((row) => (
                  <tr key={row.date}>
                    <td>{longDate(row.date)}</td>
                    {row.prices.map((price, index) => <td key={index} className="right">{price == null ? "—" : `$${price.toFixed(2)}`}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="small muted section">Educational analysis, not investment advice. No taxes, trading costs or currency conversion are applied outside the Backtest and Stress test tabs.</p>
    </>
  );
}
