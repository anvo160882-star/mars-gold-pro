
import streamlit as st
import streamlit.components.v1 as components
import requests, pandas as pd, json

st.set_page_config(page_title="M.A.R.S. GOLD PRO V2.1", layout="wide")
st.markdown("""<style>
.block-container{max-width:1800px;padding:1rem 1.4rem}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#080d16}
[data-testid="stMetric"]{background:#0d1725;border:1px solid #203149;border-radius:9px;padding:10px}
[data-testid="stMetricLabel"]{color:#8294ad;font-size:10px;text-transform:uppercase}
[data-testid="stMetricValue"]{font-size:23px;color:#eaf1fb}
</style>""",unsafe_allow_html=True)
API="https://xaus.com/api/v1"
H={"User-Agent":"MARS-GOLD-PRO-V2.1","Accept":"application/json"}

@st.cache_data(ttl=50)
def get_spot():
    j=requests.get(API+"/spot?compact=1",headers=H,timeout=12).json()
    d=j.get("data",j); p=d.get("spot_usd_oz") or j.get("spot_usd_oz")
    s=d.get("data_state") or j.get("data_state") or {}
    return p,s,j

@st.cache_data(ttl=50)
def get_bars(tf,period):
    j=requests.get(API+"/chart",params={"symbol":"xau","range":period,"interval":tf},headers=H,timeout=25).json()
    d=j.get("data",j); rows=d.get("candles") or d.get("points") or d.get("values") or j.get("candles") or j.get("points") or []
    if isinstance(rows,dict): rows=rows.get("candles",[])
    x=pd.DataFrame(rows)
    if x.empty:return x
    x=x.rename(columns={"timestamp":"t","time":"t","open":"o","high":"h","low":"l","close":"c"})
    if not set(["t","o","h","l","c"]).issubset(x.columns):return pd.DataFrame()
    if pd.api.types.is_numeric_dtype(x.t):x["dt"]=pd.to_datetime(x.t,unit="s",utc=True,errors="coerce")
    else:x["dt"]=pd.to_datetime(x.t,utc=True,errors="coerce")
    for k in ["o","h","l","c"]:x[k]=pd.to_numeric(x[k],errors="coerce")
    return x.dropna(subset=["dt","o","h","l","c"]).sort_values("dt").drop_duplicates("dt").tail(3000)

st.markdown("""<div style="display:flex;justify-content:space-between;border-bottom:1px solid #203149;padding-bottom:12px">
<div><div style="font-size:24px;font-weight:800;color:#edf4ff">✦ M.A.R.S. <span style="color:#62a8ff">GOLD PRO</span> <small style="color:#8294ad">V2.1 TERMINAL</small></div>
<div style="font-size:10px;letter-spacing:2px;color:#7d91ad">XAU/USD · MARKET STRUCTURE · QUANT RESEARCH</div></div>
<div style="font-size:10px;color:#71839a;text-align:right">RESEARCH MODE<br>NO EXECUTION</div></div>""",unsafe_allow_html=True)
try:
    spot,state,raw=get_spot()
    feed=(state.get("state") or state.get("status") or "UNKNOWN").upper()
    age=state.get("age_seconds")
except Exception:
    spot,state,raw=None,{},{};feed="UNAVAILABLE";age=None
m1,m2,m3,m4=st.columns(4)
m1.metric("XAU/USD · Spot reference",f"${float(spot):,.2f}" if spot else "Unavailable")
m2.metric("Feed condition",feed)
m3.metric("Data age",f"{age}s" if age is not None else "—")
m4.metric("Reference source","XAUS · indicative")
q1,q2,q3,q4=st.columns([1,1,1,1])
tf=q1.selectbox("TIMEFRAME",["1m","5m","15m","1h","4h","1d"],index=2)
period=q2.selectbox("HISTORY",["1mo","3mo","6mo","1y","2y","5y"],index=2)
ema20=q3.toggle("EMA 20",True);ema50=q4.toggle("EMA 50",True)
try:
    df=get_bars(tf,period)
except Exception as ex:
    df=pd.DataFrame();st.error(f"Data API error: {ex}")
