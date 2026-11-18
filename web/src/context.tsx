import { createContext, useContext, useState, type ReactNode } from "react";
import type { Settings } from "./api";

const today = new Date();
const fiveYearsAgo = new Date(today);
fiveYearsAgo.setFullYear(today.getFullYear() - 5);
const iso = (date: Date) => date.toISOString().slice(0, 10);

export const DEFAULTS: Settings = {
  tickers: ["AAPL", "MSFT", "AMZN", "JPM", "GS", "BLK"],
  benchmark: "SPY",
  start: iso(fiveYearsAgo),
  end: iso(today),
  source: "demo",
  value: 100_000,
  risk_free: 0.02,
  confidence: 0.95,
  method: "equal",
};

export const METHODS: { key: Settings["method"]; label: string; blurb: string }[] = [
  { key: "equal", label: "Equal weight", blurb: "Same amount in every holding" },
  { key: "max_sharpe", label: "Best risk-adjusted", blurb: "Highest past return per unit of risk (max Sharpe)" },
  { key: "min_vol", label: "Lowest volatility", blurb: "Smallest past price swings" },
  { key: "tilt", label: "Momentum tilt", blurb: "Leans toward past winners (simple heuristic)" },
];

/** Real US industry portfolios from the Kenneth R. French Data Library. */
export const INDUSTRIES: { key: string; label: string }[] = [
  { key: "NODUR", label: "Consumer staples" }, { key: "DURBL", label: "Consumer durables" }, { key: "MANUF", label: "Manufacturing" },
  { key: "ENRGY", label: "Energy" }, { key: "CHEMS", label: "Chemicals" }, { key: "BUSEQ", label: "Technology & business equipment" },
  { key: "TELCM", label: "Telecoms" }, { key: "UTILS", label: "Utilities" }, { key: "SHOPS", label: "Retail & wholesale" },
  { key: "HLTH", label: "Healthcare" }, { key: "MONEY", label: "Finance" }, { key: "OTHER", label: "Other industries" },
];
export const INDUSTRY_LABELS: Record<string, string> = { ...Object.fromEntries(INDUSTRIES.map((i) => [i.key, i.label])), MARKET: "US stock market" };
export const FRENCH_DEFAULTS = { tickers: ["NODUR", "ENRGY", "BUSEQ", "HLTH", "MONEY", "UTILS"], benchmark: "MARKET", end: "2026-09-30" };
export const SOURCE_NAMES: Record<string, string> = { demo: "Demo data", french: "Real US industries", yahoo: "Yahoo Finance" };

const KEY = "portfolio-lab-settings";

function load(): Settings {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) ?? "null");
    if (saved && Array.isArray(saved.tickers)) {
      const { live, ...rest } = saved;
      return { ...DEFAULTS, ...rest, source: rest.source ?? (live ? "yahoo" : "demo") };
    }
  } catch {
    /* ignore */
  }
  return DEFAULTS;
}

interface State { settings: Settings; update: (next: Settings) => void }
const SettingsContext = createContext<State | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(load);
  const update = (next: Settings) => {
    setSettings(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* storage unavailable */
    }
  };
  return <SettingsContext.Provider value={{ settings, update }}>{children}</SettingsContext.Provider>;
}

export function useSettings(): State {
  const value = useContext(SettingsContext);
  if (!value) throw new Error("useSettings must be used inside SettingsProvider");
  return value;
}
