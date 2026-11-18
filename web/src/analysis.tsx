import { query, useApi, type Weight } from "./api";
import { useSettings } from "./context";
import { longDate } from "./format";
import { Notice } from "./components/ui";

export interface Point { date: string; [series: string]: number | string | null }
export interface Analysis {
  sample: { synthetic: boolean; source: string; source_url: string | null; data_through: string | null; benchmark_name: string | null; fallback_reason: string | null; start: string; end: string; observations: number; assets: string[]; missing: string[] };
  notes: string[];
  method: string;
  weights: Weight[];
  kpis: {
    cagr: number | null; volatility: number | null; sharpe: number | null; sortino: number | null; max_drawdown: number | null;
    cvar: number | null; beta: number | null; alpha: number | null; total_return: number | null; benchmark_total_return: number | null;
    tracking_error: number | null; information_ratio: number | null;
  };
  growth: Point[];
  assets_growth: Point[];
  drawdown: Point[];
  rolling: Point[] | null;
  attribution: { asset: string; weight: number; contribution: number }[];
  tail: { confidence: number; observations: number; rows: { label: string; fraction: number; dollars: number }[] };
  correlation: { assets: string[]; values: (number | null)[][] };
  diversification: {
    effective_holdings: number | null; largest_weight: number | null; reduction: number | null; average_correlation: number | null;
    rows: { asset: string; capital: number; risk: number | null }[];
  };
}

export function useAnalysis() {
  const { settings } = useSettings();
  return useApi<Analysis>(`/api/analysis?${query(settings)}`);
}

export function SampleNotes({ data }: { data: Analysis }) {
  const { sample, notes } = data;
  return (
    <div className="stack" style={{ marginBottom: 16, gap: 8 }}>
      {sample.synthetic && (
        <Notice tone="warn">
          {sample.fallback_reason
            ? <>Live prices couldn't be loaded, so simulated prices are shown instead. {sample.fallback_reason}</>
            : <>Demo data: these prices are simulated, so results show how the tools work, not real market history.</>}
        </Notice>
      )}
      {sample.missing.length > 0 && <Notice tone="warn">Left out for lack of price history: {sample.missing.join(", ")}.</Notice>}
      {notes.map((note) => <Notice key={note}>{note}</Notice>)}
      <div className="small muted">
        {sample.source_url ? <a href={sample.source_url} target="_blank" rel="noreferrer">{sample.source}</a> : sample.source} · {longDate(sample.start)} – {longDate(sample.end)} · {sample.observations.toLocaleString()} trading days ·
        rebalanced daily, before costs and tax
      </div>
    </div>
  );
}
