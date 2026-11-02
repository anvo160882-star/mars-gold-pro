
import streamlit as st
import streamlit.components.v1 as components
import requests, pandas as pd, numpy as np, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="M.A.R.S. GOLD PRO V2.4",page_icon="✦",layout="wide")
st.markdown("""<style>
.block-container{max-width:1850px;padding:1.05rem 1.45rem 2rem}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:radial-gradient(ellipse at 50% -18%,#14243a 0%,#070d17 54%)}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(20,36,57,.96),rgba(9,18,31,.98));border:1px solid #2a405d;border-radius:12px;padding:13px 15px;box-shadow:0 7px 22px rgba(0,0,0,.16);min-height:92px}
[data-testid="stMetricLabel"]{color:#91a8c5;font-size:10px;text-transform:uppercase;letter-spacing:.11em}
[data-testid="stMetricValue"]{font-size:24px;color:#f2f6fc;font-weight:700}
[data-testid="stMetricDelta"]{font-size:11px}
.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid #263b55;padding:0 0 7px}
.stTabs [data-baseweb="tab"]{font-size:11px;font-weight:650;letter-spacing:.035em;color:#9aabc2;background:#0d1929;border:1px solid #20344d;border-radius:8px 8px 5px 5px;padding:9px 13px}
.stTabs [aria-selected="true"]{color:#f4d27d!important;background:linear-gradient(180deg,#26354a,#142236)!important;border-color:#806b3d!important}
div[data-testid="stAlert"]{border-radius:10px;border:1px solid #2b4059}
div[data-testid="stPlotlyChart"]{background:linear-gradient(145deg,rgba(15,27,43,.65),rgba(8,16,28,.55));border:1px solid rgba(48,69,96,.62);border-radius:12px;padding:5px 7px 0}
div[data-testid="stSelectbox"] label,div[data-testid="stToggle"] label{color:#a8bad1;font-size:11px;font-weight:650;letter-spacing:.06em}
h1,h2,h3,h4{letter-spacing:.01em}
hr{border-color:#263b55}
small,.stCaption{color:#91a3bc}
button[kind="secondary"]{border:1px solid #314967}
@media(max-width:800px){.block-container{padding:.7rem .7rem 1.5rem}[data-testid="stMetricValue"]{font-size:19px}.stTabs [data-baseweb="tab"]{padding:7px 8px;font-size:10px}}
</style>""",unsafe_allow_html=True)
API="https://xaus.com/api/v1"; H={"User-Agent":"MARS-GOLD-PRO-V2.4","Accept":"application/json"}

@st.cache_data(ttl=50)
def spot_data():
 r=requests.get(API+"/spot?compact=1",headers=H,timeout=12);r.raise_for_status();j=r.json();d=j.get("data",j)
 return d.get("spot_usd_oz") or j.get("spot_usd_oz"),d.get("data_state") or j.get("data_state") or {},j
@st.cache_data(ttl=50)
def bars_data(tf,period):
 r=requests.get(API+"/chart",params={"symbol":"xau","range":period,"interval":tf},headers=H,timeout=25);r.raise_for_status();j=r.json();d=j.get("data",j)
 rows=d.get("candles") or d.get("points") or d.get("values") or j.get("candles") or j.get("points") or []
 if isinstance(rows,dict):rows=rows.get("candles",[])
 x=pd.DataFrame(rows)
 if x.empty:return x
 x=x.rename(columns={"timestamp":"t","time":"t","open":"o","high":"h","low":"l","close":"c"})
 if not set(["t","o","h","l","c"]).issubset(x.columns):return pd.DataFrame()
 x["dt"]=pd.to_datetime(x.t,unit="s",utc=True,errors="coerce") if pd.api.types.is_numeric_dtype(x.t) else pd.to_datetime(x.t,utc=True,errors="coerce")
 for k in ["o","h","l","c"]:x[k]=pd.to_numeric(x[k],errors="coerce")
 return x.dropna(subset=["dt","o","h","l","c"]).sort_values("dt").drop_duplicates("dt").tail(3000).reset_index(drop=True)

