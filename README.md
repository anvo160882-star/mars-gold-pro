
# M.A.R.S. GOLD PRO V2 — Prototype

## Deploy
1. Replace `app.py` and `requirements.txt` in the existing GitHub repository.
2. Commit changes.
3. In Streamlit Community Cloud, reboot the app if it does not redeploy automatically.

## What this version includes
- Dark trading-terminal layout.
- Interactive Plotly candlestick chart with EMA20/50/200.
- Configurable timeframe and history.
- Spot reference from XAUS `/api/v1/spot?compact=1`, canonical `spot_usd_oz`.
- OHLC request via XAUS `/api/v1/chart?symbol=xau&range=...&interval=...`.
- Scenario bands based on historical volatility.
- Interactive 3D Monte Carlo scenario surface.
- Data health and explicit NO TRADE guardrail.

## Important limitations
This is a working prototype, not a validated trading system.
- XAUS spot is an indicative reference, not broker execution price.
- The chart endpoint response parser is defensive but may need adjustment if the live API schema differs.
- The scenario bands are not calibrated probabilities.
- The 3D surface is a Monte Carlo illustration, not a validated forecast.
- Trade Intelligence is deliberately locked to NO TRADE.
- The app does not yet have an independent always-on collector, persistent database, or verified secondary live OHLC source.

## Dependencies
See `requirements.txt`.
