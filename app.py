import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# ============================================================
# M.A.R.S. GOLD PRO — Streamlit rebuild
# Real XAUS public spot + daily history; optional broker CSVs.
# No fabricated intraday OHLC, no uncalibrated trade signals.
# ============================================================

st.set_page_config(
    page_title="M.A.R.S. GOLD PRO",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

C = {
    "bg": "#080E18", "panel": "#111D2C", "panel2": "#16263A",
    "line": "#28394E", "muted": "#91A3B9", "text": "#EDF3FA",
    "gold": "#EDC45E", "green": "#31C18E", "red": "#EF6B7B",
    "blue": "#6EA8FE", "amber": "#E8B45C",
}
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Manrope', sans-serif; }}
.stApp {{ background: radial-gradient(ellipse at 55% -12%, #1B3048 0%, {C['bg']} 52%); color:{C['text']}; }}
[data-testid="stSidebar"] {{ background:#0B1421; border-right:1px solid {C['line']}; }}
.block-container {{ padding-top:1.2rem; max-width:1600px; }}
h1,h2,h3 {{ letter-spacing:-.035em; }}
h1 {{ font-weight:800; }}
.mars-eyebrow {{ color:{C['gold']}; font-size:10px; font-weight:800; letter-spacing:.20em; }}
.mars-sub {{ color:{C['muted']}; font-size:12px; }}
.mars-card {{ background:linear-gradient(145deg,#142338,#101A28); border:1px solid {C['line']};
 border-radius:14px; padding:15px 17px; min-height:104px; }}
.mars-k {{ color:{C['muted']}; font-size:10px; letter-spacing:.12em; font-weight:800; text-transform:uppercase; }}
.mars-v {{ color:{C['text']}; font-size:26px; font-weight:800; margin-top:5px; line-height:1.2; }}
.mars-hint {{ color:{C['muted']}; font-size:11px; margin-top:5px; }}
.mars-section {{ color:{C['gold']}; font-size:10px; font-weight:800; letter-spacing:.18em; }}
.mars-note {{ border-left:3px solid {C['amber']}; background:#211D15; padding:11px 14px;
 border-radius:0 9px 9px 0; color:#E5D6B5; font-size:12px; }}
.mars-good {{ color:{C['green']}; }} .mars-bad {{ color:{C['red']}; }}
div[data-testid="stMetric"] {{ background:linear-gradient(145deg,#142338,#101A28);
 border:1px solid {C['line']}; padding:13px 15px; border-radius:12px; }}
div[data-testid="stMetricLabel"] {{ color:{C['muted']}; }}
div[data-testid="stMetricValue"] {{ font-family:'DM Mono',monospace; }}
.stButton>button {{ border-radius:9px; border:1px solid #465B73; background:#17283D; color:#EDF3FA; }}
.stButton>button:hover {{ border-color:{C['gold']}; color:{C['gold']}; }}
.stTabs [data-baseweb="tab"] {{ color:{C['muted']}; }}
hr {{ border-color:{C['line']}; }}
small {{ color:{C['muted']}; }}
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C["muted"], family="Manrope", size=11),
    margin=dict(l=42, r=18, t=30, b=38),
    xaxis=dict(gridcolor="rgba(145,163,185,.13)", zerolinecolor=C["line"]),
    yaxis=dict(gridcolor="rgba(145,163,185,.13)", zerolinecolor=C["line"]),
    legend=dict(orientation="h", y=1.12, x=0),
    hovermode="x unified",
)

BASE = "https://xaus.com/api/v1/"

@st.cache_data(ttl=55, show_spinner=False)
def fetch_json(path):
    r = requests.get(BASE + path, timeout=15, headers={"User-Agent":"MARS-GOLD-PRO/1.0"})
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=55, show_spinner=False)
def load_public_data():
    spot = fetch_json("spot?compact=1")
    hist = fetch_json("history")
    intraday = fetch_json("intraday?symbol=xau&hours=48")
    price = float(spot.get("spot_usd_oz"))
    points = hist.get("points", [])
    ipoints = intraday.get("points", [])
    if not np.isfinite(price) or not points:
        raise ValueError("API không trả về spot hoặc daily history hợp lệ.")
    df = pd.DataFrame(points)
    df["date"] = pd.to_datetime(df["d"], errors="coerce", utc=True)
    for col in ["o", "h", "l", "c"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "c"]).sort_values("date").drop_duplicates("date")
    return spot, price, df, ipoints

def fmt_price(x):
    return "—" if x is None or not np.isfinite(float(x)) else f"${float(x):,.2f}"

def card(label, value, hint="", color=None):
    col = color or C["text"]
    st.markdown(f"""<div class="mars-card"><div class="mars-k">{label}</div>
    <div class="mars-v" style="color:{col}">{value}</div>
    <div class="mars-hint">{hint}</div></div>""", unsafe_allow_html=True)

def plotly_chart(fig, height=None):
    fig.update_layout(**PLOT_LAYOUT)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False, "scrollZoom":True})

def normalize_csv(upload, expected):
    if upload is None:
        return None, "Chưa tải file"
    try:
        df = pd.read_csv(upload)
        mapping = {str(c).strip().lower(): c for c in df.columns}
        aliases = {
            "time": ["time","timestamp","date","datetime","gmt time"],
            "open": ["open","o"], "high": ["high","h"],
            "low": ["low","l"], "close": ["close","c","last"],
            "volume": ["volume","vol","tick_volume"],
        }
        found = {}
        for target, names in aliases.items():
            for n in names:
                if n in mapping:
                    found[target] = mapping[n]; break
        required = ["time","open","high","low","close"]
        if any(k not in found for k in required):
            return None, "Thiếu cột bắt buộc: timestamp, open, high, low, close"
        out = pd.DataFrame()
        out["time"] = pd.to_datetime(df[found["time"]], errors="coerce", utc=True)
        for k in ["open","high","low","close"]:
            out[k] = pd.to_numeric(df[found[k]], errors="coerce")
        out["volume"] = pd.to_numeric(df[found["volume"]], errors="coerce") if "volume" in found else np.nan
        out = out.dropna(subset=required).sort_values("time").drop_duplicates("time").reset_index(drop=True)
        if len(out) < 80:
            return out, f"Chỉ có {len(out)} nến — chưa đủ để xác nhận cấu trúc"
        if (out["high"] < out["low"]).any() or (out["high"] < out[["open","close"]].max(axis=1)).any() or (out["low"] > out[["open","close"]].min(axis=1)).any():
            return None, "OHLC không hợp lệ: kiểm tra High/Low"
        return out, f"{len(out):,} nến · {out.time.min():%Y-%m-%d} → {out.time.max():%Y-%m-%d} UTC"
    except Exception as e:
        return None, f"Không đọc được CSV: {e}"

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([(df["high"]-df["low"]), (df["high"]-prev).abs(), (df["low"]-prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def swing_levels(df, window=80):
    d = df.tail(window)
    return float(d["low"].min()), float(d["high"].max())

def analyze_tf(df):
    if df is None or len(df) < 80:
        return {"ready":False, "bias":"NOT VERIFIED"}
    x = df.copy()
    x["ema20"] = ema(x.close,20); x["ema50"] = ema(x.close,50)
    x["atr"] = atr(x)
    last = x.iloc[-1]
    bias = "BULLISH" if last.close > last.ema20 > last.ema50 else ("BEARISH" if last.close < last.ema20 < last.ema50 else "MIXED")
    low, high = swing_levels(x)
    return {"ready":True,"bias":bias,"last":float(last.close),"ema20":float(last.ema20),
            "ema50":float(last.ema50),"atr":float(last.atr) if pd.notna(last.atr) else np.nan,
            "support":low,"resistance":high,"time":last.time}

def candle_fig(df, title):
    x=df.copy()
    x["ema20"]=ema(x.close,20); x["ema50"]=ema(x.close,50)
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=x.time,open=x.open,high=x.high,low=x.low,close=x.close,
        name="OHLC",increasing_line_color=C["green"],decreasing_line_color=C["red"]))
    fig.add_trace(go.Scatter(x=x.time,y=x.ema20,name="EMA 20",line=dict(color=C["gold"],width=1.5)))
    fig.add_trace(go.Scatter(x=x.time,y=x.ema50,name="EMA 50",line=dict(color=C["blue"],width=1.5)))
    fig.update_layout(title=title, height=560, xaxis_rangeslider_visible=False)
    return fig

def daily_history_candles(daily):
    # XAUS daily history may not expose open. Reconstructed open is explicitly labelled.
    x=daily.copy()
    if "o" not in x or x["o"].isna().all():
        x["open_rebuilt"] = x["c"].shift(1).fillna(x["c"])
        x["open_source"] = "Previous close (reconstructed)"
    else:
        x["open_rebuilt"] = x["o"]
        x["open_source"] = "Provider OHLC"
    x["high"] = x["h"] if "h" in x else x["c"]
    x["low"] = x["l"] if "l" in x else x["c"]
    x["close"] = x["c"]
    return x.dropna(subset=["high","low","close"])

# Sidebar / navigation
with st.sidebar:
    st.markdown('<div class="mars-eyebrow">QUANT RESEARCH TERMINAL</div>', unsafe_allow_html=True)
    st.markdown("## 🟡 M.A.R.S. GOLD PRO")
    st.caption("XAU/USD · Decision support")
    page = st.radio("WORKSPACE", ["01  Market Analysis","02  Probability Zones","03  3D Forecast","04  Trade Intelligence","05  Data Health"], label_visibility="collapsed")
    st.divider()
    st.markdown("**DATA CONTROL**")
    auto = st.toggle("Auto refresh · 60 sec", value=True)
    if auto:
        st_autorefresh(interval=60_000, key="mars_refresh")
    if st.button("↻ Refresh data now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Giá tham chiếu XAUS · Không phải giá khớp lệnh broker.")
    st.divider()
    st.caption("M.A.R.S. sequence")
    st.code("Major S/R → H4 bias → reaction → momentum → R:R ≥ 1:2 → sizing", language="text")

# Load public feed
feed_error = None
spot_obj = None; spot_price = None; daily = pd.DataFrame(); intra = []
try:
    spot_obj, spot_price, daily, intra = load_public_data()
except Exception as e:
    feed_error = str(e)

if feed_error:
    data_state = "DATA ERROR"
    price_asof = "Unavailable"
else:
    ds = spot_obj.get("data_state", {}) or {}
    data_state = "STALE" if spot_obj.get("stale") else str(ds.get("status","UNKNOWN")).upper()
    price_asof = spot_obj.get("price_as_of") or ds.get("as_of") or spot_obj.get("updated_at") or "—"

# Upload broker data on sidebar
with st.sidebar:
    st.markdown("**BROKER OHLC IMPORT**")
    st.caption("CSV chuẩn cho H4 / H1 / M15. Giữ cùng một nguồn giá.")
    uploads = {}
    parsed = {}
    statuses = {}
    for tf in ["H4","H1","M15"]:
        uploads[tf] = st.file_uploader(f"{tf} · CSV", type=["csv"], key=f"upload_{tf}")
        parsed[tf], statuses[tf] = normalize_csv(uploads[tf], tf)
    st.caption("Cần dữ liệu broker thật để xác nhận setup. Không tự tạo nến intraday.")

# Header / top strip
st.markdown('<div class="mars-eyebrow">M.A.R.S. · MULTI-TIMEFRAME GOLD INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("Gold Command Center")
st.markdown('<div class="mars-sub">Institutional-style research workspace · XAU/USD · USD per troy ounce</div>', unsafe_allow_html=True)
k1,k2,k3,k4=st.columns(4)
with k1: card("SPOT REFERENCE", fmt_price(spot_price), "XAUS public indicative spot", C["gold"])
with k2: card("FEED STATE", data_state, f"As of {str(price_asof)[:19]}", C["green"] if data_state in ["LIVE","OK","FRESH"] else C["amber"])
with k3: card("DAILY HISTORY", f"{len(daily):,} bars" if len(daily) else "Unavailable", "Provider daily history · not intraday")
with k4:
    ready_count=sum(parsed[t] is not None and len(parsed[t])>=80 for t in ["H4","H1","M15"])
    card("MTF VALIDATION", f"{ready_count}/3 TF", "Broker CSV · H4 / H1 / M15", C["green"] if ready_count==3 else C["amber"])

if feed_error:
    st.error(f"Không kết nối được XAUS public API: {feed_error}. Dashboard không thay bằng giá giả.")
if data_state == "STALE":
    st.warning("Nguồn XAUS đang đánh dấu dữ liệu STALE. Không xem đây là feed LIVE.")

# ---------------- PAGE 1 ----------------
if page.startswith("01"):
    st.markdown("### <span class='mars-section'>01 / MARKET STRUCTURE</span>", unsafe_allow_html=True)
    st.markdown("#### Market Analysis")
    tf_choice=st.segmented_control("TIMEFRAME",["H4","H1","M15","DAILY"],default="H4")
    if tf_choice=="DAILY":
        if len(daily):
            d=daily_history_candles(daily).tail(220)
            fig=go.Figure(go.Candlestick(x=d.date,open=d.open_rebuilt,high=d.high,low=d.low,close=d.close,
                increasing_line_color=C["green"],decreasing_line_color=C["red"],name="XAUS Daily"))
            fig.add_trace(go.Scatter(x=d.date,y=ema(d.close,20),name="EMA20",line=dict(color=C["gold"],width=1.5)))
            fig.add_trace(go.Scatter(x=d.date,y=ema(d.close,50),name="EMA50",line=dict(color=C["blue"],width=1.5)))
            fig.update_layout(title="XAU/USD · Daily provider history",height=560,xaxis_rangeslider_visible=False)
            plotly_chart(fig)
            st.caption("Lưu ý: nếu provider không trả Open, Open được dựng từ previous close. Đây không phải broker execution candle.")
        else: st.info("Daily history chưa khả dụng.")
    elif parsed.get(tf_choice) is not None and len(parsed[tf_choice])>=80:
        df=parsed[tf_choice]
        plotly_chart(candle_fig(df.tail(500),f"Broker OHLC · {tf_choice}"),height=590)
        a=analyze_tf(df)
        a1,a2,a3,a4=st.columns(4)
        with a1: card("DIRECTIONAL BIAS",a["bias"],"EMA20 / EMA50")
        with a2: card("LAST CLOSE",fmt_price(a["last"]),"Uploaded broker feed")
        with a3: card("SUPPORT · 80 BARS",fmt_price(a["support"]),"Rolling low")
        with a4: card("RESISTANCE · 80 BARS",fmt_price(a["resistance"]),"Rolling high")
    else:
        st.info(f"Chưa có dữ liệu OHLC broker hợp lệ cho {tf_choice}. Tải CSV H4/H1/M15 ở sidebar. XAUS chỉ cấp daily history và spot reference trong build này.")
        if len(daily):
            st.markdown("**Daily context (không thay thế H4/H1/M15)**")
            d=daily_history_candles(daily).tail(120)
            fig=go.Figure(go.Candlestick(x=d.date,open=d.open_rebuilt,high=d.high,low=d.low,close=d.close,
                increasing_line_color=C["green"],decreasing_line_color=C["red"]))
            fig.update_layout(title="XAUS daily history · context only",height=420,xaxis_rangeslider_visible=False)
            plotly_chart(fig)
    st.markdown("#### Market structure checklist")
    cols=st.columns(4)
    checks=[("Major S/R","Requires broker OHLC"),("H4 directional bias","Requires H4 CSV"),("H1 reaction","Requires H1 CSV"),("M15 entry structure","Requires M15 CSV")]
    for col,(name,desc) in zip(cols,checks):
        with col: card(name,"PENDING",desc,C["amber"])
    st.markdown('<div class="mars-note">Không hiển thị volume giả cho spot XAU/USD. Nếu dùng volume COMEX futures, phải ghi rõ đó là futures volume, không phải spot volume.</div>',unsafe_allow_html=True)

# ---------------- PAGE 2 ----------------
elif page.startswith("02"):
    st.markdown("### <span class='mars-section'>02 / SCENARIO DISTRIBUTION</span>", unsafe_allow_html=True)
    st.markdown("#### Probability Zones")
    st.caption("Các dải dưới đây là phân vị lịch sử của biến động daily, KHÔNG phải xác suất dự báo đã hiệu chỉnh.")
    if len(daily)>=35 and spot_price:
        close=daily["c"].dropna().astype(float).values
        rets=pd.Series(close).pct_change().dropna()
        horizons={"1D":1,"3D":3,"5D":5,"10D":10}
        rows=[]
        for label,n in horizons.items():
            roll=(1+rets).rolling(n).apply(np.prod,raw=True)-1
            roll=roll.dropna()
            if len(roll)<20: continue
            q10,q25,q50,q75,q90=np.quantile(roll,[.10,.25,.50,.75,.90])
            rows.append({"Horizon":label,"P10":spot_price*(1+q10),"P25":spot_price*(1+q25),
                         "Median":spot_price*(1+q50),"P75":spot_price*(1+q75),"P90":spot_price*(1+q90),
                         "Samples":len(roll)})
        bands=pd.DataFrame(rows)
        if not bands.empty:
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=bands.Horizon,y=bands.P90,mode="lines",line=dict(width=0),showlegend=False))
            fig.add_trace(go.Scatter(x=bands.Horizon,y=bands.P10,mode="lines",fill="tonexty",
                fillcolor="rgba(49,193,142,.13)",line=dict(width=0),name="P10–P90 historical envelope"))
            fig.add_trace(go.Scatter(x=bands.Horizon,y=bands.P75,mode="lines",line=dict(color=C["green"],dash="dot"),name="P75"))
            fig.add_trace(go.Scatter(x=bands.Horizon,y=bands.P50,mode="lines+markers",line=dict(color=C["gold"],width=2),name="Median"))
            fig.add_trace(go.Scatter(x=bands.Horizon,y=bands.P25,mode="lines",line=dict(color=C["red"],dash="dot"),name="P25"))
            fig.add_hline(y=spot_price,line_dash="dash",line_color="#FFFFFF",annotation_text="Spot reference")
            fig.update_layout(title="Historical forward-return quantiles · USD/oz",height=440,yaxis_tickprefix="$")
            plotly_chart(fig)
            display=bands.copy()
            for c in ["P10","P25","Median","P75","P90"]: display[c]=display[c].map(lambda x:f"${x:,.2f}")
            st.dataframe(display,use_container_width=True,hide_index=True)
            st.caption("Phương pháp: rolling compounded daily returns, empirical quantiles. Đây là dải biến động lịch sử; chưa có calibration, walk-forward hoặc xác suất chạm vùng.")
        else: st.warning("Chưa đủ mẫu cho các horizon.")
    else:
        st.info("Cần ít nhất 35 daily bars hợp lệ và spot reference để tính dải lịch sử.")
    st.markdown("#### What is required before publishing true probabilities")
    req=st.columns(3)
    with req[0]: card("DATA","Consistent OHLC","H4 / H1 / M15 + timezone")
    with req[1]: card("MODEL","Walk-forward","Out-of-sample validation")
    with req[2]: card("CALIBRATION","Brier / reliability","Probability quality by horizon")

# ---------------- PAGE 3 ----------------
elif page.startswith("03"):
    st.markdown("### <span class='mars-section'>03 / VOLATILITY LANDSCAPE</span>", unsafe_allow_html=True)
    st.markdown("#### 3D Forecast")
    st.caption("3D surface hiện biểu diễn envelope biến động lịch sử theo horizon và sigma. Chưa phải forecast ML hay calibrated probability surface.")
    if len(daily)>=35 and spot_price:
        close=daily["c"].dropna().astype(float)
        rets=close.pct_change().dropna()
        vol=float(rets.tail(60).std())
        days=np.array([1,2,3,5,7,10,14,21])
        sigmas=np.array([-2,-1.5,-1,-.5,0,.5,1,1.5,2])
        X,Y=np.meshgrid(days,sigmas)
        Z=spot_price*np.exp(Y*vol*np.sqrt(X))
        fig=go.Figure(data=[go.Surface(x=X,y=Y,z=Z,colorscale=[
            [0,"#EF6B7B"],[.25,"#9B637A"],[.5,"#E4B85B"],[.75,"#4E9C91"],[1,"#31C18E"]],
            colorbar=dict(title="USD/oz"),hovertemplate="Horizon: %{x} days<br>σ: %{y:.1f}<br>Price: $%{z:,.2f}<extra></extra>")])
        fig.update_layout(height=650,scene=dict(
            xaxis_title="Forward horizon · days",yaxis_title="Volatility band · σ",
            zaxis_title="Illustrative price · USD/oz",
            bgcolor="rgba(0,0,0,0)",camera=dict(eye=dict(x=1.55,y=1.6,z=1.05))),
            margin=dict(l=0,r=0,t=35,b=0))
        st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False,"scrollZoom":True})
        horizon=st.select_slider("HORIZON",options=["1D","2D","3D","5D","7D","10D","14D","21D"],value="7D")
        n=int(horizon.replace("D",""))
        q10,q50,q90=np.exp(np.array([-1.2816,0,1.2816])*vol*np.sqrt(n))*spot_price
        c1,c2,c3=st.columns(3)
        with c1: card("LOWER ENVELOPE · ~P10",fmt_price(q10),"Normal approximation; not calibrated",C["red"])
        with c2: card("CENTRAL REFERENCE",fmt_price(q50),"Current spot carried forward",C["gold"])
        with c3: card("UPPER ENVELOPE · ~P90",fmt_price(q90),"Normal approximation; not calibrated",C["green"])
        st.markdown('<div class="mars-note">P10/P90 labels above are mathematical normal-approximation quantiles based on recent realized daily volatility, not validated hit probabilities. Treat as scenario envelope only.</div>',unsafe_allow_html=True)
    else:
        st.info("Cần daily history đủ dài để ước lượng realized volatility. Không tạo bề mặt 3D bằng dữ liệu giả.")

# ---------------- PAGE 4 ----------------
elif page.startswith("04"):
    st.markdown("### <span class='mars-section'>04 / DECISION GATES</span>", unsafe_allow_html=True)
    st.markdown("#### Trade Intelligence")
    st.markdown('<div class="mars-note">Trạng thái mặc định là NO TRADE. Chỉ xem xét tín hiệu khi đủ dữ liệu OHLC đồng nhất cho H4/H1/M15; logic này chưa được backtest walk-forward nên không tự phát BUY/SELL.</div>',unsafe_allow_html=True)
    analyses={tf:analyze_tf(parsed.get(tf)) for tf in ["H4","H1","M15"]}
    all_ready=all(analyses[t]["ready"] for t in analyses)
    for tf in ["H4","H1","M15"]:
        a=analyses[tf]
        if a["ready"]:
            st.write(f"**{tf}** · {a['bias']} · Close {fmt_price(a['last'])} · EMA20 {fmt_price(a['ema20'])} · EMA50 {fmt_price(a['ema50'])}")
        else:
            st.write(f"**{tf}** · NOT VERIFIED — cần ít nhất 80 nến CSV hợp lệ.")
    h4=analyses["H4"]; h1=analyses["H1"]; m15=analyses["M15"]
    direction_ok=all_ready and h4["bias"] in ["BULLISH","BEARISH"] and h1["bias"]==h4["bias"] and m15["bias"]==h4["bias"]
    gates=[
        ("01","Major S/R mapping",all_ready,"Needs consistent broker OHLC"),
        ("02","H4 directional bias",h4["ready"],h4.get("bias","Not verified")),
        ("03","H1 reaction & structure",h1["ready"],h1.get("bias","Not verified")),
        ("04","M15 momentum / entry structure",m15["ready"],m15.get("bias","Not verified")),
        ("05","Directional alignment",direction_ok,"H4 / H1 / M15 same EMA regime"),
        ("06","R:R ≥ 1:2 + sizing",False,"Not released — no validated entry/SL model"),
    ]
    for num,name,ok,detail in gates:
        col1,col2=st.columns([2,3])
        with col1: st.write(f"**{num} · {name}**")
        with col2:
            st.markdown(f"<span style='color:{C['green'] if ok else C['amber']};font-weight:800'>{'PASS' if ok else 'BLOCKED'}</span> · <span style='color:{C['muted']}'>{detail}</span>",unsafe_allow_html=True)
    st.divider()
    decision="NO TRADE"
    st.markdown(f"<div class='mars-card'><div class='mars-k'>M.A.R.S. DECISION</div><div class='mars-v' style='color:{C['amber']};font-size:34px'>{decision}</div><div class='mars-hint'>Trade execution remains locked until independent backtest, entry/SL rules and position sizing are validated.</div></div>",unsafe_allow_html=True)
    st.markdown("#### Trade plan")
    p1,p2,p3,p4=st.columns(4)
    with p1: card("ENTRY","—","Not authorized")
    with p2: card("STOP LOSS","—","Structural stop unavailable")
    with p3: card("TAKE PROFIT 1","—","Not calculated")
    with p4: card("TAKE PROFIT 2","—","Not calculated")
    st.caption("Không dùng giá spot XAUS làm giá khớp lệnh. Giá thực thi phải lấy từ broker đang giao dịch.")

# ---------------- PAGE 5 ----------------
else:
    st.markdown("### <span class='mars-section'>05 / SOURCE & PIPELINE MONITOR</span>", unsafe_allow_html=True)
    st.markdown("#### Data Health")
    if feed_error:
        st.error(f"XAUS API: ERROR · {feed_error}")
    else:
        st.success(f"XAUS API reachable · state={data_state}")
    rows=[
        {"Component":"XAUS spot reference","Role":"Indicative spot snapshot","State":"ERROR" if feed_error else data_state,"Coverage":str(price_asof)},
        {"Component":"XAUS daily history","Role":"Daily OHLC context","State":"ERROR" if feed_error or daily.empty else "LOADED","Coverage":f"{len(daily)} bars"},
        {"Component":"XAUS intraday sampled","Role":"Reference line only","State":"ERROR" if feed_error else ("LOADED" if len(intra) else "EMPTY"),"Coverage":f"{len(intra)} points"},
    ]
    for tf in ["H4","H1","M15"]:
        df=parsed.get(tf)
        rows.append({"Component":f"Broker {tf} OHLC","Role":"Structure / trade analysis","State":"LOADED" if df is not None and len(df)>=80 else "NOT LOADED / INVALID","Coverage":statuses.get(tf,"No file")})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.markdown("#### Data quality controls")
    quality=[
        ("Timestamp normalization","UTC parse + sorting + duplicate removal"),
        ("OHLC integrity","High ≥ Open/Close; Low ≤ Open/Close"),
        ("Minimum sample","80 candles for provisional EMA regime; 500+ preferred"),
        ("Feed consistency","H4/H1/M15 must come from the same broker/provider"),
        ("Volume integrity","Spot volume not fabricated; futures volume labelled separately"),
        ("Probability governance","Walk-forward + Brier score + reliability curve required"),
    ]
    for name,desc in quality:
        st.write(f"**{name}** — {desc}")
    st.markdown("#### Data source register")
    st.markdown("- [XAUS public API](https://xaus.com/) — indicative spot and daily/intraday reference data.\n- [Dukascopy historical data](https://www.dukascopy.com/swiss/english/marketwatch/historical/) — candidate source for deep history; not yet connected in this build.\n- Broker OHLC CSV — use the same execution provider for H4/H1/M15.")
    st.markdown('<div class="mars-note">Data Health is intentionally transparent: “not loaded” is not treated as “live”. The app never fills missing OHLC with invented prices and never converts a public spot snapshot into an executable quote.</div>',unsafe_allow_html=True)

st.divider()
st.caption(f"M.A.R.S. GOLD PRO · Streamlit rebuild · Last UI render: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC · Research / decision support only · No auto-trading.")