def sim(df):
 r=np.diff(np.log(df.c.values));v=max(float(np.std(r[-240:])),.00015);p=float(df.c.iloc[-1])
 hs=np.array([4,8,12,24,48,72,120,168.],float);rng=np.random.default_rng(24)
 paths=p*np.exp(rng.normal(0,v,size=(5000,len(hs)))*np.sqrt(hs)[None,:])
 return hs,np.quantile(paths,[.05,.10,.25,.5,.75,.9,.95],axis=0),paths,v

def dark(fig,height=480):
 fig.update_layout(template="plotly_dark",height=height,paper_bgcolor="#070d17",plot_bgcolor="#0b1422",
  font=dict(color="#d0dced",family="Inter, Arial",size=12),
  margin=dict(l=34,r=28,t=62,b=34),
  legend=dict(orientation="h",y=1.13,x=0,font=dict(size=10)),
  hovermode="x unified",
  title=dict(font=dict(size=15,color="#edf4ff"),x=0.015,xanchor="left"),
  hoverlabel=dict(bgcolor="#14243a",bordercolor="#48617f",font=dict(color="#f4f7fb",size=11)))
 fig.update_xaxes(gridcolor="#1b2b40",zerolinecolor="#1b2b40")
 fig.update_yaxes(gridcolor="#1b2b40",zerolinecolor="#1b2b40")
 return fig

st.markdown("""<div style="display:flex;justify-content:space-between;border-bottom:1px solid #24364d;padding-bottom:13px">
<div><div style="font-size:25px;font-weight:800;color:#eef5ff">✦ M.A.R.S. <span style="color:#66b2ff">GOLD PRO</span> <span style="font-size:12px;color:#8298b5">V2.4 QUANT WORKSTATION</span></div>
<div style="font-size:10px;letter-spacing:2px;color:#8194ae">XAU/USD · PROBABILITY VISUALIZATION · TRADE DECISION ENGINE</div></div>
<div style="font-size:10px;color:#7d91a9;text-align:right">LIVE RESEARCH TERMINAL<br>DATA INTEGRITY FIRST</div></div>""",unsafe_allow_html=True)
try:
 spot,state,raw=spot_data();feed=(state.get("state") or state.get("status") or "UNKNOWN").upper();age=state.get("age_seconds")
except Exception:
 spot,state,raw=None,{},{};feed="UNAVAILABLE";age=None
a,b,c,d=st.columns(4)
a.metric("XAU/USD REFERENCE",f"${float(spot):,.2f}" if spot else "Unavailable")
b.metric("SPOT FEED",feed);c.metric("DATA AGE",f"{age}s" if age is not None else "—");d.metric("SOURCE","XAUS · indicative")
p,q,r,s=st.columns([1,1,1,1])
tf=p.selectbox("TIMEFRAME",["1m","5m","15m","1h","4h","1d"],2)
period=q.selectbox("HISTORY",["1mo","3mo","6mo","1y","2y","5y"],2)
ema20=r.toggle("EMA 20",True);ema50=s.toggle("EMA 50",True)
try:df=bars_data(tf,period);err=None
except Exception as ex:df=pd.DataFrame();err=str(ex)
if not df.empty:
 for n in [20,50,200]:df[f"e{n}"]=df.c.ewm(span=n,adjust=False).mean()
