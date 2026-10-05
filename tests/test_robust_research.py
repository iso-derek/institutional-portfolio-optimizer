import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
import numpy as np
import pandas as pd
from robust_allocations import shrinkage_covariance,robust_allocation,volatility_state
from research import walk_forward_study
from stress import stress_portfolio

class RobustTests(unittest.TestCase):
    def sample(self):
        rng=np.random.default_rng(314)
        return pd.DataFrame(rng.normal(0,[.006,.012,.018],(190,3)),columns=['A','B','C'],index=pd.bdate_range('2025-01-01',periods=190))
    def test_covariance_positive_and_equal_risk_budget(self):
        data=self.sample();cov,shrinkage=shrinkage_covariance(data)
        self.assertGreaterEqual(np.linalg.eigvalsh(cov).min(),0)
        self.assertTrue(0<=shrinkage<=1)
        fit=robust_allocation(data,'risk_parity');self.assertTrue(fit['success'])
        w=fit['weights'];contributions=w*(cov@w)/(w@cov@w)
        np.testing.assert_allclose(contributions,np.ones(3)/3,atol=1e-5)
    def test_constant_data_discloses_fallback(self):
        fit=robust_allocation(pd.DataFrame(np.zeros((40,3))))
        self.assertFalse(fit['success'])
        np.testing.assert_allclose(fit['weights'],np.ones(3)/3)
    def test_adaptive_rule_responds_only_to_past_volatility(self):
        data=self.sample().iloc[:126].copy();data.iloc[-21:]*=5
        state=volatility_state(data)
        self.assertTrue(state['defensive']);self.assertEqual(state['exposure'],.5)
    def test_extended_future_invariance_cash_and_costs(self):
        data=self.sample()
        original=walk_forward_study(data,lookback=63,max_weight=.4,extended=True,cost_bps=0)
        changed=data.copy();changed.iloc[120:]*=3
        later=walk_forward_study(changed,lookback=63,max_weight=.4,extended=True,cost_bps=0)
        a=original['target_weights'];b=later['target_weights']
        pd.testing.assert_frame_equal(a[a.Date<=data.index[120]],b[b.Date<=data.index[120]])
        self.assertEqual(len(original['summary']),7)
        np.testing.assert_allclose(a[['A','B','C','__CASH__']].sum(axis=1),1)
        static=a[a.strategy=='Static defensive risk parity']
        np.testing.assert_allclose(static['__CASH__'],.5)
        paid=walk_forward_study(data,lookback=63,max_weight=.4,extended=True,cost_bps=20)
        self.assertTrue((paid['growth'].iloc[-1]<original['growth'].iloc[-1]).all())
    def test_stress_compounds_fx_and_inflation(self):
        frame=pd.DataFrame({'asset':['Bond','Stock'],'weight':[.5,.5],'asset_class':['Bond','Equity'],
                            'currency':['EUR','USD'],'modified_duration':[5.,0.]})
        result=stress_portfolio(frame,-.2,100,{'EUR':-.1},.05,1000)
        expected=.5*((1-.05)*(1-.1)-1)+.5*(-.2)
        self.assertAlmostEqual(result['nominal_return'],expected)
        self.assertAlmostEqual(result['real_return'],(1+expected)/1.05-1)
        with self.assertRaises(ValueError):stress_portfolio(frame,currency_shocks={})
    def test_invalid_risk_parameters(self):
        with self.assertRaises(ValueError):volatility_state(self.sample(),defensive_exposure=1.1)
        frame=pd.DataFrame({'asset':['A'],'weight':[1.],'asset_class':['Bond'],'currency':['USD'],'modified_duration':[100.]})
        with self.assertRaises(ValueError):stress_portfolio(frame,yield_shift_bps=200)

if __name__=='__main__':unittest.main()
