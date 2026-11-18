import { useEffect, useState } from "react";

export type Method = "equal" | "max_sharpe" | "min_vol" | "tilt";
export type Source = "demo" | "french" | "yahoo";

export interface Settings {
  tickers: string[];
  benchmark: string;
  start: string;
  end: string;
  source: Source;
  value: number;
  risk_free: number;
  confidence: number;
  method: Method;
}

export interface Weight { asset: string; weight: number }

export function query(settings: Settings, extra: Record<string, string | number> = {}): string {
  const params = new URLSearchParams({
    tickers: settings.tickers.join(","),
    benchmark: settings.benchmark,
    start: settings.start,
    end: settings.end,
    source: settings.source,
    value: String(settings.value),
    risk_free: String(settings.risk_free),
    confidence: String(settings.confidence),
    method: settings.method,
  });
  for (const [key, value] of Object.entries(extra)) params.set(key, String(value));
  return params.toString();
}

const cache = new Map<string, unknown>();

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const key = `${init?.method ?? "GET"} ${url} ${init?.body ?? ""}`;
  if (cache.has(key)) return cache.get(key) as T;
  const response = await fetch(url, init);
  if (!response.ok) {
    let message = `Something went wrong (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") message = body.detail;
      else if (Array.isArray(body?.detail)) message = "Some settings are out of range. Please check the values.";
    } catch {
      /* keep default */
    }
    throw new Error(message);
  }
  const data = (await response.json()) as T;
  cache.set(key, data);
  return data;
}

export function postJson<T>(url: string, body: unknown): Promise<T> {
  return request<T>(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

export interface Loadable<T> { data: T | undefined; error: string | undefined; loading: boolean }

export function useApi<T>(url: string | null): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ data: undefined, error: undefined, loading: url !== null });
  useEffect(() => {
    if (url === null) return;
    let live = true;
    setState((previous) => ({ ...previous, loading: true, error: undefined }));
    request<T>(url)
      .then((data) => live && setState({ data, error: undefined, loading: false }))
      .catch((error: Error) => live && setState((previous) => ({ ...previous, error: error.message, loading: false })));
    return () => {
      live = false;
    };
  }, [url]);
  return state;
}