tabs=st.tabs(["01 MARKET ANALYSIS","02 PROBABILITY ZONES","03 3D FORECAST","04 TRADE INTELLIGENCE","05 DATA HEALTH"])
with tabs[0]:
 st.markdown("#### PRICE ACTION & MARKET STRUCTURE")
 if len(df):
  bd=[{"time":int(t.timestamp()),"open":float(o),"high":float(h),"low":float(l),"close":float(c)} for t,o,h,l,c in zip(df.dt,df.o,df.h,df.l,df.c)]
  ls={}
  for n,on in [(20,ema20),(50,ema50),(200,len(df)>=200)]:
   if on:ls[str(n)]=[{"time":int(t.timestamp()),"value":float(v)} for t,v in zip(df.dt,df[f"e{n}"])]
  payload=json.dumps({"bars":bd,"lines":ls,"tf":tf})
  h=r"""<!doctype html><html><head><script src="https://unpkg.com/lightweight-charts@4.2.2/dist/lightweight-charts.standalone.production.js"></script><style>body{margin:0;background:#070d17;color:#c9d7e9;font:12px Arial}#chart{height:590px}#h{padding:10px;border-bottom:1px solid #22344c}</style></head><body><div id="h">XAU/USD　·　<span id="tf"></span>　·　Candles / EMA / Crosshair / Zoom</div><div id="chart"></div><script>const D=__D__;document.getElementById('tf').textContent=D.tf;let e=document.getElementById('chart');let c=LightweightCharts.createChart(e,{width:e.clientWidth,height:590,layout:{background:{type:'solid',color:'#070d17'},textColor:'#9aacc4'},grid:{vertLines:{color:'#192a40'},horzLines:{color:'#192a40'}},rightPriceScale:{borderColor:'#263b55'},timeScale:{borderColor:'#263b55',timeVisible:true},crosshair:{mode:0},handleScroll:true,handleScale:true});let x=c.addCandlestickSeries({upColor:'#19bf91',downColor:'#f05b70',wickUpColor:'#19bf91',wickDownColor:'#f05b70',borderUpColor:'#19bf91',borderDownColor:'#f05b70'});x.setData(D.bars);for(let [k,col] of [['20','#f5c85d'],['50','#55aaff'],['200','#b58cff']])if(D.lines[k]){let z=c.addLineSeries({color:col,lineWidth:2,priceLineVisible:false});z.setData(D.lines[k])}c.timeScale().fitContent();new ResizeObserver(a=>c.applyOptions({width:a[0].contentRect.width})).observe(e)</script></body></html>""".replace("__D__",payload)
  left,right=st.columns([4.3,1])
  with left:components.html(h,height=625)
  with right:
   z=df.iloc[-1];st.metric("LAST CLOSE",f"${z.c:,.2f}");st.metric("EMA20",f"${z.e20:,.2f}");st.metric("EMA50",f"${z.e50:,.2f}");st.metric("EMA200",f"${z.e200:,.2f}" if len(df)>=200 else "N/A")
 else:st.error(f"OHLC unavailable: {err or 'No valid bars'}")
with tabs[1]:
 st.markdown("#### PROBABILITY ZONES · DISTRIBUTION FAN")
 if len(df)>30:
  hs,qq,paths,v=sim(df);labels=["4H","8H","12H","24H","48H","3D","5D","7D"];now=float(df.c.iloc[-1])
  f=go.Figure()
  # layered percentile envelopes
  f.add_trace(go.Scatter(x=labels,y=qq[6],line=dict(width=0),showlegend=False,hoverinfo="skip"))
  f.add_trace(go.Scatter(x=labels,y=qq[0],line=dict(width=0),fill="tonexty",fillcolor="rgba(238,83,104,.18)",name="90% outer band"))
  f.add_trace(go.Scatter(x=labels,y=qq[5],line=dict(width=0),showlegend=False,hoverinfo="skip"))
  f.add_trace(go.Scatter(x=labels,y=qq[1],line=dict(width=0),fill="tonexty",fillcolor="rgba(244,184,75,.20)",name="80% band"))
  f.add_trace(go.Scatter(x=labels,y=qq[4],line=dict(width=0),showlegend=False,hoverinfo="skip"))
  f.add_trace(go.Scatter(x=labels,y=qq[2],line=dict(width=0),fill="tonexty",fillcolor="rgba(37,184,139,.24)",name="50% core"))
  f.add_trace(go.Scatter(x=labels,y=qq[3],line=dict(color="#ffe08a",width=3),mode="lines+markers",name="Median path"))
  f.add_hline(y=now,line_dash="dash",line_color="#d3deed",annotation_text=f"Spot {now:,.2f}")
  f.update_layout(title="Forward price cone · Monte Carlo quantile envelopes",yaxis_title="XAU/USD · USD/oz",xaxis_title="Forecast horizon")
  st.plotly_chart(dark(f,500),use_container_width=True)
  u,vv,w=st.columns(3)
  u.metric("24H MEDIAN",f"${qq[3,3]:,.2f}",f"{(qq[3,3]/now-1)*100:+.2f}%")
  vv.metric("24H 80% RANGE",f"${qq[1,3]:,.0f} – ${qq[5,3]:,.0f}")
  prob=float((paths[:,3]>now).mean()*100);w.metric("SIMULATED UPSIDE SHARE",f"{prob:.1f}%")
  # Distribution ridgeline-style heatmap
  st.markdown("#### PRICE PROBABILITY MAP · TIME × PRICE")
  price_grid=np.linspace(np.quantile(paths,.01),np.quantile(paths,.99),70)
  density=np.array([np.histogram(paths[:,i],bins=price_grid,density=True)[0] for i in range(len(hs))]).T
  heat=go.Figure(go.Heatmap(x=labels,y=(price_grid[:-1]+price_grid[1:])/2,z=density,colorscale="Turbo",colorbar=dict(title="Density")))
  heat.update_layout(title="Where simulated prices cluster at each horizon",xaxis_title="Horizon",yaxis_title="Price (USD/oz)")
  st.plotly_chart(dark(heat,430),use_container_width=True)
  st.caption("Quantile envelopes and density map are generated from historical-return Monte Carlo simulations. They are not calibrated probabilities or validated forecasts.")
 else:st.warning("Need more valid OHLC bars.")