if not df.empty:
    for n in [20,50,200]:df[f"e{n}"]=df.c.ewm(span=n,adjust=False).mean()
    bars=[{"time":int(t.timestamp()),"open":float(o),"high":float(h),"low":float(l),"close":float(c)} for t,o,h,l,c in zip(df.dt,df.o,df.h,df.l,df.c)]
    lines={}
    if ema20:lines["e20"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e20)]
    if ema50:lines["e50"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e50)]
    if len(df)>=200:lines["e200"]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df.e200)]
    data=json.dumps({"bars":bars,"lines":lines,"tf":tf,"count":len(df)})
    html_doc=r"""<!doctype html><html><head><meta charset="utf-8"><script src="https://unpkg.com/lightweight-charts@4.2.2/dist/lightweight-charts.standalone.production.js"></script>
<style>*{box-sizing:border-box}body{margin:0;background:#080d16;color:#dce6f5;font:11px Arial}#head{height:34px;padding:10px;border-bottom:1px solid #203149;color:#9eacc0}#chart{height:610px}#foot{height:25px;padding:6px 10px;border-top:1px solid #203149;color:#7487a2}</style></head><body>
<div id="head"><b style="color:#eef4ff">XAU/USD</b>　·　<span id="tf"></span>　·　<span id="count"></span> OHLC bars <span style="float:right;color:#f4c95d">EMA20　</span><span style="float:right;color:#55a7ff">EMA50　</span><span style="float:right;color:#b68cff">EMA200　</span></div>
<div id="chart"></div><div id="foot">Crosshair enabled · Scroll to zoom · Drag to pan · Fit content</div>
<script>
const D=__DATA__;document.getElementById('tf').textContent=D.tf;document.getElementById('count').textContent=D.count;
const el=document.getElementById('chart');
const c=LightweightCharts.createChart(el,{width:el.clientWidth,height:610,layout:{background:{type:'solid',color:'#080d16'},textColor:'#91a2ba',fontSize:11},grid:{vertLines:{color:'#17263a'},horzLines:{color:'#17263a'}},crosshair:{mode:0,vertLine:{color:'#8496ad',style:2},horzLine:{color:'#8496ad',style:2}},rightPriceScale:{borderColor:'#26374e',scaleMargins:{top:.08,bottom:.08}},timeScale:{borderColor:'#26374e',timeVisible:true,rightOffset:5,barSpacing:8},handleScroll:true,handleScale:true});
const s=c.addCandlestickSeries({upColor:'#18b887',downColor:'#ed5969',borderUpColor:'#18b887',borderDownColor:'#ed5969',wickUpColor:'#18b887',wickDownColor:'#ed5969',priceLineVisible:true});s.setData(D.bars);
for(const [k,col] of [['e20','#f4c95d'],['e50','#55a7ff'],['e200','#b68cff']])if(D.lines[k]?.length){const l=c.addLineSeries({color:col,lineWidth:2,priceLineVisible:false,crosshairMarkerVisible:false});l.setData(D.lines[k])}
c.timeScale().fitContent();new ResizeObserver(x=>c.applyOptions({width:x[0].contentRect.width})).observe(el);
</script></body></html>"""
    html_doc=html_doc.replace("__DATA__",data)
    st.markdown("**PRICE ACTION & MARKET STRUCTURE**",help="Financial chart rendered with TradingView Lightweight Charts")
    left,right=st.columns([4.5,1])
    with left:components.html(html_doc,height=670,scrolling=False)
    with right:
        st.markdown("**MARKET SNAPSHOT**")
        z=df.iloc[-1]
        st.metric("Last close",f"${z.c:,.2f}")
        st.metric("EMA 20",f"${z.e20:,.2f}")
        st.metric("EMA 50",f"${z.e50:,.2f}")
        st.metric("EMA 200",f"${z.e200:,.2f}" if len(df)>=200 else "Need 200 bars")
        st.caption(f"High: {df.tail(100).h.max():,.2f}")
        st.caption(f"Low: {df.tail(100).l.min():,.2f}")
        st.caption(f"Last bar: {z.dt}")
else:
    st.error("No valid OHLC data returned. Chart is intentionally not fabricated.")
st.divider()
a,b,c=st.columns(3)
a.metric("SIGNAL ENGINE","NO TRADE")
b.metric("DATA MODE","Reference / OHLC")
c.metric("VALIDATION","Prototype")
st.caption("V2.1 · XAUS is indicative reference, not broker execution. EMA200 hidden until 200 real bars exist. Independent minute collector and validated secondary feed remain to be implemented.")
