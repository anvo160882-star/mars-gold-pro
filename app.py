
import streamlit as st
import streamlit.components.v1 as components
import requests, pandas as pd, numpy as np, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="M.A.R.S. GOLD PRO V2.3",page_icon="✦",layout="wide")
st.markdown("""<style>
.block-container{max-width:1800px;padding:1rem 1.35rem}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:#080d16}
[data-testid="stMetric"]{background:#0d1725;border:1px solid #203149;border-radius:9px;padding:10px}
[data-testid="stMetricLabel"]{color:#8294ad;font-size:10px;text-transform:uppercase}
[data-testid="stMetricValue"]{font-size:22px;color:#eaf1fb}
.stTabs [data-baseweb="tab-list"]{gap:18px}
.stTabs [data-baseweb="tab"]{color:#91a3bc;font-size:12px}
div[data-testid="stAlert"]{border-radius:9px}
</style>""",unsafe_allow_html=True)
API="https://xaus.com/api/v1"; H={"User-Agent":"MARS-GOLD-PRO-V2.3","Accept":"application/json"}

@st.cache_data(ttl=50)
def get_spot():
    r=requests.get(API+"/spot?compact=1",headers=H,timeout=12);r.raise_for_status()
    j=r.json();d=j.get("data",j);p=d.get("spot_usd_oz") or j.get("spot_usd_oz")
    s=d.get("data_state") or j.get("data_state") or {}
    return float(p) if p else None,s,j

@st.cache_data(ttl=50)
def get_bars(tf,period):
    r=requests.get(API+"/chart",params={"symbol":"xau","range":period,"interval":tf},headers=H,timeout=25);r.raise_for_status()
    j=r.json();d=j.get("data",j);rows=d.get("candles") or d.get("points") or d.get("values") or j.get("candles") or j.get("points") or []
    if isinstance(rows,dict):rows=rows.get("candles",[])
    x=pd.DataFrame(rows)
    if x.empty:return x
    x=x.rename(columns={"timestamp":"t","time":"t","open":"o","high":"h","low":"l","close":"c"})
    if not set(["t","o","h","l","c"]).issubset(x.columns):return pd.DataFrame()
    x["dt"]=pd.to_datetime(x.t,unit="s",utc=True,errors="coerce") if pd.api.types.is_numeric_dtype(x.t) else pd.to_datetime(x.t,utc=True,errors="coerce")
    for k in ["o","h","l","c"]:x[k]=pd.to_numeric(x[k],errors="coerce")
    return x.dropna(subset=["dt","o","h","l","c"]).sort_values("dt").drop_duplicates("dt").tail(3000).reset_index(drop=True)

def scenario_model(df):
    close=df.c.astype(float).values
    r=np.diff(np.log(close))
    sigma=max(float(np.std(r[-240:])),0.00015)
    spot=float(close[-1])
    hs=np.array([4,8,12,24,48,72,120,168],dtype=float)
    paths=4000
    rng=np.random.default_rng(19)
    sims=spot*np.exp(rng.normal(0,sigma*np.sqrt(hs)[None,:],size=(paths,len(hs))))
    q=np.quantile(sims,[.05,.10,.25,.50,.75,.90,.95],axis=0)
    return hs,q,sims,sigma

def fmt(v):return f"${v:,.2f}"

st.markdown("""<div style="display:flex;justify-content:space-between;border-bottom:1px solid #203149;padding-bottom:12px">
<div><div style="font-size:24px;font-weight:800;color:#edf4ff">✦ M.A.R.S. <span style="color:#62a8ff">GOLD PRO</span> <small style="color:#8294ad">V2.3 VISUAL QUANT</small></div>
<div style="font-size:10px;letter-spacing:2px;color:#7d91ad">XAU/USD · MARKET STRUCTURE · PROBABILITY · TRADE INTELLIGENCE</div></div>
<div style="font-size:10px;color:#71839a;text-align:right">RESEARCH MODE<br>DATA TRANSPARENCY ON</div></div>""",unsafe_allow_html=True)
try:
    spot,state,raw=get_spot();feed=(state.get("state") or state.get("status") or "UNKNOWN").upper();age=state.get("age_seconds");asof=state.get("as_of") or state.get("updated_at")