with tabs[2]:
 st.markdown("#### 3D FORECAST · PRICE DENSITY SURFACE")
 if len(df)>30:
  hs,qq,paths,v=sim(df);g=np.linspace(np.quantile(paths,.01),np.quantile(paths,.99),65)
  dens=np.array([np.histogram(paths[:,i],bins=g,density=True)[0] for i in range(len(hs))]).T
  yy=(g[:-1]+g[1:])/2;X,Y=np.meshgrid(hs,yy)
  fig=go.Figure(go.Surface(x=X,y=Y,z=dens,colorscale="Turbo",opacity=.96,contours={"z":{"show":True,"usecolormap":True,"project_z":True}},colorbar=dict(title="Density")))
  fig.update_layout(title="Interactive 3D scenario density · 5,000 paths",scene=dict(xaxis_title="Hours forward",yaxis_title="Price USD/oz",zaxis_title="Probability density",camera=dict(eye=dict(x=1.7,y=1.6,z=1.2))),uirevision="mars3d")
  st.plotly_chart(dark(fig,680),use_container_width=True)
  st.caption(f"Historical volatility input: {v*100:.4f}% per bar · drag to rotate · scroll to zoom.")
 else:st.warning("Need more valid OHLC bars.")
with tabs[3]:
 st.markdown("#### TRADE INTELLIGENCE · M.A.R.S. DECISION COCKPIT")
 if len(df)>50:
  z=df.iloc[-1];delta=df.c.diff();gain=delta.clip(lower=0).rolling(14).mean().iloc[-1];loss=(-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
  rsi=100-100/(1+gain/loss) if loss and np.isfinite(loss) else 50
  atr=pd.concat([df.h-df.l,(df.h-df.c.shift()).abs(),(df.l-df.c.shift()).abs()],axis=1).max(axis=1).rolling(14).mean().iloc[-1]
  bias="BULLISH" if z.c>z.e20>z.e50 else ("BEARISH" if z.c<z.e20<z.e50 else "MIXED")
  x1,x2,x3,x4=st.columns(4);x1.metric("MARKET BIAS",bias);x2.metric("RSI 14",f"{rsi:.1f}");x3.metric("ATR 14",f"{atr:.2f}");x4.metric("PRICE",f"${z.c:,.2f}")
  # gauge for RSI
  gauge=go.Figure(go.Indicator(mode="gauge+number",value=float(rsi),title={"text":"Momentum · RSI 14"},gauge={"axis":{"range":[0,100]},"bar":{"color":"#69b5ff"},"steps":[{"range":[0,30],"color":"#174d48"},{"range":[30,70],"color":"#26374f"},{"range":[70,100],"color":"#633044"}],"threshold":{"line":{"color":"#f3ca67","width":3},"value":50}}))
  gauge.update_layout(height=260,margin=dict(l=20,r=20,t=40,b=10),paper_bgcolor="#070d17",font={"color":"#dbe7f5"})
  st.plotly_chart(gauge,use_container_width=True)
 else:bias="INSUFFICIENT DATA";rsi=atr=np.nan
 st.markdown("#### SETUP VALIDATION PIPELINE")
 stages=[("01 · MAJOR S/R","Identify reaction zones","PENDING FULL STRUCTURE ENGINE"),("02 · H4 BIAS","Higher-timeframe direction","NOT VERIFIED"),("03 · PRICE REACTION","Rejection / acceptance / sweep","WAIT FOR CONFIRMATION"),("04 · MOMENTUM","RSI / EMA proxy","OBSERVATIONAL ONLY"),("05 · RISK / REWARD","Minimum 1:2","NO VALID SETUP"),("06 · POSITION SIZE","Risk-based sizing","LOCKED")]
 cols=st.columns(3)
 for i,(title,desc,status) in enumerate(stages):
  with cols[i%3]:
   st.markdown(f"""<div style="background:linear-gradient(145deg,#12243a,#0b1421);border:1px solid #263d59;border-radius:12px;padding:15px;min-height:126px;margin-bottom:10px"><div style="color:#70b8ff;font-size:11px;font-weight:700">{title}</div><div style="color:#e4edf8;font-size:14px;font-weight:600;margin:8px 0">{desc}</div><div style="color:#e7bd6d;font-size:10px;letter-spacing:.06em">{status}</div></div>""",unsafe_allow_html=True)
 st.error("NO TRADE · BUY/SELL bị khóa cho đến khi xác thực H4/H1/M15, broker spread, giá khớp lệnh và walk-forward backtest.")
 st.caption("M.A.R.S. sequence: Major S/R → H4 bias → price reaction → momentum/structure → R:R ≥ 1:2 → position sizing.")
with tabs[4]:
 st.markdown("#### DATA HEALTH · DATA RELIABILITY MONITOR")
 st.write("Đây là bảng kiểm tra chất lượng và đường đi dữ liệu. Nó cho biết feed nào đang chạy, dữ liệu mới đến đâu, thành phần nào đã có và phần nào chưa được kết nối.")
 agev=float(age) if age is not None else 99999
 status_color="success" if feed=="FRESH" and agev<=120 else ("warning" if agev<=300 else "error")
 c1,c2,c3=st.columns(3);c1.metric("SPOT SOURCE STATUS",feed);c2.metric("SPOT AGE",f"{age}s" if age is not None else "Unknown");c3.metric("VALID OHLC BARS",f"{len(df):,}")
 if status_color=="success":st.success("SPOT REFERENCE: FRESH — nguồn báo giá tham chiếu mới. Đây không phải xác nhận broker feed.")
 elif status_color=="warning":st.warning("SPOT REFERENCE: DELAYED — dữ liệu có thể đã trễ.")
 else:st.error("SPOT REFERENCE: UNAVAILABLE / UNVERIFIED.")
 items=[
 ("XAUS spot reference","Giá spot tham chiếu và timestamp","CONNECTED" if spot else "FAILED"),
 ("XAUS OHLC endpoint","Nến theo timeframe đang chọn","CONNECTED" if len(df) else "FAILED"),
 ("Candle validation","Timestamp, OHLC numeric, duplicate removal","BASIC"),
 ("Minute collector","Thu thập nền mỗi phút khi dashboard đóng","NOT BUILT"),
 ("Persistent database","Kho lịch sử độc lập Streamlit","NOT BUILT"),
 ("Backup OHLC provider","Nguồn OHLC dự phòng đã xác thực","NOT CONNECTED"),
 ("Broker bid/ask feed","Giá có thể thực thi và spread","NOT CONNECTED")]
 for title,desc,status in items:
  aa,bb,cc=st.columns([2,4,1.3]);aa.markdown(f"**{title}**");bb.caption(desc)
  if status=="CONNECTED":cc.success(status)
  elif status=="BASIC":cc.info(status)
  else:cc.warning(status)
 st.markdown("#### SOURCE TIMESTAMPS")
 st.json({"spot_state":feed,"spot_age_seconds":age,"spot_as_of":state.get("as_of") or state.get("updated_at"),"ohlc_source":"XAUS chart endpoint","last_bar_utc":str(df.dt.iloc[-1]) if len(df) else None,"timeframe":tf,"history":period})
 with st.expander("Raw API response"):st.json(raw if isinstance(raw,dict) else {})
 st.info("Quan trọng: ứng dụng hiện fetch khi trang được tải hoặc tương tác. Chưa có dịch vụ thu thập dữ liệu chạy độc lập mỗi phút. FRESH chỉ phản ánh trạng thái spot do XAUS trả về.")
st.caption("M.A.R.S. GOLD PRO V2.4 · Visual quant prototype · Indicative spot is not broker execution price.")
