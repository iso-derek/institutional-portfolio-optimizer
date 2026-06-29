# Institutional Portfolio Optimizer

## Overview

Institutional Portfolio Optimizer is a Python finance analytics project for portfolio construction, risk analysis, and allocation research. It combines market data, portfolio metrics, Monte Carlo simulation, optimisation, and an interactive Streamlit dashboard.

The project is designed for MSc Finance & Data Science / Financial Engineering applications, graduate investment analytics roles, fintech roles, and quantitative finance portfolio review.

This project is for educational and analytical purposes only. It does not provide investment advice.

## Business Problem

Investment teams need to understand the relationship between asset allocation, expected return, volatility, drawdowns, and portfolio risk concentration. This project provides a structured tool for comparing equal-weight, minimum volatility, maximum Sharpe, and simplified Black-Litterman style allocations.

## Key Features

- Fetches historical market data using `yfinance`
- Offline synthetic fallback if live data is unavailable
- Daily returns and cumulative returns
- Annualised return and volatility
- Sharpe Ratio and Sortino Ratio
- Beta against SPY when available
- Maximum drawdown
- Historical VaR, parametric VaR, and CVaR
- Risk contribution by asset
- Correlation heatmap
- Monte Carlo portfolio simulation
- Efficient frontier visualisation
- Minimum volatility portfolio
- Maximum Sharpe Ratio portfolio
- Simplified Black-Litterman style allocation placeholder
- Streamlit dashboard with portfolio inputs and visual analytics

## Technologies Used

- Python
- pandas
- NumPy
- scipy
- yfinance
- Streamlit
- Plotly
- pathlib

## Project Structure

```text
institutional-portfolio-optimizer/
  README.md
  requirements.txt
  .gitignore
  app.py
  data/
    raw/
    processed/
  src/
    data_generation.py
    preprocessing.py
    modelling.py
    analytics.py
    visualisation.py
  notebooks/
  outputs/
  screenshots/
  assets/
```

## Methodology

1. Download or generate historical price data.
2. Clean prices and calculate daily returns.
3. Calculate portfolio-level performance and risk metrics.
4. Simulate random portfolios for efficient frontier analysis.
5. Optimise allocations for maximum Sharpe Ratio and minimum volatility.
6. Visualise allocation, risk, drawdown, correlation, and frontier results in Streamlit.

## How To Run

```bash
pip install -r requirements.txt
python src/data_generation.py
streamlit run app.py
```

## Dashboard Screenshots

Add screenshots to the `screenshots/` folder after running the app locally.

Suggested screenshots:

- Executive summary
- Allocation chart
- Correlation heatmap
- Efficient frontier
- Drawdown chart

## Results / Insights

The dashboard helps answer:

- Which assets dominate portfolio risk?
- How does a maximum Sharpe allocation differ from equal weights?
- How severe are historical drawdowns?
- Does diversification reduce volatility?
- How sensitive is the portfolio to market benchmark movements?

## Skills Demonstrated

- Quantitative finance analytics
- Portfolio optimisation
- Risk metrics
- Monte Carlo simulation
- Streamlit dashboard development
- Plotly visualisation
- Python package organisation

## Future Improvements

- Full Black-Litterman implementation
- Factor exposure analysis
- Transaction cost modelling
- Portfolio rebalancing simulation
- Benchmark selection
- PDF report export

## Author

Derek Ohimai Isokpehi  
GitHub: [iso-derek](https://github.com/iso-derek)
