
import streamlit as st
import pandas as pd
import numpy as np
import requests, time
from datetime import datetime, timezone
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="M.A.R.S. GOLD PRO V2", page_icon="✦", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem}
[data-testid="stMetric"]{background:#101827;border:1px solid #243247;padding:14px;border-radius:12px}
.stApp{background:#080e18;color:#e8eef8}
h1,h2,h3{letter-spacing:.2px}
</style>
""", unsafe_allow_html=True)

API="https://xaus.com/api/v1"
HEAD={"User-Agent":"MARS-GOLD-PRO-V2/1.0","Accept":"application/json"}

@st.cache_data(ttl=55, show_spinner=False)
def get_spot():
    r=requests.get(f"{API}/spot?compact=1",headers=HEAD,timeout=12); r.raise_for_status()
    j=r.json()
    # tolerate envelope variations, prefer documented canonical key
    d=j.get("data",j) if isinstance(j,dict) else {}
    price=d.get("spot_usd_oz") or j.get("spot_usd_oz")
    state=d.get("data_state") or j.get("data_state") or {}
    return float(price) if price else None, state, j

@st.cache_data(ttl=55, show_spinner=False)
def get_chart(interval,period):
    params={"symbol":"xau","range":period,"interval":interval}
    r=requests.get(f"{API}/chart",params=params,headers=HEAD,timeout=20); r.raise_for_status()
    j=r.json()
    d=j.get("data",j)
    rows=d.get("candles") or d.get("points") or d.get("values") or j.get("candles") or j.get("points") or []
    if isinstance(rows,dict): rows=rows.get("candles",[])
    df=pd.DataFrame(rows)
    if df.empty: return df
    aliases={"timestamp":"t","time":"t","open":"o","high":"h","low":"l","close":"c","volume":"v"}
    df=df.rename(columns={k:v for k,v in aliases.items() if k in df.columns})
    needed=["t","o","h","l","c"]
    if not all(k in df.columns for k in needed): return pd.DataFrame()
    df["time"]=pd.to_datetime(df["t"],unit="s",utc=True,errors="coerce")
    for c in ["o","h","l","c"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.dropna(subset=["time","o","h","l","c"]).sort_values("time").drop_duplicates("time")
    return df.tail(1500).reset_index(drop=True)

def enrich(df):
    if df.empty:return df
    x=df.copy()
    x["ema20"]=x.c.ewm(span=20,adjust=False).mean()
    x["ema50"]=x.c.ewm(span=50,adjust=False).mean()
    x["ema200"]=x.c.ewm(span=200,adjust=False).mean()
    x["atr"]=pd.concat([(x.h-x.l),(x.h-x.c.shift()).abs(),(x.l-x.c.shift()).abs()],axis=1).max(axis=1).rolling(14).mean()
    return x

def chart_candles(df,title):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.04,row_heights=[.78,.22])
    fig.add_trace(go.Candlestick(x=df.time,open=df.o,high=df.h,low=df.l,close=df.c,name="XAU/USD",
        increasing_line_color="#20c997",decreasing_line_color="#ff5c70"),row=1,col=1)
    for col,color in [("ema20","#f5c451"),("ema50","#4da3ff"),("ema200","#b58cff")]:
        if col in df: fig.add_trace(go.Scatter(x=df.time,y=df[col],name=col.upper(),line=dict(width=1.2,color=color)),row=1,col=1)
    fig.add_trace(go.Bar(x=df.time,y=(df.h-df.l),name="Range",marker_color="#42536c"),row=2,col=1)
    fig.update_layout(title=title,template="plotly_dark",height=610,margin=dict(l=10,r=10,t=45,b=10),
      paper_bgcolor="#080e18",plot_bgcolor="#080e18",xaxis_rangeslider_visible=False,
      legend=dict(orientation="h",y=1.02,x=0),hovermode="x unified")
    fig.update_yaxes(title="USD/oz",row=1,col=1)
    return fig

def mc_surface(df):
    # Exploratory conditional simulation, not a calibrated probability forecast.
    c=df.c.astype(float).values
    ret=np.diff(np.log(c))
    vol=float(np.std(ret[-240:])) if len(ret)>20 else .002
    vol=max(vol,0.0002)
    spot=float(c[-1]); horizons=np.array([1,2,3,4,6,8,12,16,24,36,48,72,96,120,168])
    paths=1200
    rng=np.random.default_rng(42)
    z=rng.normal(size=(paths,len(horizons)))
    steps=np.diff(np.r_[0,horizons])
    increments=z*vol*np.sqrt(steps)[None,:]
    sims=spot*np.exp(np.cumsum(increments,axis=1))
    grid=np.linspace(np.quantile(sims,.01),np.quantile(sims,.99),60)
    dens=[]
    for k in range(len(horizons)):
        hist,_=np.histogram(sims[:,k],bins=grid,density=True)
        dens.append(hist)
    centers=(grid[:-1]+grid[1:])/2
    X,Y=np.meshgrid(horizons,centers)
    Z=np.array(dens).T
    fig=go.Figure(data=[go.Surface(x=X,y=Y,z=Z,colorscale="Viridis",colorbar=dict(title="Density"))])
    fig.update_layout(template="plotly_dark",height=560,title="Monte Carlo scenario surface · experimental",
      scene=dict(xaxis_title="Hours",yaxis_title="Simulated price (USD/oz)",zaxis_title="Density"),
      paper_bgcolor="#080e18",margin=dict(l=0,r=0,t=45,b=0))
    return fig,vol,sims

st.title("✦ M.A.R.S. GOLD PRO V2")
st.caption("XAU/USD · Quant research terminal · Minute refresh · Data provenance visible")
with st.sidebar:
    st.subheader("Market controls")
    tf=st.selectbox("Chart timeframe",["15m","1h","4h","5m","1m"],index=0)
    period=st.selectbox("History",["1mo","3mo","6mo","1y","2y","5y"],index=2)
    st.caption("Giá spot tham chiếu không phải giá khớp lệnh broker.")
    if st.button("↻ Refresh data",use_container_width=True):
        st.cache_data.clear(); st.rerun()

try:
    spot,state,raw=get_spot()
    spot_status=(state.get("state") or state.get("status") or "unknown").upper() if isinstance(state,dict) else "UNKNOWN"
    age=state.get("age_seconds") if isinstance(state,dict) else None
    updated=state.get("as_of") or state.get("updated_at") if isinstance(state,dict) else None
except Exception as e:
    spot,state,raw=None,{},{}
    spot_status="UNAVAILABLE"; age=None; updated=None
try:
    rawdf=get_chart(tf,period)
    df=enrich(rawdf)
    chart_error=None if not df.empty else "API response chưa trả về cấu trúc OHLC nhận diện được."
except Exception as e:
    df=pd.DataFrame(); chart_error=str(e)

last=float(df.c.iloc[-1]) if not df.empty else spot
chg=((df.c.iloc[-1]/df.c.iloc[-2])-1)*100 if len(df)>1 else None
a,b,c,d=st.columns(4)
a.metric("XAU/USD reference",f"${spot:,.2f}" if spot else "Unavailable")
b.metric("OHLC last close",f"${last:,.2f}" if last else "—",f"{chg:+.2f}%" if chg is not None else None)
c.metric("Feed status",spot_status)
d.metric("Data age",f"{age}s" if age is not None else "Not reported")
st.caption(f"Reference updated: {updated or 'Not reported'} · UI refresh is manual/on rerun; source cache target 55s.")
tabs=st.tabs(["MARKET ANALYSIS","PROBABILITY ZONES","3D FORECAST","TRADE INTELLIGENCE","DATA HEALTH"])
with tabs[0]:
    st.subheader("Price action & market structure")
    if not df.empty:
        st.plotly_chart(chart_candles(df,f"XAU/USD · {tf} · {period}"),use_container_width=True,config={"displaylogo":False,"scrollZoom":True})
        recent=df.tail(100)
        support=float(recent.l.min()); resistance=float(recent.h.max())
        x,y,z=st.columns(3); x.metric("EMA 20",f"{df.ema20.iloc[-1]:,.2f}"); y.metric("EMA 50",f"{df.ema50.iloc[-1]:,.2f}"); z.metric("EMA 200",f"{df.ema200.iloc[-1]:,.2f}")
        st.write(f"Recent range support: **{support:,.2f}** · resistance: **{resistance:,.2f}**")
    else: st.error(f"Không tải được OHLC: {chart_error or 'No data'}")
with tabs[1]:
    st.subheader("Bull / Base / Bear scenario bands")
    if not df.empty:
        r=np.log(df.c).diff().dropna()
        sig=float(r.tail(240).std())
        s=float(df.c.iloc[-1])
        horizons={"4H":4,"12H":12,"24H":24}
        rows=[]
        for name,h in horizons.items():
            sd=sig*np.sqrt(h*4) # 15m bars approximation; descriptive scenario band
            rows.append({"Horizon":name,"Bear lower":s*np.exp(-1.5*sd),"Bear upper":s*np.exp(-.5*sd),
                         "Base lower":s*np.exp(-.5*sd),"Base upper":s*np.exp(.5*sd),
                         "Bull lower":s*np.exp(.5*sd),"Bull upper":s*np.exp(1.5*sd)})
        st.dataframe(pd.DataFrame(rows).style.format(precision=2),use_container_width=True,hide_index=True)
        st.info("Các vùng hiện là dải kịch bản biến động dựa trên độ lệch chuẩn lịch sử, KHÔNG phải xác suất đã hiệu chỉnh. Chưa gắn nhãn xác suất thắng.")
    else: st.warning("Cần OHLC hợp lệ để tính vùng kịch bản.")
with tabs[2]:
    st.subheader("3D forward scenario distribution")
    if not df.empty:
        fig,vol,sims=mc_surface(df); st.plotly_chart(fig,use_container_width=True,config={"scrollZoom":True,"displaylogo":False})
        st.caption(f"Volatility input: {vol*100:.3f}% per bar · 1,200 simulated paths · deterministic seed for reproducibility.")
        st.warning("Đây là mô phỏng Monte Carlo minh họa từ biến động lịch sử, chưa phải mô hình dự báo đã backtest hoặc hiệu chỉnh xác suất.")
    else: st.warning("Chưa có dữ liệu nến để mô phỏng.")
with tabs[3]:
    st.subheader("M.A.R.S. Trade Intelligence")
    if not df.empty and len(df)>200:
        q=df.iloc[-1]; bullish=q.c>q.ema20>q.ema50 and q.ema20>q.ema200
        bearish=q.c<q.ema20<q.ema50 and q.ema20<q.ema200
        if bullish: bias="BULLISH"
        elif bearish: bias="BEARISH"
        else: bias="MIXED"
        st.metric("H4/H1 proxy trend (selected chart timeframe)",bias)
    st.error("NO TRADE · V2 prototype: chưa bật BUY/SELL. Cần xác thực multi-timeframe, broker spread, execution price và walk-forward backtest trước khi phát tín hiệu.")
    st.write("Quy tắc giữ nguyên: Major S/R → H4 bias → price reaction → momentum/structure → R:R ≥ 1:2 → position sizing. Không bắt buộc break + retest; không ép lệnh.")
with tabs[4]:
    st.subheader("Data health & source diagnostics")
    st.write({"Spot source":"XAUS API","Spot status":spot_status,"Spot age seconds":age,"OHLC source":"XAUS chart endpoint","Timeframe":tf,"History":period,"OHLC rows":len(df),"Last OHLC timestamp":str(df.time.iloc[-1]) if not df.empty else None})
    with st.expander("Raw spot payload"): st.json(raw if isinstance(raw,dict) else {})
    st.caption("Prototype note: this app reads public endpoints on page rerun. A persistent minute collector, durable database, and verified secondary OHLC provider are the next deployment step; Streamlit alone is not an always-on ingestion service.")
st.caption("M.A.R.S. GOLD PRO V2 · Research tool only · Not investment advice · Never execute trades from unvalidated prototype signals.")
