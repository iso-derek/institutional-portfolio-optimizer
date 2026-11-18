import type { ReactNode } from "react";
import { AlertTriangle, Info } from "lucide-react";

export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </header>
  );
}

export function Card({ title, sub, action, children, className = "" }: {
  title?: string; sub?: ReactNode; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {sub && <div className="card-sub">{sub}</div>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Stat({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: "up" | "down" }) {
  return (
    <div className="card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone ?? ""}`}>{value}</div>
      {note && <div className="stat-note">{note}</div>}
    </div>
  );
}

export function Segmented<T extends string | number>({ options, value, onChange, label }: {
  options: { key: T; label: string }[]; value: T; onChange: (value: T) => void; label: string;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={String(option.key)} type="button" aria-pressed={option.key === value} onClick={() => onChange(option.key)}>
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn"; children: ReactNode }) {
  const Icon = tone === "warn" ? AlertTriangle : Info;
  return (
    <div className={`notice notice-${tone}`}>
      <Icon size={18} style={{ flexShrink: 0, marginTop: 2 }} aria-hidden />
      <div>{children}</div>
    </div>
  );
}

export function Skeleton({ height = 120, label = "Loading" }: { height?: number; label?: string }) {
  return <div className="skeleton" style={{ height }} role="status" aria-label={label} />;
}

export function ErrorState({ message }: { message: string }) {
  return <Notice tone="warn">{message}</Notice>;
}

export function Slider({ label, value, min, max, step, onChange, display, help }: {
  label: string; value: number; min: number; max: number; step: number; onChange: (value: number) => void; display: string; help?: string;
}) {
  return (
    <label className="slider">
      <span className="slider-top">
        <span className="stat-label">{label}</span>
        <span className="slider-value">{display}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      {help && <span className="small muted">{help}</span>}
    </label>
  );
}

export function Tip({ title, rows }: { title?: ReactNode; rows: { label: ReactNode; value: ReactNode; color?: string }[] }) {
  return (
    <div className="tooltip">
      {title && <strong>{title}</strong>}
      {rows.map((row, index) => (
        <div key={index} className="row" style={{ gap: 8, justifyContent: "space-between" }}>
          <span className="row" style={{ gap: 6 }}>
            {row.color && <span className="dot" style={{ background: row.color }} />}
            {row.label}
          </span>
          <strong className="num">{row.value}</strong>
        </div>
      ))}
    </div>
  );
}
