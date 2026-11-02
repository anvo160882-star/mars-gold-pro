# M.A.R.S. GOLD PRO V2.2 FULL TERMINAL
This package preserves all four modules:
1. Market Analysis — Lightweight Charts candlesticks, crosshair, zoom/pan, EMA.
2. Probability Zones — historical-volatility scenario bands (not calibrated probabilities).
3. 3D Forecast — Monte Carlo scenario density surface (experimental, not validated forecast).
4. Trade Intelligence — M.A.R.S. rule display; signal generation locked to NO TRADE.
5. Data Health — source, freshness and OHLC diagnostics.

Replace app.py and requirements.txt in the existing GitHub repository. Streamlit redeploys after commit.
Important: XAUS spot is indicative, not broker execution price. The current prototype fetches on page rerun; independent minute collector, persistent database and verified backup OHLC feed are future infrastructure work.
