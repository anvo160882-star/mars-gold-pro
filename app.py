import streamlit as st
import requests, pandas as pd, numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
st.set_page_config(page_title="M.A.R.S. GOLD PRO",page_icon="🟡",layout="wide")
st.title("🟡 M.A.R.S. GOLD PRO")
st.caption("XAU/USD • Live reference • Probability • 3D volatility • Trade intelligence")
BASE="https://xaus.com/api/v1"
@st.cache_data(ttl=55,show_spinner=False)
def api(path,params=None):
 r=requests.get(f"{BASE}/{path}",params=params,timeout=15); r.raise_for_status(); return r.json()
def points(x):
 if isinstance(x,list): return x
 if isinstance(x,dict):
  for k in ("data","prices","history","points","results"):
   if isinstance(x.get(k),list): return x[k]
 return []
try:
 spot=api("spot",{"compact":"1"})
 price=float(spot.get("price",spot.get("spot",spot.get("xauusd",np.nan)))) if isinstance(spot,dict) else np.nan
 state=spot.get("data_state",{}) if isinstance(spot,dict) else {}
 status=state.get("status",spot.get("status","received")) if isinstance(spot,dict) else "unknown"
 asof=spot.get("price_as_of",state.get("price_as_of","")) if isinstance(spot,dict) else ""
except Exception as e: price=np.nan; status=f"ERROR: {e}"; asof=""
a,b,c,d=st.columns(4)
a.metric("XAU/USD reference",f"${price:,.2f}" if np.isfinite(price) else "Unavailable")
b.metric("Feed status",str(status).upper()); c.metric("Price as of",str(asof)[:24] or "—"); d.metric("Refresh","55 sec cache")
t1,t2,t3,t4,t5=st.tabs(["01 MARKET ANALYSIS","02 PROBABILITY ZONES","03 3D FORECAST","04 TRADE INTELLIGENCE","DATA & SETUP"])
with t1:
 st.subheader("Market Analysis")
 try:
  raw=api("intraday",{"symbol":"xau","hours":48}); df=pd.DataFrame(points(raw))
  if {"t","p"}.issubset(df.columns):
   df["time"]=pd.to_datetime(df.t,unit="s",utc=True,errors="coerce"); df["price"]=pd.to_numeric(df.p,errors="coerce"); df=df.dropna().sort_values("time")
   df["EMA20"]=df.price.ewm(span=20).mean(); df["EMA50"]=df.price.ewm(span=50).mean()
   fig=go.Figure()
   for col in ["price","EMA20","EMA50"]: fig.add_trace(go.Scatter(x=df.time,y=df[col],name=col,mode="lines"))
   fig.update_layout(template="plotly_dark",height=480,xaxis_rangeslider_visible=False)
   st.plotly_chart(fig,use_container_width=True); st.caption("XAUS sampled 5-minute reference prices, NOT broker OHLC candles.")
   st.write(f"{len(df)} samples • {df.time.min()} → {df.time.max()}")
  else: st.warning("API schema did not contain expected t/p fields."); st.json(raw)
 except Exception as e: st.error(f"Intraday unavailable: {e}")
 st.info("H4/H1/M15 broker-style OHLC and Dukascopy historical candles are not connected yet.")
with t2:
 st.subheader("Probability Zones")
 st.warning("No calibrated Bull/Base/Bear probabilities yet. We will not invent probabilities.")
 try:
  h=pd.DataFrame(points(api("history"))); 
  if "c" in h:
   r=pd.to_numeric(h.c,errors="coerce").pct_change().dropna()
   if len(r)>30:
    st.write("Descriptive historical daily-return quantiles (not forecast probabilities).")
    st.dataframe(pd.DataFrame({"Quantile":["5%","25%","50%","75%","95%"],"Return":[r.quantile(q) for q in [.05,.25,.5,.75,.95]]}))
   else: st.info("Not enough valid history.")
  else: st.info("History endpoint schema unavailable."); st.json(h.head())
 except Exception as e: st.error(f"History unavailable: {e}")
with t3:
 st.subheader("3D Forecast")
 st.warning("This is a historical volatility surface, not a forward price forecast.")
 try:
  h=pd.DataFrame(points(api("history")))
  if "c" in h:
   r=np.log(pd.to_numeric(h.c,errors="coerce")).diff().dropna()
   if len(r)>25:
    hs=np.array([4,12,24,72,168]); ws=np.array([5,10,20,40,60])
    z=np.array([[r.tail(min(w,len(r))).std()*np.sqrt(x) for x in hs] for w in ws])
    fig=go.Figure(go.Surface(x=hs,y=ws,z=z,colorscale="Viridis"))
    fig.update_layout(template="plotly_dark",height=520,scene=dict(xaxis_title="Horizon hours",yaxis_title="Lookback days",zaxis_title="Volatility"))
    st.plotly_chart(fig,use_container_width=True)
   else: st.info("Insufficient history.")
  else: st.info("No usable history series.")
 except Exception as e: st.error(f"3D surface unavailable: {e}")
with t4:
 st.subheader("Trade Intelligence")
 st.error("NO TRADE — H4/H1/M15 synchronized OHLC and validated backtest are not ready.")
 st.write("Entry — | SL — | TP1 — | TP2 — | R:R —")
 st.caption("M.A.R.S.: Major S/R → H4 bias → reaction → momentum/structure → R:R → sizing. Min R:R 1:2. No forced trades.")
with t5:
 st.subheader("Data & Setup")
 st.markdown("- XAUS spot: indicative reference price, not executable quote.\n- XAUS intraday: sampled 5-minute prices, 48-hour window.\n- History: daily series; not enough to claim H4/H1/M15.\n- Remaining: Dukascopy OHLC integration, data QA, out-of-sample backtest and probability calibration.")
 st.caption("Last app run: "+datetime.now(timezone.utc).isoformat())
 if st.button("Refresh data"): st.cache_data.clear(); st.rerun()
