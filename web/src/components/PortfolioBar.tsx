import { useEffect, useState, type KeyboardEvent } from "react";
import { Pencil, RotateCcw, X } from "lucide-react";
import type { Settings } from "../api";
import { DEFAULTS, FRENCH_DEFAULTS, INDUSTRIES, INDUSTRY_LABELS, METHODS, SOURCE_NAMES, useSettings } from "../context";
import { money, percent, shortDate } from "../format";
import { Segmented } from "./ui";

export default function PortfolioBar() {
  const { settings } = useSettings();
  const [open, setOpen] = useState(false);
  const method = METHODS.find((item) => item.key === settings.method)?.label;
  const name = (ticker: string) => (settings.source === "french" ? INDUSTRY_LABELS[ticker] ?? ticker : ticker);
  return (
    <>
      <div className="portfolio-bar">
        <div className="chips">
          <strong style={{ marginRight: 4 }}>Your portfolio</strong>
          <span className="chip">{settings.tickers.map(name).join(" · ")}</span>
          <span className="chip">{method}</span>
          <span className="chip">{money(settings.value, true)}</span>
          <span className="chip">{shortDate(settings.start)} – {shortDate(settings.end)}</span>
          {settings.benchmark && <span className="chip">vs {name(settings.benchmark)}</span>}
          <span className="chip">{SOURCE_NAMES[settings.source]}</span>
        </div>
        <button className="button" type="button" onClick={() => setOpen(true)}>
          <Pencil size={16} aria-hidden /> Edit portfolio
        </button>
      </div>
      {open && <SettingsDrawer onClose={() => setOpen(false)} />}
    </>
  );
}

