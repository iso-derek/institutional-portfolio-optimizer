"""Shrinkage allocation baselines and a trailing-volatility exposure rule."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf


def shrinkage_covariance(returns):
    data=np.asarray(returns,dtype=float)
    if data.ndim!=2 or data.shape[0]<2 or data.shape[1]<1 or not np.isfinite(data).all():
        raise ValueError('Need at least two finite training observations.')
    fitted=LedoitWolf().fit(data)
    return fitted.covariance_,float(fitted.shrinkage_)


def robust_allocation(training,kind='minimum_volatility'):
    cov,shrinkage=shrinkage_covariance(training)
    n=cov.shape[0];equal=np.full(n,1/n)
    scale=float(np.trace(cov)/n)
    if scale<=1e-16:
        return {'weights':equal,'success':False,'message':'Zero covariance; equal-weight fallback.','shrinkage':shrinkage}
    matrix=cov/scale+np.eye(n)*1e-10
    if kind=='minimum_volatility':
        fit=minimize(lambda w:float(w@matrix@w),equal,jac=lambda w:2*matrix@w,
                     bounds=[(0,1)]*n,constraints={'type':'eq','fun':lambda w:w.sum()-1},
                     method='SLSQP',options={'ftol':1e-12,'maxiter':500})
        weights=fit.x
    elif kind=='risk_parity':
        budget=np.full(n,1/n)
        fit=minimize(lambda x:float(.5*x@matrix@x-budget@np.log(x)),equal,
                     jac=lambda x:matrix@x-budget/x,bounds=[(1e-8,None)]*n,
                     method='L-BFGS-B',options={'ftol':1e-14,'gtol':1e-9,'maxiter':1000})
        weights=fit.x/fit.x.sum()
    else: raise ValueError('Unknown allocation objective.')
    success=bool(fit.success and np.isfinite(weights).all() and (weights>=-1e-7).all() and np.isclose(weights.sum(),1,atol=1e-7))
    if not success:weights=equal
    return {'weights':weights,'success':success,'message':str(fit.message),'shrinkage':shrinkage}


def volatility_state(training,threshold=1.25,defensive_exposure=.5):
    if not np.isfinite([threshold,defensive_exposure]).all() or threshold<=0 or not 0<=defensive_exposure<=1:
        raise ValueError('Use a positive volatility trigger and defensive exposure in [0,1].')
    proxy=training.mean(axis=1)
    long=float(proxy.std(ddof=1));short=float(proxy.tail(min(21,len(proxy))).std(ddof=1))
    ratio=short/long if long>1e-12 else 1.
    defensive=bool(ratio>threshold)
    return {'ratio':ratio,'defensive':defensive,'exposure':defensive_exposure if defensive else 1.}