except Exception as ex:
    spot,state,raw=None,{},{};feed="UNAVAILABLE";age=None;asof=None
m1,m2,m3,m4=st.columns(4)
m1.metric("XAU/USD · Spot reference",fmt(spot) if spot else "Unavailable")
m2.metric("Feed condition",feed);m3.metric("Data age",f"{age}s" if age is not None else "Not reported");m4.metric("Reference source","XAUS · indicative")
q1,q2,q3,q4=st.columns([1,1,1,1])
tf=q1.selectbox("CHART TIMEFRAME",["1m","5m","15m","1h","4h","1d"],index=2)
period=q2.selectbox("HISTORY",["1mo","3mo","6mo","1y","2y","5y"],index=2)
ema20=q3.toggle("EMA 20",True);ema50=q4.toggle("EMA 50",True)
try:df=get_bars(tf,period);fetch_error=None
except Exception as ex:df=pd.DataFrame();fetch_error=str(ex)
if not df.empty:
    for n in [20,50,200]:df[f"e{n}"]=df.c.ewm(span=n,adjust=False).mean()
tabs=st.tabs(["01 · MARKET ANALYSIS","02 · PROBABILITY ZONES","03 · 3D FORECAST","04 · TRADE INTELLIGENCE","05 · DATA HEALTH"])
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
            st.metric("Last close",fmt(z.c));st.metric("EMA 20",fmt(z.e20));st.metric("EMA 50",fmt(z.e50))
            st.metric("EMA 200",fmt(z.e200) if len(df)>=200 else "Need 200 bars")
            st.caption(f"Recent high: {df.tail(100).h.max():,.2f}");st.caption(f"Recent low: {df.tail(100).l.min():,.2f}")
    else:st.error(f"OHLC unavailable. {fetch_error or 'API schema not recognized.'}")
with tabs[1]:
    st.subheader("Probability Zones · forward price distribution")
    if len(df)>30:
        hs,q,sims,sigma=scenario_model(df);spot0=float(df.c.iloc[-1])
        labels=["4H","8H","12H","24H","48H","3D","5D","7D"]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=labels,y=q[6],mode="lines",line=dict(width=0),showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=labels,y=q[0],mode="lines",line=dict(width=0),fill="tonexty",fillcolor="rgba(239,89,105,.13)",name="90% range"))
        fig.add_trace(go.Scatter(x=labels,y=q[5],mode="lines",line=dict(width=0),showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=labels,y=q[1],mode="lines",line=dict(width=0),fill="tonexty",fillcolor="rgba(245,190,75,.16)",name="80% range"))
        fig.add_trace(go.Scatter(x=labels,y=q[4],mode="lines",line=dict(width=0),showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=labels,y=q[2],mode="lines",line=dict(width=0),fill="tonexty",fillcolor="rgba(40,180,135,.18)",name="50% range"))
        fig.add_trace(go.Scatter(x=labels,y=q[3],mode="lines+markers",line=dict(color="#f4d06f",width=3),name="Median scenario"))
        fig.add_hline(y=spot0,line_dash="dash",line_color="#9aa9bd",annotation_text=f"Current {spot0:,.2f}")
        fig.update_layout(template="plotly_dark",height=500,title="Forward scenario fan · quantile bands",paper_bgcolor="#080d16",plot_bgcolor="#080d16",yaxis_title="Scenario price (USD/oz)",xaxis_title="Horizon",hovermode="x unified",legend=dict(orientation="h",y=1.08))
        st.plotly_chart(fig,use_container_width=True)
        a,b,c=st.columns(3)
        a.metric("Median 24H",fmt(q[3,3]),f"{(q[3,3]/spot0-1)*100:+.2f}%")
        b.metric("80% range 24H",f"{q[1,3]:,.0f} – {q[5,3]:,.0f}")
        p_up=float((sims[:,3]>spot0).mean()*100);c.metric("Simulated P(price > spot)",f"{p_up:.1f}%")
        st.caption("Dải 50% / 80% / 90% là quantile của mô phỏng Monte Carlo từ volatility lịch sử. Tỷ lệ tăng/giảm chỉ là tần suất mô phỏng, KHÔNG phải xác suất dự báo đã hiệu chỉnh.")
    else:st.warning("Cần ít nhất 31 nến OHLC hợp lệ.")
