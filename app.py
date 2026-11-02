
import streamlit as st
import streamlit.components.v1 as components
import requests, pandas as pd, numpy as np, json
import plotly.graph_objects as go

st.set_page_config(page_title="M.A.R.S. GOLD PRO V2",page_icon="✦",layout="wide")
st.markdown("""<style>
.block-container{max-width:1800px;padding:1rem 1.35rem}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#080d16}
[data-testid="stMetric"]{background:#0d1725;border:1px solid #203149;border-radius:9px;padding:10px}
[data-testid="stMetricLabel"]{color:#8294ad;font-size:10px;text-transform:uppercase}
[data-testid="stMetricValue"]{font-size:22px;color:#eaf1fb}
.stTabs [data-baseweb="tab-list"]{gap:22px}
.stTabs [data-baseweb="tab"]{color:#91a3bc}
</style>""",unsafe_allow_html=True)
API="https://xaus.com/api/v1"; H={"User-Agent":"MARS-GOLD-PRO-V2-FULL/2.2","Accept":"application/json"}

@st.cache_data(ttl=50)
def get_spot():
    j=requests.get(API+"/spot?compact=1",headers=H,timeout=12).json()
    d=j.get("data",j); p=d.get("spot_usd_oz") or j.get("spot_usd_oz")
    s=d.get("data_state") or j.get("data_state") or {}
    return float(p) if p else None,s,j

@st.cache_data(ttl=50)
def get_bars(tf,period):
    j=requests.get(API+"/chart",params={"symbol":"xau","range":period,"interval":tf},headers=H,timeout=25).json()
    d=j.get("data",j); rows=d.get("candles") or d.get("points") or d.get("values") or j.get("candles") or j.get("points") or []
    if isinstance(rows,dict):rows=rows.get("candles",[])
    x=pd.DataFrame(rows)
    if x.empty:return x
    x=x.rename(columns={"timestamp":"t","time":"t","open":"o","high":"h","low":"l","close":"c"})
    if not set(["t","o","h","l","c"]).issubset(x.columns):return pd.DataFrame()
    x["dt"]=pd.to_datetime(x.t,unit="s",utc=True,errors="coerce") if pd.api.types.is_numeric_dtype(x.t) else pd.to_datetime(x.t,utc=True,errors="coerce")
    for k in ["o","h","l","c"]:x[k]=pd.to_numeric(x[k],errors="coerce")
    return x.dropna(subset=["dt","o","h","l","c"]).sort_values("dt").drop_duplicates("dt").tail(3000).reset_index(drop=True)

st.markdown("""<div style="display:flex;justify-content:space-between;border-bottom:1px solid #203149;padding-bottom:12px">
<div><div style="font-size:24px;font-weight:800;color:#edf4ff">✦ M.A.R.S. <span style="color:#62a8ff">GOLD PRO</span> <small style="color:#8294ad">V2.2 FULL TERMINAL</small></div>
<div style="font-size:10px;letter-spacing:2px;color:#7d91ad">XAU/USD · MARKET STRUCTURE · QUANT RESEARCH</div></div>
<div style="font-size:10px;color:#71839a;text-align:right">4 ANALYSIS MODULES<br>RESEARCH MODE</div></div>""",unsafe_allow_html=True)
try:
    spot,state,raw=get_spot();feed=(state.get("state") or state.get("status") or "UNKNOWN").upper();age=state.get("age_seconds")
except Exception:
    spot,state,raw=None,{},{};feed="UNAVAILABLE";age=None
m1,m2,m3,m4=st.columns(4)
m1.metric("XAU/USD · Spot reference",f"${spot:,.2f}" if spot else "Unavailable")
m2.metric("Feed condition",feed);m3.metric("Data age",f"{age}s" if age is not None else "—");m4.metric("Reference source","XAUS · indicative")
q1,q2,q3,q4=st.columns([1,1,1,1])
tf=q1.selectbox("CHART TIMEFRAME",["1m","5m","15m","1h","4h","1d"],index=2)
period=q2.selectbox("HISTORY",["1mo","3mo","6mo","1y","2y","5y"],index=2)
ema20=q3.toggle("EMA 20",True);ema50=q4.toggle("EMA 50",True)
try:
    df=get_bars(tf,period)
except Exception as ex:
    df=pd.DataFrame();fetch_error=str(ex)