function SettingsDrawer({ onClose }: { onClose: () => void }) {
  const { settings, update } = useSettings();
  const [draft, setDraft] = useState<Settings>(settings);
  const [typing, setTyping] = useState("");
  const [problem, setProblem] = useState("");
  const set = <K extends keyof Settings>(key: K, value: Settings[K]) => setDraft((previous) => ({ ...previous, [key]: value }));

  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const addTickers = (text: string) => {
    const symbols = text.toUpperCase().split(/[\s,]+/).map((symbol) => symbol.trim()).filter(Boolean);
    if (!symbols.length) return;
    set("tickers", Array.from(new Set([...draft.tickers, ...symbols])).slice(0, 20));
    setTyping("");
  };
  const onTickerKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === "," || event.key === " ") {
      event.preventDefault();
      addTickers(typing);
    } else if (event.key === "Backspace" && !typing && draft.tickers.length) {
      set("tickers", draft.tickers.slice(0, -1));
    }
  };
  const french = draft.source === "french";
  const chooseSource = (source: Settings["source"]) => {
    if (source === draft.source) return;
    if (source === "french") {
      setDraft({ ...draft, source, ...FRENCH_DEFAULTS, end: draft.end > FRENCH_DEFAULTS.end ? FRENCH_DEFAULTS.end : draft.end });
    } else if (draft.source === "french") {
      setDraft({ ...draft, source, tickers: DEFAULTS.tickers, benchmark: DEFAULTS.benchmark });
    } else {
      setDraft({ ...draft, source });
    }
    setTyping("");
  };
  const toggleIndustry = (key: string) =>
    set("tickers", draft.tickers.includes(key) ? draft.tickers.filter((item) => item !== key) : [...draft.tickers, key]);
  const apply = () => {
    const tickers = typing ? Array.from(new Set([...draft.tickers, ...typing.toUpperCase().split(/[\s,]+/).filter(Boolean)])) : draft.tickers;
    if (!tickers.length) return setProblem("Add at least one holding.");
    if (draft.start >= draft.end) return setProblem("The start date must be before the end date.");
    update({ ...draft, tickers, benchmark: draft.benchmark.trim().toUpperCase() });
    onClose();
  };

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Edit portfolio">
        <div className="drawer-head">
          <h2 style={{ fontSize: 18 }}>Edit portfolio</h2>
          <button className="button button-ghost" type="button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <div className="drawer-body">
          <div className="field">
            <span>Prices</span>
            <Segmented label="Data source" value={draft.source} onChange={chooseSource}
              options={[{ key: "demo", label: "Demo" }, { key: "french", label: "Real US industries" }, { key: "yahoo", label: "Yahoo Finance" }]} />
            <span className="small muted" style={{ fontWeight: 400 }}>
              {french ? "Real daily returns for 12 US industries since 1926, from the Kenneth R. French Data Library (Dartmouth)."
                : draft.source === "yahoo" ? "Live adjusted prices via yfinance. Yahoo's data is for personal use only and can be slow or unavailable."
                : "Simulated, reproducible prices for trying the tools."}
            </span>
          </div>
          {french ? (
            <div className="field">
              <span>Industries to hold</span>
              <div className="ticker-chips">
                {INDUSTRIES.map((industry) => (
                  <button key={industry.key} type="button" className="ticker" aria-pressed={draft.tickers.includes(industry.key)}
                    onClick={() => toggleIndustry(industry.key)}
                    style={draft.tickers.includes(industry.key) ? { paddingRight: 10 } : { background: "transparent", color: "var(--muted)", border: "1px solid var(--line)", paddingRight: 10 }}>
                    {industry.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
          <div className="field">
            <span>Holdings (up to 20 ticker symbols)</span>
            <div className="ticker-chips" onClick={(event) => (event.currentTarget.querySelector("input") as HTMLInputElement | null)?.focus()}>
              {draft.tickers.map((ticker) => (
                <span className="ticker" key={ticker}>
                  {ticker}
                  <button type="button" aria-label={`Remove ${ticker}`} onClick={() => set("tickers", draft.tickers.filter((item) => item !== ticker))}>
                    <X size={14} />
                  </button>
                </span>
              ))}
              <input value={typing} onChange={(event) => setTyping(event.target.value)} onKeyDown={onTickerKey}
                onBlur={() => addTickers(typing)} placeholder="Add e.g. NVDA" aria-label="Add ticker" />
            </div>
          </div>
          )}
          <div className="field">
            <span>How to split the money</span>
            <div className="method-grid">
              {METHODS.map((item) => (
                <button key={item.key} type="button" className="method" aria-pressed={draft.method === item.key} onClick={() => set("method", item.key)}>
                  <strong>{item.label}</strong>
                  <span>{item.blurb}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="grid cols-2" style={{ gap: 12 }}>
            <label className="field"><span>From</span>
              <input className="input" type="date" value={draft.start} max={draft.end} onChange={(event) => set("start", event.target.value)} />
            </label>
            <label className="field"><span>To</span>
              <input className="input" type="date" value={draft.end} min={draft.start} onChange={(event) => set("end", event.target.value)} />
            </label>
            <label className="field"><span>Amount invested (USD)</span>
              <input className="input" type="number" min={1} step={1000} value={draft.value} onChange={(event) => set("value", Math.max(1, Number(event.target.value)))} />
            </label>
            <label className="field"><span>Compare against</span>
              <input className="input" value={french ? "US stock market" : draft.benchmark} disabled={french} placeholder="e.g. SPY, or blank"
                onChange={(event) => set("benchmark", event.target.value)} />
            </label>
            <label className="field"><span>Safe interest rate (% a year)</span>
              <input className="input" type="number" min={0} max={20} step={0.25} value={+(draft.risk_free * 100).toFixed(2)}
                onChange={(event) => set("risk_free", Math.min(20, Math.max(0, Number(event.target.value))) / 100)} />
            </label>
            <label className="field"><span>Bad-day confidence</span>
              <select className="input" value={draft.confidence} onChange={(event) => set("confidence", Number(event.target.value))}>
                {[0.95, 0.975, 0.99].map((level) => <option key={level} value={level}>{percent(level, 1)}</option>)}
              </select>
            </label>
          </div>
          {problem && <div className="notice notice-warn">{problem}</div>}
        </div>
        <div className="drawer-foot">
          <button className="button button-ghost" type="button" onClick={() => { setDraft(DEFAULTS); setTyping(""); }}>
            <RotateCcw size={16} aria-hidden /> Reset
          </button>
          <button className="button button-primary" type="button" onClick={apply}>Show results</button>
        </div>
      </aside>
    </>
  );
}