with tabs[2]:
    st.subheader("3D Forecast · animated scenario surface")
    if len(df)>30:
        hs,q,sims,sigma=scenario_model(df)
        grid=np.linspace(np.quantile(sims,.01),np.quantile(sims,.99),55)
        dens=[np.histogram(sims[:,i],bins=grid,density=True)[0] for i in range(len(hs))]
        y=(grid[:-1]+grid[1:])/2;X,Y=np.meshgrid(hs,y);Z=np.array(dens).T
        fig=go.Figure(go.Surface(x=X,y=Y,z=Z,colorscale="Viridis",colorbar=dict(title="Density"),contours={"z":{"show":True,"usecolormap":True,"project_z":True}}))
        fig.update_layout(template="plotly_dark",height=650,title="Monte Carlo price probability density · 4,000 paths",scene=dict(xaxis_title="Hours ahead",yaxis_title="Price (USD/oz)",zaxis_title="Density",camera=dict(eye=dict(x=1.6,y=1.6,z=1.15))),paper_bgcolor="#080d16",margin=dict(l=0,r=0,t=50,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.caption(f"Simulation input volatility: {sigma*100:.3f}% per selected bar · 4,000 paths · interactive rotate/zoom.")
        st.warning("Đây là phân phối mô phỏng, không phải dự báo đã kiểm định. Chưa đưa vào Trade Intelligence.")
    else:st.warning("Cần dữ liệu OHLC đủ dài.")
with tabs[3]:
    st.subheader("Trade Intelligence · decision cockpit")
    if len(df)>200:
        z=df.iloc[-1];bull=z.c>z.e20>z.e50>z.e200;bear=z.c<z.e20<z.e50<z.e200
        trend="BULLISH" if bull else ("BEARISH" if bear else "MIXED")
        atr=float(pd.concat([(df.h-df.l),(df.h-df.c.shift()).abs(),(df.l-df.c.shift()).abs()],axis=1).max(axis=1).rolling(14).mean().iloc[-1])
        rsi_delta=df.c.diff();gain=rsi_delta.clip(lower=0).rolling(14).mean().iloc[-1];loss=(-rsi_delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/loss)) if loss and not np.isnan(loss) else 50
        recent=df.tail(100);sup=float(recent.l.min());res=float(recent.h.max())
    else:trend="INSUFFICIENT DATA";atr=np.nan;rsi=np.nan;sup=res=np.nan
    a,b,c,d=st.columns(4)
    a.metric("Directional bias",trend);b.metric("RSI(14)",f"{rsi:.1f}" if np.isfinite(rsi) else "—");c.metric("ATR(14)",f"{atr:.2f}" if np.isfinite(atr) else "—");d.metric("Structure range",f"{sup:,.0f} – {res:,.0f}" if np.isfinite(sup) else "—")
    st.markdown("#### M.A.R.S. decision gates")
    gates=[
      ("01","Major Support / Resistance","Range reference calculated" if np.isfinite(sup) else "OHLC not sufficient"),
      ("02","H4 directional bias","Not verified — chart timeframe may not be H4"),
      ("03","Price reaction","Needs live H4/H1/M15 confirmation"),
      ("04","Momentum / structure","RSI and EMA proxy available" if np.isfinite(rsi) else "Not available"),
      ("05","Risk : Reward ≥ 1:2","Not calculated — no validated setup"),
      ("06","Position sizing","Locked until stop distance and account risk are supplied")
    ]
    for num,title,desc in gates:
        x,y=st.columns([1.2,4])
        x.markdown(f"<div style='padding:8px;color:#70aaff;font-weight:700'>{num}</div>",unsafe_allow_html=True)
        y.markdown(f"**{title}**  \n<span style='color:#8294ad;font-size:12px'>{desc}</span>",unsafe_allow_html=True)
        st.markdown("<hr style='margin:2px 0;border-color:#1b2a3e'>",unsafe_allow_html=True)
    st.error("NO TRADE · Không phát BUY/SELL vì chưa xác minh đồng thời H4/H1/M15, spread broker, entry/SL thực thi và kết quả walk-forward.")
    st.caption("M.A.R.S.: Major S/R → H4 bias → price reaction → momentum/structure → R:R ≥ 1:2 → position sizing. Tactical Entry allowed; break + retest không bắt buộc.")
with tabs[4]:
    st.subheader("Data Health · tình trạng sức khỏe dữ liệu")
    st.write("Trang này trả lời 4 câu hỏi: dữ liệu đến từ đâu, mới đến mức nào, có đủ nến không, và hệ thống có được phép dùng dữ liệu để phân tích hay không.")
    s1,s2,s3=st.columns(3)
    s1.metric("Spot feed",feed);s2.metric("Data age",f"{age}s" if age is not None else "Unknown");s3.metric("OHLC bars",f"{len(df):,}")
    age_num=float(age) if age is not None else None
    if feed=="FRESH" and age_num is not None and age_num<=120:
        st.success("SPOT FEED HEALTHY · Nguồn tham chiếu báo dữ liệu mới.")
    elif age_num is not None and age_num<=300:
        st.warning("SPOT FEED DELAYED · Cần thận trọng với dữ liệu trễ.")
    else:st.error("SPOT FEED NOT VERIFIED · Không xác nhận được dữ liệu mới.")
    st.markdown("#### Data pipeline")
    pipe=[
      ("XAUS spot reference","Lấy giá spot tham chiếu","OK" if spot else "FAILED"),
      ("OHLC chart endpoint",f"Timeframe {tf} · {period}","OK" if len(df)>0 else "FAILED"),
      ("Candle integrity","OHLC numeric, timestamp parse, duplicate removal","BASIC CHECK"),
      ("Independent minute collector","Chạy nền khi dashboard đóng","NOT IMPLEMENTED"),
      ("Persistent database","Lưu lịch sử độc lập Streamlit","NOT IMPLEMENTED"),
      ("Verified backup OHLC provider","Nguồn dự phòng OHLC đã kiểm thử","NOT IMPLEMENTED"),
      ("Broker execution feed","Giá bid/ask thực thi từ broker","NOT CONNECTED")
    ]
    for title,desc,status in pipe:
        x,y,z=st.columns([2,4,1.2])
        x.markdown(f"**{title}**");y.caption(desc)
        if status=="OK":z.success(status)
        elif status=="BASIC CHECK":z.info(status)
        else:z.warning(status)
    st.markdown("#### Data timestamps & provenance")
    st.write({"spot_as_of":asof,"spot_age_seconds":age,"ohlc_source":"XAUS chart endpoint","last_ohlc_utc":str(df.dt.iloc[-1]) if len(df) else None,"timeframe":tf,"history":period})
    with st.expander("Raw spot API response"):st.json(raw if isinstance(raw,dict) else {})
    st.info("Lưu ý: dashboard hiện lấy dữ liệu khi tải/làm mới trang. Chưa có collector chạy độc lập mỗi phút. 'FRESH' là trạng thái do nguồn spot trả về, không chứng minh toàn bộ OHLC hoặc broker feed đang live.")
st.caption("M.A.R.S. GOLD PRO V2.3 · Research prototype · Indicative data is not broker execution price.")
