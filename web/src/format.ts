export function money(value: number | null | undefined, compact = false): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", notation: compact ? "compact" : "standard", maximumFractionDigits: compact ? 1 : 0,
  }).format(value);
}

export function percent(value: number | null | undefined, digits = 1, signed = false): string {
  if (value == null || Number.isNaN(value)) return "—";
  const text = `${Math.abs(value * 100).toFixed(digits)}%`;
  if (value < 0) return `−${text}`;
  return signed && value > 0 ? `+${text}` : text;
}

export function ratio(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value < 0 ? `−${Math.abs(value).toFixed(digits)}` : value.toFixed(digits);
}

export function shortDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export function longDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
}

// Distinct, colour-blind-friendly series colours.
export const PALETTE = ["#5B4BDB", "#14A38B", "#F2994A", "#EB5757", "#2D9CDB", "#9B51E0", "#27AE60", "#F2C94C", "#56CCF2", "#BB6BD9"];
export const colorFor = (index: number) => PALETTE[index % PALETTE.length];
