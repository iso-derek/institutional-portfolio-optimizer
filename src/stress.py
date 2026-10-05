"""Transparent first-order asset, bond-duration, FX and purchasing-power stress."""
import numpy as np
import pandas as pd


def stress_portfolio(exposures,equity_shock=-.2,yield_shift_bps=200.,currency_shocks=None,
                     inflation=.03,portfolio_value=100000.,other_shock=-.1):
    required={'asset','weight','asset_class','currency','modified_duration'}
    if not required.issubset(exposures):raise ValueError('Missing asset exposure fields.')
    frame=exposures.copy()
    if frame.empty or frame.asset.duplicated().any() or frame[ list(required) ].isna().any().any():
        raise ValueError('Provide unique assets and complete exposure assumptions.')
    for c in ['weight','modified_duration']:frame[c]=pd.to_numeric(frame[c],errors='raise')
    if not np.isfinite(frame[['weight','modified_duration']]).all().all() or (frame.weight<0).any() or not np.isclose(frame.weight.sum(),1) or (frame.modified_duration<0).any():
        raise ValueError('Long-only weights must sum to one; durations must be non-negative.')
    if not frame.asset_class.isin(['Equity','Bond','Cash','Other']).all():raise ValueError('Unknown asset class.')
    if not np.isfinite([equity_shock,yield_shift_bps,inflation,portfolio_value,other_shock]).all() or inflation<=-1 or portfolio_value<=0:
        raise ValueError('Invalid scenario assumptions.')
    fx={'USD':0.} if currency_shocks is None else dict(currency_shocks)
    if fx.get('USD',0)!=0:raise ValueError('Base USD currency shock must be zero.')
    fx['USD']=0.
    frame['fx_return']=frame.currency.map(fx)
    if frame.fx_return.isna().any() or not np.isfinite(frame.fx_return).all() or (frame.fx_return<=-1).any():
        raise ValueError('Each currency needs a finite move greater than -100%.')
    frame['local_return']=np.select([frame.asset_class.eq('Equity'),frame.asset_class.eq('Bond'),frame.asset_class.eq('Cash')],
        [equity_shock,-frame.modified_duration*yield_shift_bps/10000,0.],default=other_shock)
    if (frame.local_return<=-1).any():raise ValueError('Scenario produces a loss of at least 100%; duration approximation is invalid here.')
    frame['usd_return']=(1+frame.local_return)*(1+frame.fx_return)-1
    frame['portfolio_contribution']=frame.weight*frame.usd_return
    frame['pnl_usd']=portfolio_value*frame.portfolio_contribution
    nominal=float(frame.portfolio_contribution.sum())
    real=(1+nominal)/(1+inflation)-1
    return {'assets':frame,'nominal_return':nominal,'real_return':real,'pnl_usd':portfolio_value*nominal,
            'real_pnl_usd':portfolio_value*real,'settings':{'equity_shock':equity_shock,'yield_shift_bps':yield_shift_bps,
             'inflation':inflation,'portfolio_value':portfolio_value,'currency_shocks':fx,'other_shock':other_shock},
            'limitations':'One-year purchasing-power illustration; parallel yield shift with first-order modified duration, no convexity/coupons/defaults, unhedged FX. User-entered exposures are not inferred from tickers.'}
