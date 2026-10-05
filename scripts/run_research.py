"""Fixed-design extended allocation benchmark, with explicit input provenance."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from data_generation import fetch_price_data,generate_synthetic_prices
from preprocessing import calculate_returns
from research import walk_forward_study,paired_block_interval
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
assets=['SPY','IEF','GLD']
if args.live:
    prices=fetch_price_data(assets,'2018-01-01','2026-01-01',save_path=None)
    if prices.attrs.get('synthetic') or list(sorted(prices.columns))!=sorted(assets):
        raise SystemExit('Complete real adjusted-price data unavailable; no substitution in live benchmark.')
else:
    prices=generate_synthetic_prices(assets,'2018-01-01','2025-12-31')
    prices.attrs.update(source='synthetic',synthetic=True,seed=42)
returns=calculate_returns(prices)
study=walk_forward_study(returns,extended=True)
out=ROOT/'outputs';out.mkdir(exist_ok=True)
prices.to_csv(out/'study_prices.csv')
for key in ['summary','net_returns','trades','target_weights']:study[key].to_csv(out/f'{key}.csv')
diff=study['net_returns']['Volatility-adaptive risk parity']-study['net_returns']['Static defensive risk parity']
meta={'settings':study['settings'],'source':prices.attrs,'input_sha256':hashlib.sha256(prices.to_csv().encode()).hexdigest(),
      'adaptive_vs_static_annual_mean':float(diff.mean()*252),'adaptive_vs_static_block_ci':paired_block_interval(diff),
      'failures':study['failures']}
(out/'metadata.json').write_text(json.dumps(meta,indent=2,default=str))
print(study['summary'].to_string());print(json.dumps(meta,indent=2,default=str))