else:fetch_error=None
if not df.empty:
    for n in [20,50,200]:df[f"e{n}"]=df.c.ewm(span=n,adjust=False).mean()
tabs=st.tabs(["01 · MARKET ANALYSIS","02 · PROBABILITY ZONES","03 · 3D FORECAST","04 · TRADE INTELLIGENCE","DATA HEALTH"])
with tabs[0]:
    st.markdown("**PRICE ACTION & MARKET STRUCTURE**")
    if not df.empty:
        bars=[{"time":int(t.timestamp()),"open":float(o),"high":float(h),"low":float(l),"close":float(c)} for t,o,h,l,c in zip(df.dt,df.o,df.h,df.l,df.c)]
        lines={}
        if ema20:lines["e20"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e20)]
        if ema50:lines["e50"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e50)]
        if len(df)>=200:lines["e200"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e200)]
        payload=json.dumps({"bars":bars,"lines":lines,"tf":tf,"count":len(df)})
        chart=r"""<!doctype html><html><head><meta charset="utf-8"><script src="https://unpkg.com/lightweight-charts@4.2.2/dist/lightweight-charts.standalone.production.js"></script><style>*{box-sizing:border-box}body{margin:0;background:#080d16;color:#dce6f5;font:11px Arial}#head{height:34px;padding:10px;border-bottom:1px solid #203149;color:#9eacc0}#chart{height:570px}#foot{height:25px;padding:6px 10px;border-top:1px solid #203149;color:#7487a2}</style></head><body><div id="head"><b style="color:#eef4ff">XAU/USD</b>　·　<span id="tf"></span>　·　<span id="count"></span> verified OHLC bars <span style="float:right;color:#f4c95d">EMA20　</span><span style="float:right;color:#55a7ff">EMA50　</span><span style="float:right;color:#b68cff">EMA200　</span></div><div id="chart"></div><div id="foot">Crosshair · Scroll to zoom · Drag to pan · Fit content</div><script>
const D=__DATA__;document.getElementById('tf').textContent=D.tf;document.getElementById('count').textContent=D.count;const el=document.getElementById('chart');
const c=LightweightCharts.createChart(el,{width:el.clientWidth,height:570,layout:{background:{type:'solid',color:'#080d16'},textColor:'#91a2ba',fontSize:11},grid:{vertLines:{color:'#17263a'},horzLines:{color:'#17263a'}},crosshair:{mode:0,vertLine:{color:'#8496ad',style:2},horzLine:{color:'#8496ad',style:2}},rightPriceScale:{borderColor:'#26374e',scaleMargins:{top:.08,bottom:.08}},timeScale:{borderColor:'#26374e',timeVisible:true,rightOffset:5,barSpacing:8},handleScroll:true,handleScale:true});
const s=c.addCandlestickSeries({upColor:'#18b887',downColor:'#ed5969',borderUpColor:'#18b887',borderDownColor:'#ed5969',wickUpColor:'#18b887',wickDownColor:'#ed5969',priceLineVisible:true});s.setData(D.bars);
for(const [k,col] of [['e20','#f4c95d'],['e50','#55a7ff'],['e200','#b68cff']])if(D.lines[k]?.length){const l=c.addLineSeries({color:col,lineWidth:2,priceLineVisible:false,crosshairMarkerVisible:false});l.setData(D.lines[k])}
c.timeScale().fitContent();new ResizeObserver(x=>c.applyOptions({width:x[0].contentRect.width})).observe(el);
</script></body></html>""".replace("__DATA__",payload)
        l,r=st.columns([4.5,1])
        with l:components.html(chart,height=625,scrolling=False)
        with r:
            z=df.iloc[-1];st.markdown("**MARKET SNAPSHOT**")
            st.metric("Last close",f"${z.c:,.2f}");st.metric("EMA 20",f"${z.e20:,.2f}");st.metric("EMA 50",f"${z.e50:,.2f}")
            st.metric("EMA 200",f"${z.e200:,.2f}" if len(df)>=200 else "Need 200 bars")
            st.caption(f"Recent high: {df.tail(100).h.max():,.2f}");st.caption(f"Recent low: {df.tail(100).l.min():,.2f}")
    else:st.error(f"No valid OHLC data. {fetch_error or 'API schema not recognized.'}")
with tabs[1]:
    st.subheader("Bull / Base / Bear scenario bands")
    if len(df)>30:
        rets=np.log(df.c).diff().dropna();vol=float(rets.tail(240).std());px=float(df.c.iloc[-1])
        horizons=[("4H",4),("12H",12),("24H",24),("3D",72),("7D",168)]
        rows=[]
        for label,h in horizons:
            sigma=max(vol,0.0001)*np.sqrt(h*4)
            rows.append({"Horizon":label,"Bear low":px*np.exp(-1.5*sigma),"Bear high":px*np.exp(-.5*sigma),"Base low":px*np.exp(-.5*sigma),"Base high":px*np.exp(.5*sigma),"Bull low":px*np.exp(.5*sigma),"Bull high":px*np.exp(1.5*sigma)})
        st.dataframe(pd.DataFrame(rows).style.format(precision=2),use_container_width=True,hide_index=True)
        st.info("Dải kịch bản biến động từ độ lệch chuẩn lịch sử; chưa phải xác suất đã hiệu chỉnh hoặc tín hiệu giao dịch.")
    else:st.warning("Cần tối thiểu 31 nến hợp lệ.")
with tabs[2]:
    st.subheader("3D Forward Scenario Distribution")
    if len(df)>30:
        ret=np.diff(np.log(df.c.values));vol=max(float(np.std(ret[-240:])),.0002);px=float(df.c.iloc[-1])
        hrs=np.array([1,2,3,4,6,8,12,16,24,36,48,72,96,120,168]);rng=np.random.default_rng(7)
        sims=px*np.exp(np.cumsum(rng.normal(0,vol,size=(1500,len(hrs)))*np.sqrt(np.diff(np.r_[0,hrs]))[None,:],axis=1))
        edges=np.linspace(np.quantile(sims,.01),np.quantile(sims,.99),55);dens=[]
        for i in range(len(hrs)):dens.append(np.histogram(sims[:,i],bins=edges,density=True)[0])
        y=(edges[:-1]+edges[1:])/2;X,Y=np.meshgrid(hrs,y)
        fig=go.Figure(go.Surface(x=X,y=Y,z=np.array(dens).T,colorscale="Viridis",colorbar=dict(title="Density")))
        fig.update_layout(template="plotly_dark",height=600, title="Monte Carlo · 1,500 simulated paths",scene=dict(xaxis_title="Hours ahead",yaxis_title="Scenario price",zaxis_title="Density"),paper_bgcolor="#080d16",margin=dict(l=0,r=0,t=45,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.warning("Mô phỏng kịch bản từ biến động lịch sử, chưa phải mô hình dự báo đã backtest/hiệu chỉnh. Không dùng độc lập để vào lệnh.")
    else:st.warning("Cần dữ liệu OHLC đủ dài.")
with tabs[3]:
    st.subheader("M.A.R.S. Trade Intelligence")
    if len(df)>200:
        z=df.iloc[-1];bias="BULLISH" if z.c>z.e20>z.e50>z.e200 else ("BEARISH" if z.c<z.e20<z.e50<z.e200 else "MIXED")
        st.metric("Selected timeframe trend proxy",bias)
    st.error("NO TRADE · Signals locked pending verified H4/H1/M15 alignment, broker spread, execution price and walk-forward validation.")
    st.write("M.A.R.S. sequence: Major S/R → H4 bias → price reaction → momentum/structure → R:R ≥ 1:2 → position sizing. Tactical Entry allowed; break + retest is not mandatory. No forced trades.")
with tabs[4]:
    st.subheader("Data Health & Diagnostics")
    st.json({"spot_source":"XAUS indicative spot","feed_state":feed,"age_seconds":age,"ohlc_source":"XAUS chart endpoint","timeframe":tf,"history":period,"ohlc_rows":len(df),"last_bar_utc":str(df.dt.iloc[-1]) if not df.empty else None,"signal_mode":"LOCKED_NO_TRADE"})
    with st.expander("Raw spot response"):st.json(raw if isinstance(raw,dict) else {})
    st.caption("This prototype fetches on Streamlit rerun. Persistent minute collector, durable historical database and independently verified secondary OHLC provider are still pending.")
st.caption("M.A.R.S. GOLD PRO V2.2 FULL · Research only · Indicative data is not broker execution price.")
