"""
Superstore Executive Dashboard — Streamlit
Run : streamlit run superstore_app.py
CSV : merged_superstore.csv  (same folder)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Superstore Dashboard", page_icon="🏪",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
section[data-testid="stMainBlockContainer"]{padding-top:6px!important}
.stApp>header{display:none!important}
.main .block-container{padding:6px 16px 4px!important;max-width:100%!important}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
[data-testid="stSidebar"]{background:#0F1F3D!important;min-width:205px!important;max-width:205px!important}
[data-testid="stSidebar"] *{color:#C8D8F0!important}
[data-testid="stSidebar"] hr{border-color:#2A3F6F!important;margin:5px 0!important}
div[data-testid="stVerticalBlock"]>div{gap:0!important}
div[data-testid="column"]{gap:0!important;padding:0 5px!important}
div[data-testid="stHorizontalBlock"]{gap:0!important;align-items:start!important}
[data-testid="stPlotlyChart"]{margin:0!important;padding:0!important;line-height:0!important}
[data-testid="stPlotlyChart"]>div{margin:0!important;padding:0!important}
/* KPI cards */
.kpi-card{background:#fff;border-radius:10px;padding:11px 15px 9px;
  box-shadow:0 1px 5px rgba(15,31,61,.09);margin-bottom:6px;display:block}
.kpi-lbl{font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  color:#7A8BA8;margin-bottom:2px;line-height:1.2}
.kpi-val{font-size:26px;font-weight:900;color:#0F1F3D;line-height:1.0;letter-spacing:-.5px}
.kpi-sub{font-size:11px;color:#9BAFC8;margin-top:2px}
.kpi-up{color:#16A34A;font-weight:800;font-size:12px}
.kpi-dn{color:#DC2626;font-weight:800;font-size:12px}
/* Chart title */
.cht{font-size:12px;font-weight:700;color:#0F1F3D;letter-spacing:.06em;
  text-transform:uppercase;margin:9px 0 3px;line-height:1.35;display:block}
/* Page title */
.dtitle{font-size:22px;font-weight:900;color:#0F1F3D;margin:0 0 1px;padding:0}
.dsub{font-size:12px;color:#7A8BA8;margin:0 0 5px}
/* Active selection pills */
.sel-pill{display:inline-flex;align-items:center;background:#EEF3FF;color:#1E6FD9;
  border:1px solid #C7D9FF;border-radius:12px;padding:2px 9px;font-size:11px;
  font-weight:600;margin:2px 4px;gap:4px}
/* Widget labels tight */
label[data-testid="stWidgetLabel"]{font-size:10px!important;color:#7A8BA8!important;
  margin-bottom:0!important;padding-bottom:0!important;font-weight:600!important}
div[data-testid="stMarkdownContainer"]>*{margin-bottom:0!important}
div[data-testid="stMarkdownContainer"]{margin-bottom:0!important;padding:0!important}
div[class*="stSelectbox"]{margin-bottom:0!important}
div[data-testid="stRadio"]{margin-bottom:0!important}
div[data-testid="stRadio"]>div{gap:8px!important}
</style>
""", unsafe_allow_html=True)

# ── Palette ──────────────────────────────────────────────────
CN="#0F1F3D"; CB="#1669C1"; CLB="#90BAE8"; CT="#0AA896"
CO="#E87722"; CR="#D32F2F"; CG="#2E7D32"; CGR="#EAEEF5"
CDIM="rgba(155,175,210,0.25)"

REG_C={"West":CN,"East":"#1669C1","Central":"#4A90D9","South":"#7EB8E8"}
CAT_C={"Technology":CN,"Furniture":"#1669C1","Office Supplies":"#4A90D9"}
SEG_C={"Consumer":CN,"Corporate":"#1669C1","Home Office":"#4A90D9"}
RFM_C={"Champions":CN,"Loyal Customers":CT,"High Value":"#5C35C0",
        "At Risk":CO,"Lost Customers":CR,"New Customers":CG,"Regular Customers":"#4A90D9"}
SHIP_C={"Standard Class":CN,"Second Class":"#1669C1","First Class":"#4A90D9","Same Day":CT}
MONTH_NAMES=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CFG={"displayModeBar":False,"scrollZoom":False}

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(base,"merged_superstore.csv"), encoding="latin-1")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"])
    df["Year"]  = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.month
    return df

df = load_data()
YEARS = sorted(df["Year"].unique())
MAX_YEAR = max(YEARS)

# ── Global helpers ────────────────────────────────────────────
def _gr(c, p): return (c-p)/p*100 if p else 0

def _fmt(v, t="Sales"):
    if t in ("Sales","Profit","SALES","PROFIT"):
        if abs(v) >= 1e6: return f"${v/1e6:.2f}M"
        if abs(v) >= 1e3: return f"${v/1e3:.1f}K"
        return f"${v:.0f}"
    return f"{int(v):,}"

def _lo(h, ml=8, mr=8, mt=20, mb=6):
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=h, margin=dict(l=ml,r=mr,t=mt,b=mb),
                font=dict(family="'Inter','Helvetica Neue',sans-serif",size=11,color=CN))

def kpi_card(lbl, val, delta, prev):
    s="▲" if delta>=0 else "▼"; c="kpi-up" if delta>=0 else "kpi-dn"
    return (f'<div class="kpi-card"><div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val">{val}</div>'
            f'<div><span class="{c}">{s}{abs(delta):.1f}%</span>'
            f'<span class="kpi-sub"> vs {prev}</span></div></div>')

def kpi_simple(lbl, val, sub=""):
    return (f'<div class="kpi-card"><div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val">{val}</div>'
            + (f'<div class="kpi-sub">{sub}</div>' if sub else "") + '</div>')

def cht(t):
    st.markdown(f'<div class="cht">{t}</div>', unsafe_allow_html=True)

def hl(names, sel, base, dim=None):
    """Return color list: full for selected (or all if none), dim for others."""
    d = dim or CDIM
    if not sel: return [base]*len(names)
    return [base if str(n)==str(sel) else d for n in names]

def hl_map(names, sel, color_map, dim=None):
    """Per-item color dict with highlight."""
    d = dim or CDIM
    if not sel: return [color_map.get(n,CB) for n in names]
    return [color_map.get(n,CB) if str(n)==str(sel) else d for n in names]

def sparkline(curr, prev, color, h=58):
    x = list(range(1,13))
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=curr, marker_color=[CLB]*11+[color],
        showlegend=False, hovertemplate="Month %{x}: %{y:,.0f}<extra></extra>"))
    if prev:
        fig.add_trace(go.Scatter(x=x, y=prev, mode="lines",
            line=dict(color="#BBC8DE",width=1.5,dash="dot"), showlegend=False,
            hovertemplate="PY %{x}: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=curr, mode="lines+markers",
        line=dict(color=color,width=2.0), marker=dict(size=4,color=color),
        showlegend=False, hovertemplate="Month %{x}: %{y:,.0f}<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=h, margin=dict(l=0,r=0,t=0,b=0),
        xaxis=dict(visible=False,fixedrange=True),
        yaxis=dict(visible=False,fixedrange=True))
    return fig

STATE_COORDS={
    "Alabama":(32.8,-86.8),"Alaska":(64,-153),"Arizona":(34.3,-111.1),
    "Arkansas":(34.8,-92.2),"California":(36.8,-119.4),"Colorado":(39,-105.5),
    "Connecticut":(41.6,-72.7),"Delaware":(38.9,-75.5),"Florida":(27.8,-81.5),
    "Georgia":(32.2,-83.4),"Hawaii":(20.9,-157),"Idaho":(44.4,-114.5),
    "Illinois":(40,-89.2),"Indiana":(40,-86.3),"Iowa":(42,-93.5),
    "Kansas":(38.5,-98),"Kentucky":(37.5,-85),"Louisiana":(31,-91.8),
    "Maine":(45.4,-69.2),"Maryland":(39,-76.8),"Massachusetts":(42.2,-71.5),
    "Michigan":(44,-85.4),"Minnesota":(46.4,-93.1),"Mississippi":(32.7,-89.7),
    "Missouri":(38.5,-92.5),"Montana":(47,-110),"Nebraska":(41.5,-99.9),
    "Nevada":(39.3,-116.6),"New Hampshire":(43.7,-71.6),"New Jersey":(40,-74.3),
    "New Mexico":(34.5,-106),"New York":(42.9,-75.5),"North Carolina":(35.5,-79.8),
    "North Dakota":(47.5,-100.5),"Ohio":(40.4,-82.8),"Oklahoma":(35.5,-97.5),
    "Oregon":(44,-120.5),"Pennsylvania":(40.9,-77.8),"Rhode Island":(41.7,-71.5),
    "South Carolina":(33.9,-81.2),"South Dakota":(44.4,-100.3),"Tennessee":(35.9,-86.7),
    "Texas":(31,-100),"Utah":(39.4,-111.1),"Vermont":(44,-72.7),
    "Virginia":(37.5,-79.5),"Washington":(47.4,-120.6),"West Virginia":(38.6,-80.5),
    "Wisconsin":(44.5,-89.8),"Wyoming":(43,-107.5),"District of Columbia":(38.9,-77),
}

# ── Session state ─────────────────────────────────────────────
ACTS=["sel_month","sel_state","sel_region","sel_segment","sel_subcat","sel_customer","sel_category"]
for k in ACTS:
    if k not in st.session_state: st.session_state[k]=None

def clear_sel():
    for k in ACTS: st.session_state[k]=None

def active_pills():
    m=st.session_state.sel_month; parts=[]
    if m: parts.append(f"Month:{MONTH_NAMES[m-1]}")
    if st.session_state.sel_state:    parts.append(f"State:{st.session_state.sel_state}")
    if st.session_state.sel_region:   parts.append(f"Region:{st.session_state.sel_region}")
    if st.session_state.sel_segment:  parts.append(f"Segment:{st.session_state.sel_segment}")
    if st.session_state.sel_subcat:   parts.append(f"SubCat:{st.session_state.sel_subcat}")
    if st.session_state.sel_customer: parts.append(f"Customer:{st.session_state.sel_customer}")
    if st.session_state.sel_category: parts.append(f"Category:{st.session_state.sel_category}")
    return parts

def render_pills(key):
    pills = active_pills()
    if not pills: return
    pc,bc = st.columns([6,1])
    with pc:
        st.markdown(" ".join(f'<span class="sel-pill">✕ {p}</span>' for p in pills),
                    unsafe_allow_html=True)
    with bc:
        if st.button("Clear", key=f"clr_{key}"):
            clear_sel(); st.rerun()

def toggle(key, val):
    st.session_state[key] = None if st.session_state[key]==val else val


def page_header_with_filters(title, subtitle, metric_key, filter_defs):
    st.markdown(f'<div class="dtitle">{title}</div><div class="dsub">{subtitle}</div>', unsafe_allow_html=True)

    values = {}
    widths = [1.05] * len(filter_defs) + [1.75]
    cols = st.columns(widths)

    for col, fd in zip(cols[:-1], filter_defs):
        with col:
            values[fd["key"]] = st.selectbox(
                fd["label"],
                fd["options"],
                index=fd.get("index", 0),
                key=fd["key"],
            )

    with cols[-1]:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        metric = st.radio(
            "",
            ["Sales", "Profit", "Orders"],
            horizontal=True,
            label_visibility="collapsed",
            key=metric_key,
        )
    return metric, values

# ── Data slice helpers ────────────────────────────────────────
def slice_df(src, f_year="All", f_reg="All", f_seg="All", f_cat="All",
             actions=True):
    d = src.copy()
    if f_year != "All": d = d[d["Year"]==int(f_year)]
    if f_reg  != "All": d = d[d["Region"]==f_reg]
    if f_seg  != "All": d = d[d["Segment"]==f_seg]
    if f_cat  != "All": d = d[d["Category"]==f_cat]
    if actions:
        ss = st.session_state
        if ss.sel_month:    d = d[d["Month"]==ss.sel_month]
        if ss.sel_state:    d = d[d["State"]==ss.sel_state]
        if ss.sel_region:   d = d[d["Region"]==ss.sel_region]
        if ss.sel_segment:  d = d[d["Segment"]==ss.sel_segment]
        if ss.sel_subcat:   d = d[d["Sub-Category"]==ss.sel_subcat]
        if ss.sel_customer: d = d[d["Customer Name"]==ss.sel_customer]
        if ss.sel_category: d = d[d["Category"]==ss.sel_category]
    return d

def get_cy_py(src, f_year, f_reg, f_seg, f_cat):
    """
    Returns (kpi_total, d_cy, d_py, yr, yr_py).
    kpi_total: the period shown in KPI (all years if f_year=All, else specific year).
    d_cy / d_py: current & prior year slices for YoY delta.
    """
    d_all = slice_df(src, "All", f_reg, f_seg, f_cat, actions=True)
    yr    = MAX_YEAR     if f_year=="All" else int(f_year)
    yr_py = MAX_YEAR-1   if f_year=="All" else yr-1
    kpi_total = d_all if f_year=="All" else d_all[d_all["Year"]==yr]
    d_cy = d_all[d_all["Year"]==yr]
    d_py = d_all[d_all["Year"]==yr_py]
    return kpi_total, d_cy, d_py, yr, yr_py

def safe_grp(d, col):
    """groupby col → indexed DataFrame. col stays as the index (standard groupby behavior)."""
    if col not in d.columns or d.empty:
        return pd.DataFrame()
    return d.groupby(col).agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                              Orders=("Order ID","nunique"))

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:4px 0 10px">
      <div style="font-size:20px;font-weight:900;letter-spacing:-1px">
        <span style="color:#5B9FE0">Super</span><span style="color:#fff">Store</span>
      </div>
      <div style="font-size:9px;color:#4A6A9F;letter-spacing:2px;text-transform:uppercase">Analytics</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("", ["Home","Location Analysis","Product Analysis",
                         "Customer Analysis","RFM Analysis","Order Details"], label_visibility="collapsed")
    st.markdown("---")

# ════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════
if page == "Home":

    # Header + filters
    metric, fvals = page_header_with_filters(
        "Superstore Overview Dashboard",
        "Executive Summary | 2014–2017",
        "home_metric_radio",
        [
            {"label": "Year", "options": ["All"] + [str(y) for y in YEARS], "index": len(YEARS), "key": "home_year"},
            {"label": "Region", "options": ["All"] + sorted(df["Region"].unique()), "key": "home_region"},
            {"label": "Segment", "options": ["All"] + sorted(df["Segment"].unique()), "key": "home_segment"},
            {"label": "Category", "options": ["All"] + sorted(df["Category"].unique()), "key": "home_category"},
        ],
    )
    f_year = fvals["home_year"]
    f_reg  = fvals["home_region"]
    f_seg  = fvals["home_segment"]
    f_cat  = fvals["home_category"]
    render_pills("home")

    # Data
    d_kpi, d_cy, d_py, yr, yr_py = get_cy_py(df, f_year, f_reg, f_seg, f_cat)
    ss = st.session_state

    s_tot=d_kpi["Sales"].sum();   s_cy=d_cy["Sales"].sum();   s_py=d_py["Sales"].sum()
    p_tot=d_kpi["Profit"].sum();  p_cy=d_cy["Profit"].sum();  p_py=d_py["Profit"].sum()
    o_tot=d_kpi["Order ID"].nunique(); o_cy=d_cy["Order ID"].nunique(); o_py=d_py["Order ID"].nunique()

    m_cy_s=[d_cy[d_cy["Month"]==m]["Sales"].sum()         for m in range(1,13)]
    m_py_s=[d_py[d_py["Month"]==m]["Sales"].sum()         for m in range(1,13)]
    m_cy_p=[d_cy[d_cy["Month"]==m]["Profit"].sum()        for m in range(1,13)]
    m_py_p=[d_py[d_py["Month"]==m]["Profit"].sum()        for m in range(1,13)]
    m_cy_o=[d_cy[d_cy["Month"]==m]["Order ID"].nunique()  for m in range(1,13)]
    m_py_o=[d_py[d_py["Month"]==m]["Order ID"].nunique()  for m in range(1,13)]

    # ── 3-column layout ──────────────────────────────────────
    left, mid, right = st.columns([1.05, 2.1, 1.75])

    # LEFT — KPI + sparklines (click month → filter)
    with left:
        st.markdown(kpi_card("SALES",   _fmt(s_tot),         _gr(s_cy,s_py),  _fmt(s_py)+" PY"),   unsafe_allow_html=True)
        ev1=st.plotly_chart(sparkline(m_cy_s,m_py_s,CB),use_container_width=True,
            config=CFG,on_select="rerun",key="sp_s")
        if ev1 and ev1.selection and ev1.selection.points:
            m=ev1.selection.points[0].get("x")
            if m and 1<=int(m)<=12: toggle("sel_month",int(m)); st.rerun()

        st.markdown(kpi_card("PROFIT",  _fmt(p_tot,"Profit"), _gr(p_cy,p_py), _fmt(p_py,"Profit")+" PY"), unsafe_allow_html=True)
        ev2=st.plotly_chart(sparkline(m_cy_p,m_py_p,CT),use_container_width=True,
            config=CFG,on_select="rerun",key="sp_p")
        if ev2 and ev2.selection and ev2.selection.points:
            m=ev2.selection.points[0].get("x")
            if m and 1<=int(m)<=12: toggle("sel_month",int(m)); st.rerun()

        st.markdown(kpi_card("# ORDERS",_fmt(o_tot,"Orders"), _gr(o_cy,o_py), _fmt(o_py,"Orders")+" PY"), unsafe_allow_html=True)
        ev3=st.plotly_chart(sparkline(m_cy_o,m_py_o,CN),use_container_width=True,
            config=CFG,on_select="rerun",key="sp_o")
        if ev3 and ev3.selection and ev3.selection.points:
            m=ev3.selection.points[0].get("x")
            if m and 1<=int(m)<=12: toggle("sel_month",int(m)); st.rerun()

    # CENTER — Map + Segment
    with mid:
        # Map uses base filters only (no region action) so map stays complete
        d_map = slice_df(df, f_year, f_reg, f_seg, f_cat, actions=False)
        if ss.sel_month:    d_map = d_map[d_map["Month"]==ss.sel_month]
        if ss.sel_state:    d_map = d_map[d_map["State"]==ss.sel_state]
        if ss.sel_segment:  d_map = d_map[d_map["Segment"]==ss.sel_segment]
        if ss.sel_category: d_map = d_map[d_map["Category"]==ss.sel_category]
        if ss.sel_subcat:   d_map = d_map[d_map["Sub-Category"]==ss.sel_subcat]

        st_d = d_map.groupby("State").agg(
            Sales=("Sales","sum"), Profit=("Profit","sum"),
            Orders=("Order ID","nunique")).reset_index()
        st_d["htxt"] = st_d.apply(lambda r:
            f"<b>{r['State']}</b><br>Sales: {_fmt(r['Sales'])}<br>"
            f"Profit: {_fmt(r['Profit'],'Profit')}<br>Orders: {int(r['Orders'])}", axis=1)

        vc = metric if metric in st_d.columns else "Sales"
        fig_map = go.Figure()
        fig_map.add_trace(go.Choropleth(
            locations=st_d["State"], locationmode="USA-states", z=st_d[vc],
            colorscale=[[0,"#DCE9F8"],[0.5,CB],[1,CN]], showscale=False,
            hovertemplate=st_d["htxt"]+"<extra></extra>",
            marker_line_color="white", marker_line_width=0.6,
            customdata=st_d["State"].tolist()))
        top15 = st_d.nlargest(15, vc)
        lats=[STATE_COORDS.get(s,(0,0))[0] for s in top15["State"]]
        lons=[STATE_COORDS.get(s,(0,0))[1] for s in top15["State"]]
        vv=top15[vc].tolist(); mx=max(vv) if vv else 1
        b_op=[1.0 if (not ss.sel_state or s==ss.sel_state) else 0.15 for s in top15["State"]]
        fig_map.add_trace(go.Scattergeo(
            lat=lats, lon=lons, mode="markers",
            marker=dict(size=[10+20*(v/mx) for v in vv], color=CN,
                        opacity=b_op, line=dict(color="white",width=0.8)),
            hovertext=top15["htxt"].tolist(),
            hovertemplate="%{hovertext}<extra></extra>",
            customdata=top15["State"].tolist(), showlegend=False))
        fig_map.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=285, margin=dict(l=0,r=0,t=18,b=0),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", showland=True,
                     landcolor="#F0F4FA", showlakes=False, showframe=False,
                     coastlinecolor="#C5D5E8", projection_type="albers usa"))
        cht(f"{metric} | By State  — click to highlight")
        ev_map=st.plotly_chart(fig_map,use_container_width=True,config=CFG,
                               on_select="rerun",key="map_home")
        if ev_map and ev_map.selection and ev_map.selection.points:
            pt=ev_map.selection.points[0]
            sc=pt.get("customdata") or pt.get("location")
            if sc and isinstance(sc,str): toggle("sel_state",sc); st.rerun()

        # Segment bars — always 3 bars; highlight clicked
        seg_cy = safe_grp(d_cy,"Segment").reindex(["Consumer","Corporate","Home Office"])
        seg_py = safe_grp(d_py,"Segment")   # index = Segment (no set_index needed)

        fig_seg = go.Figure()
        segs_ord = ["Consumer","Corporate","Home Office"]
        seg_colors = [CN,"#1669C1","#4A90D9"]
        for i, seg in enumerate(segs_ord):
            vc2 = float(seg_cy.loc[seg,metric]) if (not seg_cy.empty and seg in seg_cy.index) else 0.0
            vp  = float(seg_py.loc[seg,metric]) if (not seg_py.empty and seg in seg_py.index) else 0.0
            gr  = _gr(vc2,vp)
            bc  = seg_colors[i]
            bar_c = bc if (not ss.sel_segment or ss.sel_segment==seg) else CDIM
            fig_seg.add_trace(go.Bar(
                x=[seg], y=[vc2], marker_color=bar_c, width=0.55,
                showlegend=False,
                text=[f"<b>{_fmt(vc2,metric)}</b>"], textposition="outside",
                textfont=dict(size=11,color=CN,family="Inter"),
                customdata=[seg],
                hovertemplate=f"<b>{seg}</b><br>{metric}: %{{y:,.0f}}<br>YoY: {gr:+.1f}%<extra></extra>"))
            if vp > 0:
                fig_seg.add_shape(type="line",x0=i-0.28,x1=i+0.28,y0=vp,y1=vp,
                    line=dict(color="#555",width=1.5,dash="dot"),xref="x",yref="y")
            if vc2 > 0:
                sign="▲" if gr>=0 else "▼"; gcol=CG if gr>=0 else CR
                fig_seg.add_annotation(x=seg, y=vc2*0.5,
                    text=f"<b>{sign}{abs(gr):.1f}%</b>",
                    showarrow=False,font=dict(size=11,color="white"))
        max_seg = max([float(seg_cy.loc[s,metric]) if (not seg_cy.empty and s in seg_cy.index) else 0 for s in segs_ord], default=1)
        fig_seg.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=205, margin=dict(l=4,r=4,t=28,b=4),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=12)),
            yaxis=dict(visible=False,range=[0,max_seg*1.28]),
            bargap=0.3, showlegend=False)
        cht(f"{metric} | By Segment  — click to highlight")
        ev_seg=st.plotly_chart(fig_seg,use_container_width=True,config=CFG,
                               on_select="rerun",key="seg_home")
        if ev_seg and ev_seg.selection and ev_seg.selection.points:
            cd=ev_seg.selection.points[0].get("customdata")
            if cd: toggle("sel_segment",cd); st.rerun()

    # RIGHT — Region + Sub-Category
    with right:
        # Region bars
        reg_cy = safe_grp(d_cy,"Region")
        reg_py = safe_grp(d_py,"Region")
        regs = reg_cy.index.tolist() if not reg_cy.empty else []
        regs_sorted = sorted(regs, key=lambda r: float(reg_cy.loc[r,metric]) if r in reg_cy.index else 0, reverse=True)

        fig_reg = go.Figure()
        for i,reg in enumerate(regs_sorted):
            vc2=float(reg_cy.loc[reg,metric]) if reg in reg_cy.index else 0
            vp =float(reg_py.loc[reg,metric]) if (not reg_py.empty and reg in reg_py.index) else 0
            gr=_gr(vc2,vp); sign="▲" if gr>=0 else "▼"
            bc=REG_C.get(reg,CB)
            bar_c = bc if (not ss.sel_region or ss.sel_region==reg) else CDIM
            fig_reg.add_trace(go.Bar(
                x=[reg], y=[vc2], marker_color=bar_c, width=0.55, showlegend=False,
                text=[f"<b>{_fmt(vc2,metric)}</b>"], textposition="outside",
                textfont=dict(size=11,color=CN,family="Inter"),
                customdata=[reg],
                hovertemplate=f"<b>{reg}</b><br>{metric}: %{{y:,.0f}}<br>YoY: {gr:+.1f}%<extra></extra>"))
            if vp > 0:
                fig_reg.add_shape(type="line",x0=i-0.28,x1=i+0.28,y0=vp,y1=vp,
                    line=dict(color="#555",width=1.5,dash="dot"),xref="x",yref="y")
            if vc2 > 0:
                gcol=CG if gr>=0 else CR
                fig_reg.add_annotation(x=reg, y=vc2*0.5,
                    text=f"<b>{sign}{abs(gr):.1f}%</b>",
                    showarrow=False,font=dict(size=11,color="white"))
        max_reg = max([float(reg_cy.loc[r,metric]) if r in reg_cy.index else 0 for r in regs_sorted], default=1)
        fig_reg.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=235, margin=dict(l=4,r=8,t=28,b=4),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=12)),
            yaxis=dict(visible=False,range=[0,max_reg*1.28]),
            bargap=0.28, showlegend=False)
        cht(f"{metric} | By Region  — click to highlight")
        ev_reg=st.plotly_chart(fig_reg,use_container_width=True,config=CFG,
                               on_select="rerun",key="reg_home")
        if ev_reg and ev_reg.selection and ev_reg.selection.points:
            cd=ev_reg.selection.points[0].get("customdata")
            if cd: toggle("sel_region",cd); st.rerun()

        # Sub-Category top 10 horizontal
        sc_cy = d_cy.groupby("Sub-Category").agg(
            Sales=("Sales","sum"), Profit=("Profit","sum"),
            Orders=("Order ID","nunique")).reset_index()
        sc_py = d_py.groupby("Sub-Category").agg(
            Sales=("Sales","sum"), Profit=("Profit","sum"),
            Orders=("Order ID","nunique"))  # index = Sub-Category

        top10 = sc_cy.nlargest(10,metric).sort_values(metric)
        names = top10["Sub-Category"].tolist()
        vals  = top10[metric].tolist()
        mx    = max(vals) if vals else 1
        bar_cols = hl(names, ss.sel_subcat, CB)

        fig_sc = go.Figure()
        # Track bar
        fig_sc.add_trace(go.Bar(x=[mx*1.25]*len(top10), y=names, orientation="h",
            marker_color="#EDF2FA", width=0.72, showlegend=False, hoverinfo="skip"))
        # Main bar
        fig_sc.add_trace(go.Bar(x=vals, y=names, orientation="h",
            marker_color=bar_cols, width=0.72, showlegend=False,
            text=[f"<b>{_fmt(v,metric)}</b>" for v in vals],
            textposition="outside", textfont=dict(size=11,color=CN,family="Inter"),
            customdata=names,
            hovertemplate="<b>%{y}</b><br>"+metric+": %{x:,.0f}<extra></extra>"))
        # YoY annotations
        for _,row in top10.iterrows():
            sc=row["Sub-Category"]; vc2=row[metric]
            vp=float(sc_py.loc[sc,metric]) if (not sc_py.empty and sc in sc_py.index) else 0
            gr=_gr(vc2,vp); gcol=CG if gr>=0 else CR
            fig_sc.add_annotation(x=mx*1.23, y=sc,
                text=f"<b>{'▲' if gr>=0 else '▼'}{abs(gr):.1f}%</b>",
                showarrow=False, xanchor="right", font=dict(size=11,color=gcol))
        fig_sc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=305, margin=dict(l=4,r=8,t=28,b=4),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            barmode="overlay",
            xaxis=dict(visible=False, range=[0,mx*1.35]),
            yaxis=dict(showgrid=False, tickfont=dict(size=12), autorange="reversed"),
            bargap=0.22)
        cht(f"{metric} | Top 10 Sub-Category  — click to highlight")
        ev_sc=st.plotly_chart(fig_sc,use_container_width=True,config=CFG,
                              on_select="rerun",key="sc_home")
        if ev_sc and ev_sc.selection and ev_sc.selection.points:
            for pt in ev_sc.selection.points:
                cd=pt.get("customdata")
                if cd and isinstance(cd,str): toggle("sel_subcat",cd); st.rerun()

# ════════════════════════════════════════════════════════════
# LOCATION ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "Location Analysis":
    metric, fvals = page_header_with_filters(
        "Location Analysis",
        "Regional performance and geographic distribution",
        "loc_metric_radio",
        [
            {"label": "Year", "options": ["All"] + [str(y) for y in YEARS], "index": len(YEARS), "key": "loc_year"},
            {"label": "Region", "options": ["All"] + sorted(df["Region"].unique()), "key": "loc_region"},
            {"label": "Segment", "options": ["All"] + sorted(df["Segment"].unique()), "key": "loc_segment"},
            {"label": "Category", "options": ["All"] + sorted(df["Category"].unique()), "key": "loc_category"},
        ],
    )
    f_year = fvals["loc_year"]
    f_reg  = fvals["loc_region"]
    f_seg  = fvals["loc_segment"]
    f_cat  = fvals["loc_category"]
    render_pills("loc")

    d_kpi,d_cy,d_py,yr,yr_py = get_cy_py(df,f_year,f_reg,f_seg,f_cat)
    d = slice_df(df,f_year,f_reg,f_seg,f_cat)

    k1,k2,k3,k4 = st.columns(4)
    pairs=[("SALES",d_kpi["Sales"].sum(),d_py["Sales"].sum(),"Sales"),
           ("PROFIT",d_kpi["Profit"].sum(),d_py["Profit"].sum(),"Profit"),
           ("ORDERS",d_kpi["Order ID"].nunique(),d_py["Order ID"].nunique(),"Orders"),
           ("CUSTOMERS",d_kpi["Customer ID"].nunique(),d_py["Customer ID"].nunique(),"Orders")]
    for col,(lbl,vc,vp,fmt) in zip([k1,k2,k3,k4],pairs):
        col.markdown(kpi_card(lbl,_fmt(vc,fmt),_gr(vc,vp),_fmt(vp,fmt)),unsafe_allow_html=True)

    m1,m2 = st.columns([3,2])
    st_d = d.groupby("State").agg(Sales=("Sales","sum"),Profit=("Profit","sum"),
                                   Orders=("Order ID","nunique")).reset_index()
    with m1:
        fig_ch = px.choropleth(st_d,locations="State",locationmode="USA-states",
            color=metric,hover_name="State",
            hover_data={"Sales":":.0f","Profit":":.0f","Orders":True},
            color_continuous_scale=[[0,CR],[0.35,"#F5F5F5"],[1,CT]],scope="usa")
        fig_ch.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=300,
            margin=dict(l=0,r=0,t=20,b=0),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            coloraxis_showscale=False,
            geo=dict(bgcolor="rgba(0,0,0,0)",showland=True,landcolor="#F0F4FA",
                     showframe=False,coastlinecolor="#C5D5E8"))
        cht(f"{metric} by State  — click state")
        ev_ch=st.plotly_chart(fig_ch,use_container_width=True,config=CFG,
                              on_select="rerun",key="loc_choro")
        if ev_ch and ev_ch.selection and ev_ch.selection.points:
            sc=ev_ch.selection.points[0].get("location")
            if sc: toggle("sel_state",sc); st.rerun()

    with m2:
        top10s = st_d.nlargest(10,metric).sort_values(metric)
        ss = st.session_state
        bar_c_s = hl(top10s["State"].tolist(), ss.sel_state, CB)
        bar_c_p = [(CR if p<0 else CT) if (not ss.sel_state or s==ss.sel_state)
                   else CDIM for s,p in zip(top10s["State"],top10s["Profit"])]
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Bar(x=top10s[metric],y=top10s["State"],orientation="h",
            marker_color=bar_c_s,showlegend=False,
            text=top10s[metric].apply(lambda x:f"<b>{_fmt(x, metric)}</b>"),
            textposition="outside",textfont=dict(size=12,color=CN),
            customdata=top10s["State"].tolist(),
            hovertemplate="<b>%{y}</b><br>"+metric+": %{x:,.0f}<extra></extra>"))
        mx_s=max(float(top10s[metric].max()), 1)
        fig_ts.update_layout(**_lo(288,mr=70),
            xaxis=dict(visible=False,range=[0,mx_s*1.35]),
            yaxis=dict(autorange="reversed",tickfont=dict(size=12)))
        cht(f"Top 10 States | {metric}  — click state")
        ev_ts=st.plotly_chart(fig_ts,use_container_width=True,config=CFG,
                              on_select="rerun",key="loc_state")
        if ev_ts and ev_ts.selection and ev_ts.selection.points:
            cd=ev_ts.selection.points[0].get("customdata")
            if cd: toggle("sel_state",cd); st.rerun()

    r1,r2 = st.columns(2)
    reg_d = d.groupby("Region").agg(Sales=("Sales","sum"),Profit=("Profit","sum"),
                                     Orders=("Order ID","nunique")).reset_index()
    reg_d["Margin"] = (reg_d["Profit"]/reg_d["Sales"]*100).fillna(0)
    with r1:
        fig_rm = make_subplots(specs=[[{"secondary_y":True}]])
        reg_sorted = reg_d.sort_values(metric,ascending=False)
        for i,row in reg_sorted.reset_index(drop=True).iterrows():
            fig_rm.add_trace(go.Bar(x=[row["Region"]],y=[row[metric]],
                marker_color=REG_C.get(row["Region"],CB),width=0.52,showlegend=False,
                text=[f"<b>{_fmt(row[metric], metric)}</b>"],textposition="outside",
                textfont=dict(size=12,color=CN),customdata=[row["Region"]]),secondary_y=False)
        fig_rm.add_trace(go.Scatter(
            x=reg_sorted["Region"],y=reg_sorted["Margin"],
            mode="lines+markers+text",
            line=dict(color=CO,width=2.5),marker=dict(size=9,color=CO,
                line=dict(color="white",width=1.5)),
            text=[f"<b>{m:.0f}%</b>" for m in reg_sorted["Margin"]],
            textposition="top center",textfont=dict(size=11,color=CO),
            showlegend=False,name="Margin%"),secondary_y=True)
        mx_r=max(float(reg_sorted[metric].max()), 1)
        fig_rm.update_layout(**_lo(225))
        fig_rm.update_yaxes(visible=False,secondary_y=False,range=[0,mx_r*1.3])
        fig_rm.update_yaxes(visible=False,secondary_y=True,range=[0,reg_sorted["Margin"].max()*1.8])
        fig_rm.update_xaxes(showgrid=False,tickfont=dict(size=12))
        cht(f"Region: {metric} + Margin %")
        ev_rm=st.plotly_chart(fig_rm,use_container_width=True,config=CFG,
                              on_select="rerun",key="loc_reg")
        if ev_rm and ev_rm.selection and ev_rm.selection.points:
            cd=ev_rm.selection.points[0].get("customdata")
            if cd: toggle("sel_region",cd); st.rerun()
    with r2:
        city_d = d.groupby(["City","Region"]).agg(
            Sales=("Sales","sum"),Profit=("Profit","sum"),Orders=("Order ID","nunique")).reset_index().nlargest(12,metric).sort_values(metric)
        fig_ct = px.bar(city_d,x=metric,y="City",orientation="h",color="Region",
            color_discrete_map=REG_C,
            text=city_d[metric].apply(lambda x:f"<b>{_fmt(x, metric)}</b>"))
        fig_ct.update_traces(textposition="outside",textfont_size=12)
        mx_c=max(float(city_d[metric].max()), 1)
        fig_ct.update_layout(**_lo(225,mr=70),showlegend=False,
            xaxis=dict(visible=False,range=[0,mx_c*1.35]),
            yaxis=dict(tickfont=dict(size=12)))
        cht(f"Top 12 Cities by {metric}")
        st.plotly_chart(fig_ct,use_container_width=True,config=CFG)

# ════════════════════════════════════════════════════════════
# PRODUCT ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "Product Analysis":
    metric, fvals = page_header_with_filters(
        "Product Analysis",
        "Category, sub-category, and discount performance",
        "prod_metric_radio",
        [
            {"label": "Year", "options": ["All"] + [str(y) for y in YEARS], "index": len(YEARS), "key": "prod_year"},
            {"label": "Region", "options": ["All"] + sorted(df["Region"].unique()), "key": "prod_region"},
            {"label": "Segment", "options": ["All"] + sorted(df["Segment"].unique()), "key": "prod_segment"},
        ],
    )
    f_year = fvals["prod_year"]
    f_reg  = fvals["prod_region"]
    f_seg  = fvals["prod_segment"]
    render_pills("prod")

    d_kpi,d_cy,d_py,yr,yr_py = get_cy_py(df,f_year,f_reg,f_seg,"All")
    ss = st.session_state

    mg_k = d_kpi["Profit"].sum()/d_kpi["Sales"].sum()*100 if d_kpi["Sales"].sum() else 0
    mg_cy= d_cy["Profit"].sum()/d_cy["Sales"].sum()*100 if d_cy["Sales"].sum() else 0
    mg_py= d_py["Profit"].sum()/d_py["Sales"].sum()*100 if d_py["Sales"].sum() else 0
    loss = (d_cy["Profit"]<0).mean()*100

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi_card("SALES",  _fmt(d_kpi["Sales"].sum()),
        _gr(d_cy["Sales"].sum(),d_py["Sales"].sum()), "PY"),unsafe_allow_html=True)
    k2.markdown(kpi_card("PROFIT", _fmt(d_kpi["Profit"].sum(),"Profit"),
        _gr(d_cy["Profit"].sum(),d_py["Profit"].sum()), "PY"),unsafe_allow_html=True)
    k3.markdown(kpi_card("MARGIN", f"{mg_k:.1f}%", mg_cy-mg_py, f"{mg_py:.1f}% PY"),unsafe_allow_html=True)
    k4.markdown(kpi_simple("LOSS-MAKING LINES",f"{loss:.1f}%","of line items"),unsafe_allow_html=True)

    p1,p2 = st.columns([1,1])

    with p1:
        # Category bar + margin line (dual axis)
        cat_d = d_cy.groupby("Category").agg(
            Sales=("Sales","sum"),Profit=("Profit","sum"),Orders=("Order ID","nunique")).reset_index()
        cat_d["Margin"] = (cat_d["Profit"]/cat_d["Sales"]*100).fillna(0)
        # Reorder
        cat_ord = ["Technology","Furniture","Office Supplies"]
        cat_d = cat_d.set_index("Category").reindex(cat_ord).reset_index()

        fig_cat = make_subplots(specs=[[{"secondary_y":True}]])
        for i,row in cat_d.iterrows():
            bc = list(CAT_C.values())[i]
            bar_c = bc if (not ss.sel_category or ss.sel_category==row["Category"]) else CDIM
            fig_cat.add_trace(go.Bar(x=[row["Category"]],y=[row[metric]],
                marker_color=bar_c, width=0.52, showlegend=False,
                text=[f"<b>{_fmt(row[metric], metric)}</b>"],
                textposition="outside", textfont=dict(size=12,color=CN,family="Inter"),
                customdata=[row["Category"]]),secondary_y=False)
        # Margin line — bright orange, large markers, clear separation from bars
        fig_cat.add_trace(go.Scatter(
            x=cat_d["Category"], y=cat_d["Margin"],
            mode="lines+markers+text",
            line=dict(color=CO,width=3),
            marker=dict(size=10,color="white",line=dict(color=CO,width=3)),
            text=[f"<b>{m:.1f}%</b>" for m in cat_d["Margin"]],
            textposition="top center", textfont=dict(size=11,color=CO,family="Inter"),
            showlegend=False,name="Margin%"),secondary_y=True)
        mx_cat=max(float(cat_d[metric].max()), 1)
        fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            height=278,margin=dict(l=10,r=10,t=38,b=10),
            font=dict(family="'Inter',sans-serif",size=11,color=CN))
        fig_cat.update_yaxes(visible=False,secondary_y=False,range=[0,mx_cat*1.32])
        fig_cat.update_yaxes(visible=False,secondary_y=True,
                             range=[0,cat_d["Margin"].max()*2.2])
        fig_cat.update_xaxes(showgrid=False,tickfont=dict(size=12))
        cht(f"Category: {metric} + Margin %  — click to highlight")
        ev_cat=st.plotly_chart(fig_cat,use_container_width=True,config=CFG,
                               on_select="rerun",key="prod_cat")
        if ev_cat and ev_cat.selection and ev_cat.selection.points:
            cd=ev_cat.selection.points[0].get("customdata")
            if cd: toggle("sel_category",cd); st.rerun()

    with p2:
        # Sub-category profit — horizontal bar, all 17 items
        sc_d = d_cy.groupby("Sub-Category").agg(
            Sales=("Sales","sum"),Profit=("Profit","sum"),Orders=("Order ID","nunique")).reset_index().sort_values(metric)
        mx_abs = max(sc_d[metric].abs().max(), 1) if len(sc_d) else 1
        bar_c = [(CDIM if (ss.sel_subcat and s!=ss.sel_subcat)
                  else (CR if (metric=="Profit" and p<0) else CT))
                 for s,p in zip(sc_d["Sub-Category"],sc_d["Profit"])]
        fig_sc2 = go.Figure(go.Bar(
            y=sc_d["Sub-Category"], x=sc_d[metric], orientation="h",
            marker_color=bar_c,
            text=[f"<b>{_fmt(v, metric)}</b>" for v in sc_d[metric]],
            textposition="outside", textfont=dict(size=10.5,color=CN,family="Inter"),
            customdata=sc_d["Sub-Category"].tolist(),
            hovertemplate="<b>%{y}</b><br>"+metric+": %{x:,.0f}<extra></extra>"))
        if metric == "Profit":
            fig_sc2.add_vline(x=0,line_color="#888",line_width=1)
        fig_sc2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=278, margin=dict(l=8,r=80,t=38,b=8),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            xaxis=dict(visible=False, range=[-mx_abs*1.05, mx_abs*1.55]),
            yaxis=dict(showgrid=False, tickfont=dict(size=12), autorange="reversed"))
        cht(f"{metric} by Sub-Category  — click to highlight")
        ev_sc2=st.plotly_chart(fig_sc2,use_container_width=True,config=CFG,
                               on_select="rerun",key="prod_sc2")
        if ev_sc2 and ev_sc2.selection and ev_sc2.selection.points:
            cd=ev_sc2.selection.points[0].get("customdata")
            if cd: toggle("sel_subcat",cd); st.rerun()

    p3,p4 = st.columns([1,1])
    with p3:
        d_band = d_cy.copy()
        bins=[0,0.001,0.2,0.4,0.6,1.0]; labels=["0%","1–20%","20–40%","40–60%",">60%"]
        d_band["Band"]=pd.cut(d_band["Discount"],bins=bins,labels=labels,include_lowest=True)
        band_d=d_band.groupby("Band",observed=False).agg(AvgProfit=("Profit","mean")).reset_index()
        band_d["Band"]=band_d["Band"].astype(str)
        ymin=band_d["AvgProfit"].min(); ymax=band_d["AvgProfit"].max()
        fig_disc=go.Figure(go.Bar(
            x=band_d["Band"],y=band_d["AvgProfit"],width=0.58,
            marker_color=[CT if v>0 else CR for v in band_d["AvgProfit"]],
            text=[f"<b>${v:.0f}</b>" for v in band_d["AvgProfit"]],
            textposition="outside",textfont=dict(size=11,color=CN,family="Inter")))
        fig_disc.add_hline(y=0,line_color="#999",line_width=0.8)
        fig_disc.add_vline(x=1.5,line_dash="dash",line_color=CO,opacity=0.75,
            annotation_text="Cap 20%",annotation_position="top right",
            annotation_font=dict(size=11,color=CO))
        fig_disc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            height=258,margin=dict(l=10,r=10,t=38,b=10),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            xaxis=dict(showgrid=False,tickfont=dict(size=12)),
            yaxis=dict(visible=False,range=[ymin*1.4,ymax*1.5]))
        cht("Avg Profit / Line by Discount Band")
        st.plotly_chart(fig_disc,use_container_width=True,config=CFG)

    with p4:
        samp=d_cy.sample(min(len(d_cy),2000),random_state=42)
        fig_dsc=px.scatter(samp,x="Discount",y="Profit",color="Category",
            color_discrete_map=CAT_C,opacity=0.55,size_max=5,
            labels={"Discount":"Discount","Profit":"Profit ($)"})
        fig_dsc.add_hline(y=0,line_dash="dash",line_color=CR,opacity=0.5)
        fig_dsc.add_vline(x=0.2,line_dash="dash",line_color=CO,opacity=0.5,
            annotation_text="20%",annotation_position="top right",
            annotation_font=dict(size=11,color=CO))
        fig_dsc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            height=258,margin=dict(l=10,r=10,t=38,b=10),
            font=dict(family="'Inter',sans-serif",size=11,color=CN),
            legend=dict(orientation="h",y=1.12,font_size=9,x=0,bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(showgrid=True,gridcolor=CGR,tickformat=".0%",tickfont=dict(size=12)),
            yaxis=dict(showgrid=True,gridcolor=CGR,title=""))
        cht("Discount vs Profit — Scatter")
        st.plotly_chart(fig_dsc,use_container_width=True,config=CFG)

    # Correlation heatmap
    corr=d_cy[["Discount","Sales","Profit","Quantity"]].corr().round(2)
    fig_corr=go.Figure(go.Heatmap(
        z=corr.values,x=corr.columns.tolist(),y=corr.index.tolist(),
        colorscale=[[0,CR],[0.5,"#F5F5F5"],[1,CN]],zmin=-1,zmax=1,
        text=corr.values,texttemplate="<b>%{text:.2f}</b>",textfont_size=13,
        showscale=True,colorbar=dict(thickness=10,len=0.85)))
    fig_corr.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        height=205,margin=dict(l=10,r=20,t=28,b=6),
        font=dict(family="'Inter',sans-serif",size=11,color=CN),
        xaxis=dict(side="bottom",tickfont=dict(size=12)),
        yaxis=dict(autorange="reversed",tickfont=dict(size=12)))
    cht("Correlation — Discount · Sales · Profit · Quantity")
    st.plotly_chart(fig_corr,use_container_width=True,config=CFG)

# ════════════════════════════════════════════════════════════
# CUSTOMER ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "Customer Analysis":

    st.markdown("""
    <style>
    .cus-panel{
        background:#fff;
        border-radius:16px;
        padding:14px 16px 10px;
        box-shadow:0 1px 6px rgba(15,31,61,.08);
        margin-bottom:14px;
    }
    .cus-small-title{
        font-size:13px;
        font-weight:800;
        color:#0F1F3D;
        margin-bottom:8px;
    }
    .cus-blue{color:#0288D1;font-weight:800;}
    .cus-sub{font-size:11px;color:#7A8BA8;}
    .seg-name{font-size:13px;color:#0F1F3D;font-weight:700;min-width:86px;display:inline-block;}
    .seg-yoy{font-size:12px;font-weight:900;display:inline-block;min-width:72px;}
    .legend-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;}
    </style>
    """, unsafe_allow_html=True)

    # Header + filters
    metric, fvals = page_header_with_filters(
        "Superstore Overview Dashboard",
        f"Customer Analysis | {min(YEARS)}–{max(YEARS)}",
        "cus_metric_radio",
        [
            {"label": "Year", "options": ["All"] + [str(y) for y in YEARS], "index": len(YEARS), "key": "cus_year"},
            {"label": "Region", "options": ["All"] + sorted(df["Region"].unique()), "key": "cus_region"},
            {"label": "Segment", "options": ["All"] + sorted(df["Segment"].unique()), "key": "cus_segment"},
        ],
    )
    f_year = fvals["cus_year"]
    f_reg  = fvals["cus_region"]
    f_seg  = fvals["cus_segment"]
    render_pills("cus_new")

    # Data preparation
    d_kpi, d_cy, d_py, yr, yr_py = get_cy_py(df, f_year, f_reg, f_seg, "All")
    ss = st.session_state

    s_tot = d_kpi["Sales"].sum(); s_cy = d_cy["Sales"].sum(); s_py = d_py["Sales"].sum()
    p_tot = d_kpi["Profit"].sum(); p_cy = d_cy["Profit"].sum(); p_py = d_py["Profit"].sum()
    o_tot = d_kpi["Order ID"].nunique(); o_cy = d_cy["Order ID"].nunique(); o_py = d_py["Order ID"].nunique()
    c_tot = d_kpi["Customer ID"].nunique(); c_cy = d_cy["Customer ID"].nunique(); c_py = d_py["Customer ID"].nunique()

    m_cy_s = [d_cy[d_cy["Month"] == m]["Sales"].sum() for m in range(1, 13)]
    m_py_s = [d_py[d_py["Month"] == m]["Sales"].sum() for m in range(1, 13)]
    m_cy_p = [d_cy[d_cy["Month"] == m]["Profit"].sum() for m in range(1, 13)]
    m_py_p = [d_py[d_py["Month"] == m]["Profit"].sum() for m in range(1, 13)]
    m_cy_o = [d_cy[d_cy["Month"] == m]["Order ID"].nunique() for m in range(1, 13)]
    m_py_o = [d_py[d_py["Month"] == m]["Order ID"].nunique() for m in range(1, 13)]
    m_cy_c = [d_cy[d_cy["Month"] == m]["Customer ID"].nunique() for m in range(1, 13)]
    m_py_c = [d_py[d_py["Month"] == m]["Customer ID"].nunique() for m in range(1, 13)]

    def customer_kpi_card(label, value, py_value, growth, curr, prev, color):
        sign = "▲" if growth >= 0 else "▼"
        g_color = "#16A34A" if growth >= 0 else "#DC2626"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-lbl">{label}</div>
                <div class="kpi-val">{value}</div>
                <div class="kpi-sub">{py_value} PY</div>
                <div style="text-align:right;margin-top:-38px">
                    <span style="color:{g_color};font-size:12px;font-weight:800">
                        {sign} {abs(growth):.1f}%
                    </span>
                    <div class="kpi-sub">vs {yr_py}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        ev = st.plotly_chart(sparkline(curr, prev, color, h=62), use_container_width=True,
                             config=CFG, on_select="rerun", key=f"cus_kpi_{label}")
        if ev and ev.selection and ev.selection.points:
            m = ev.selection.points[0].get("x")
            if m and 1 <= int(m) <= 12:
                toggle("sel_month", int(m)); st.rerun()

    left, right = st.columns([1.0, 2.25])

    with left:
        customer_kpi_card("SALES", _fmt(s_tot, "Sales"), _fmt(s_py, "Sales"),
                          _gr(s_cy, s_py), m_cy_s, m_py_s, CB)
        customer_kpi_card("PROFIT", _fmt(p_tot, "Profit"), _fmt(p_py, "Profit"),
                          _gr(p_cy, p_py), m_cy_p, m_py_p, CB)
        customer_kpi_card("# ORDERS", _fmt(o_tot, "Orders"), _fmt(o_py, "Orders"),
                          _gr(o_cy, o_py), m_cy_o, m_py_o, CB)
        customer_kpi_card("# CUSTOMERS", _fmt(c_tot, "Orders"), _fmt(c_py, "Orders"),
                          _gr(c_cy, c_py), m_cy_c, m_py_c, CB)

    with right:
        # 1. By customer segment
        st.markdown('<div class="cus-panel">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="cus-small-title">{metric} | <span class="cus-blue">By Customer Segment</span></div>',
            unsafe_allow_html=True
        )

        seg_order = ["Consumer", "Corporate", "Home Office"]
        seg_cy = d_cy.groupby("Segment").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                                             Orders=("Order ID", "nunique")).reindex(seg_order).fillna(0)
        seg_py = d_py.groupby("Segment").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                                             Orders=("Order ID", "nunique")).reindex(seg_order).fillna(0)
        total_metric = seg_cy[metric].sum() if len(seg_cy) else 0
        max_metric = seg_cy[metric].max() if len(seg_cy) else 1
        max_metric = max(max_metric, 1)

        for seg in seg_order:
            val = seg_cy.loc[seg, metric] if seg in seg_cy.index else 0
            py_val = seg_py.loc[seg, metric] if seg in seg_py.index else 0
            yoy = _gr(val, py_val)
            pct = val / total_metric * 100 if total_metric else 0

            r1, r2, r3 = st.columns([1.7, 2.35, 2.2])
            with r1:
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-top:18px;white-space:nowrap;">
                        <span class="seg-name">{seg}</span>
                        <span class="seg-yoy" style="color:{CG if yoy >= 0 else CR};">
                            {'▲' if yoy >= 0 else '▼'} {abs(yoy):.1f}%
                        </span>
                        <span class="cus-sub">vs PY</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with r2:
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=[max_metric], y=[seg], orientation="h",
                                         marker_color="#EAF1F8", hoverinfo="skip", showlegend=False))
                fig_bar.add_trace(go.Bar(x=[val], y=[seg], orientation="h", marker_color=CB,
                                         text=[f"{int(val):,}<br>({pct:.1f}%)"],
                                         textposition="outside", textfont=dict(size=12, color=CN),
                                         showlegend=False,
                                         hovertemplate=f"<b>{seg}</b><br>{metric}: %{{x:,.0f}}<extra></extra>"))
                fig_bar.update_layout(height=68, margin=dict(l=0, r=50, t=2, b=2),
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      barmode="overlay", xaxis=dict(visible=False, range=[0, max_metric * 1.25]),
                                      yaxis=dict(visible=False))
                st.plotly_chart(fig_bar, use_container_width=True, config=CFG)
            with r3:
                seg_month = d_cy[d_cy["Segment"] == seg].groupby("Month").agg(
                    Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                    Orders=("Order ID", "nunique")).reindex(range(1, 13)).fillna(0)
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=list(range(1, 13)), y=seg_month[metric], mode="lines",
                                              line=dict(color=CB, width=2.2), fill="tozeroy",
                                              fillcolor="rgba(2,136,209,0.14)", showlegend=False))
                fig_line.update_layout(height=68, margin=dict(l=0, r=0, t=2, b=2),
                                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                       xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig_line, use_container_width=True, config=CFG)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Top 15 customers
        st.markdown('<div class="cus-panel">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="cus-small-title">{metric} | <span class="cus-blue">Top 15 Customers</span></div>
            <div class="cus-sub">
                <span class="legend-dot" style="background:#0288D1"></span>Profitable
                &nbsp;&nbsp;
                <span class="legend-dot" style="background:#E45757"></span>Not Profitable
            </div>
            """,
            unsafe_allow_html=True
        )

        cust_df = d_cy.groupby("Customer Name").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                                                    Orders=("Order ID", "nunique")).reset_index()
        top_cust = cust_df.nlargest(15, metric).sort_values(metric) if len(cust_df) else cust_df
        colors = [CB if p >= 0 else "#E45757" for p in top_cust.get("Profit", [])]
        avg_val = cust_df[metric].mean() if len(cust_df) else 0
        max_val = top_cust[metric].max() if len(top_cust) else 1
        max_val = max(max_val, 1)

        fig_top = go.Figure()
        fig_top.add_trace(go.Bar(
            x=top_cust[metric] if len(top_cust) else [],
            y=top_cust["Customer Name"] if len(top_cust) else [],
            orientation="h", marker_color=colors,
            text=[_fmt(v, metric) if metric in ["Sales", "Profit"] else f"{int(v)}" for v in (top_cust[metric] if len(top_cust) else [])],
            textposition="outside", textfont=dict(size=12, color=CN),
            customdata=top_cust["Customer Name"] if len(top_cust) else [],
            hovertemplate="<b>%{y}</b><br>" + metric + ": %{x:,.0f}<extra></extra>"
        ))
        fig_top.add_vline(x=avg_val, line_width=1.4, line_color=CN, opacity=0.8)
        fig_top.update_layout(height=285, margin=dict(l=8, r=60, t=10, b=5),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(visible=False, range=[0, max_val * 1.15]),
                              yaxis=dict(showgrid=False, tickfont=dict(size=12), autorange="reversed"),
                              showlegend=False)
        ev_top = st.plotly_chart(fig_top, use_container_width=True, config=CFG,
                                 on_select="rerun", key="cus_top15_new")
        if ev_top and ev_top.selection and ev_top.selection.points:
            cd = ev_top.selection.points[0].get("customdata")
            if cd: toggle("sel_customer", cd); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)



    # 3. New vs repeat customers trend — full dashboard width
    st.markdown('<div class="cus-panel" style="margin-top:2px">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cus-small-title">Trend of New & Repeat Customer</div>
        <div class="cus-sub">
            <span class="legend-dot" style="background:#0288D1"></span>Repeat Customer
            &nbsp;&nbsp;
            <span class="legend-dot" style="background:#8EC3E6"></span>New Customer
        </div>
        """,
        unsafe_allow_html=True
    )

    d_trend = slice_df(df, "All", f_reg, f_seg, "All", actions=True).copy()
    if not d_trend.empty:
        d_trend["OrderMonth"] = d_trend["Order Date"].dt.to_period("M").dt.to_timestamp()
        first_purchase = d_trend.groupby("Customer ID")["OrderMonth"].min().reset_index().rename(columns={"OrderMonth": "FirstMonth"})
        d_trend = d_trend.merge(first_purchase, on="Customer ID", how="left")
        d_trend["CustomerType"] = np.where(d_trend["OrderMonth"] == d_trend["FirstMonth"],
                                           "New Customer", "Repeat Customer")
        trend = d_trend.groupby(["OrderMonth", "CustomerType"])["Customer ID"].nunique().reset_index(name="Customers")
    else:
        trend = pd.DataFrame(columns=["OrderMonth", "CustomerType", "Customers"])

    fig_trend = go.Figure()
    for ctype, col in [("Repeat Customer", CB), ("New Customer", "#8EC3E6")]:
        temp = trend[trend["CustomerType"] == ctype]
        fig_trend.add_trace(go.Scatter(
            x=temp["OrderMonth"],
            y=temp["Customers"],
            mode="lines",
            line=dict(color=col, width=2.6),
            name=ctype,
            hovertemplate=f"<b>{ctype}</b><br>%{{x|%b %Y}}<br>Customers: %{{y}}<extra></extra>"
        ))

    if not trend.empty:
        x_min = trend["OrderMonth"].min()
        x_max = trend["OrderMonth"].max()
    else:
        x_min = None
        x_max = None

    fig_trend.update_layout(
        height=330,
        margin=dict(l=12, r=12, t=12, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=12),
            range=[x_min, x_max] if x_min is not None and x_max is not None else None,
            automargin=True
        ),
        yaxis=dict(visible=False, fixedrange=True),
        legend=dict(
            orientation="h",
            y=1.10,
            x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)"
        )
    )
    st.plotly_chart(fig_trend, use_container_width=True, config=CFG)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# RFM ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "RFM Analysis":

    st.markdown("""
    <style>
    .rfm-page-title{font-size:26px;font-weight:900;color:#0F1F3D;margin-bottom:2px;}
    .rfm-page-sub{font-size:12px;color:#7A8BA8;margin-bottom:8px;}
    .rfm-card{background:#fff;border-radius:14px;padding:12px 14px;box-shadow:0 1px 6px rgba(15,31,61,.08);margin-bottom:12px;}
    .rfm-big-value{font-size:34px;font-weight:900;color:#F5B400;line-height:1.1;}
    .rfm-card-title{font-size:13px;font-weight:800;color:#0F1F3D;text-transform:uppercase;margin-bottom:8px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="rfm-page-title">RFM Analysis Dashboard</div>
        <div class="rfm-page-sub">Customer segmentation based on Recency, Frequency, and Monetary value</div>
        """,
        unsafe_allow_html=True
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        f_year = st.selectbox("Year", ["All"] + [str(y) for y in YEARS], index=len(YEARS), key="rfm_year")
    with f2:
        f_reg = st.selectbox("Region", ["All"] + sorted(df["Region"].dropna().unique()), key="rfm_region")
    with f3:
        f_seg = st.selectbox("Customer Segment", ["All"] + sorted(df["Segment"].dropna().unique()), key="rfm_customer_segment")
    with f4:
        f_rfm = st.selectbox("RFM Segment", ["All"] + sorted(df["RFM_Segment"].dropna().unique()), key="rfm_segment_filter")

    d = slice_df(df, f_year, f_reg, f_seg, "All", actions=False).copy()
    if f_rfm != "All":
        d = d[d["RFM_Segment"] == f_rfm]

    rfm_customer = d.groupby("Customer ID").agg(
        Customer_Name=("Customer Name", "first"),
        R=("R", "first"),
        F=("F", "first"),
        M=("M", "first"),
        RFM_Segment=("RFM_Segment", "first"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique")
    ).reset_index() if not d.empty else pd.DataFrame(columns=["Customer ID","Customer_Name","R","F","M","RFM_Segment","Sales","Profit","Orders"])

    def make_rfm_score(s, reverse=False):
        """Return 1–5 score. If the column already looks like a 1–5 score, keep it."""
        s = pd.to_numeric(s, errors="coerce")
        valid = s.dropna()
        if valid.empty:
            return pd.Series([], dtype="Int64")
        looks_scored = valid.min() >= 1 and valid.max() <= 5 and valid.nunique() <= 5
        if looks_scored:
            return s.round().astype("Int64")
        ranks = s.rank(method="first", ascending=True)
        labels = [5,4,3,2,1] if reverse else [1,2,3,4,5]
        try:
            return pd.qcut(ranks, q=5, labels=labels, duplicates="drop").astype("Int64")
        except ValueError:
            return pd.Series([3] * len(s), index=s.index, dtype="Int64")

    if not rfm_customer.empty:
        # Lower recency is better, so reverse=True assigns higher score to recent customers.
        rfm_customer["R_Score"] = make_rfm_score(rfm_customer["R"], reverse=True)
        rfm_customer["F_Score"] = make_rfm_score(rfm_customer["F"], reverse=False)
        rfm_customer["M_Score"] = make_rfm_score(rfm_customer["M"], reverse=False)
    else:
        rfm_customer["R_Score"] = []
        rfm_customer["F_Score"] = []
        rfm_customer["M_Score"] = []

    total_customers = rfm_customer["Customer ID"].nunique() if not rfm_customer.empty else 0
    total_sales = d["Sales"].sum() if not d.empty else 0

    left, right = st.columns([1.1, 2.15])

    with left:
        st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        with k1:
            st.markdown(f'<div class="rfm-card-title">Number of Customers</div><div class="rfm-big-value">{total_customers:,}</div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="rfm-card-title">Total Sales</div><div class="rfm-big-value">{total_sales/1e6:.1f}M</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
        st.markdown('<div class="rfm-card-title" style="text-align:center">Customer Sales by Group</div>', unsafe_allow_html=True)
        rfm_group = d.groupby("RFM_Segment").agg(Sales=("Sales", "sum"), Customers=("Customer ID", "nunique")).reset_index().sort_values("Sales", ascending=True) if not d.empty else pd.DataFrame(columns=["RFM_Segment","Sales","Customers"])
        fig_group = go.Figure()
        fig_group.add_trace(go.Bar(
            x=rfm_group["Sales"], y=rfm_group["RFM_Segment"], orientation="h",
            marker_color="#12A8E0",
            text=[f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.1f}K" for v in rfm_group["Sales"]],
            textposition="outside", textfont=dict(size=12, color=CN),
            hovertemplate="<b>%{y}</b><br>Sales: $%{x:,.0f}<extra></extra>"
        ))
        max_group_sales = rfm_group["Sales"].max() if len(rfm_group) else 1
        max_group_sales = max(max_group_sales, 1)
        fig_group.update_layout(height=425, margin=dict(l=8, r=48, t=8, b=8),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                xaxis=dict(visible=False, range=[0, max_group_sales * 1.22]),
                                yaxis=dict(showgrid=False, tickfont=dict(size=12)), showlegend=False)
        st.plotly_chart(fig_group, use_container_width=True, config=CFG)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        r1, r2, r3 = st.columns(3)

        def rfm_score_bar(data, score_col, title, color):
            if data.empty or score_col not in data.columns:
                score_sales = pd.DataFrame({score_col: [1,2,3,4,5], "Sales": [0,0,0,0,0]})
            else:
                score_sales = data.groupby(score_col).agg(Sales=("Sales", "sum")).reset_index()
                score_sales[score_col] = pd.to_numeric(score_sales[score_col], errors="coerce")
                score_sales = score_sales.dropna().sort_values(score_col)
                score_sales = score_sales.set_index(score_col).reindex([1,2,3,4,5], fill_value=0).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=score_sales[score_col].astype(int).astype(str), y=score_sales["Sales"],
                marker_color=color,
                text=[f"{v/1e6:.0f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v > 0 else "" for v in score_sales["Sales"]],
                textposition="outside", textfont=dict(size=12, color=CN),
                hovertemplate="<b>Score %{x}</b><br>Sales: $%{y:,.0f}<extra></extra>"
            ))
            max_val = score_sales["Sales"].max() if len(score_sales) else 1
            max_val = max(max_val, 1)
            fig.update_layout(height=225, margin=dict(l=8, r=8, t=32, b=10),
                              title=dict(text=title, x=0.5, font=dict(size=18, color=CN, family="Inter")),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(showgrid=False, tickfont=dict(size=12)),
                              yaxis=dict(visible=False, range=[0, max_val * 1.25]), showlegend=False)
            return fig

        with r1:
            st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
            st.plotly_chart(rfm_score_bar(rfm_customer, "R_Score", "Sales by Recency", "#F5B400"), use_container_width=True, config=CFG)
            st.markdown('</div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
            st.plotly_chart(rfm_score_bar(rfm_customer, "F_Score", "Sales by Frequency Value", "#8BDD4F"), use_container_width=True, config=CFG)
            st.markdown('</div>', unsafe_allow_html=True)
        with r3:
            st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
            st.plotly_chart(rfm_score_bar(rfm_customer, "M_Score", "Sales by Monetary Value", "#15A9DD"), use_container_width=True, config=CFG)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="rfm-card">', unsafe_allow_html=True)
        st.markdown('<div class="rfm-card-title" style="text-align:center;font-size:16px">RFM Score Matrix</div>', unsafe_allow_html=True)
        matrix_df = rfm_customer.groupby("RFM_Segment").agg(Customers=("Customer ID", "nunique"), Sales=("Sales", "sum")).reset_index() if not rfm_customer.empty else pd.DataFrame(columns=["RFM_Segment","Customers","Sales"])

        matrix_layout = {
            "Champions":             dict(x=4.8, y=4.6, w=0.9, h=0.8, color="#83DC45"),
            "Loyal Customers":       dict(x=3.6, y=4.0, w=2.0, h=1.5, color="#E4F4D8"),
            "Loyal":                 dict(x=3.6, y=4.0, w=2.0, h=1.5, color="#E4F4D8"),
            "Potential Loyalist":    dict(x=4.2, y=2.4, w=1.8, h=1.2, color="#BFE8F3"),
            "Potential loyalist":    dict(x=4.2, y=2.4, w=1.8, h=1.2, color="#BFE8F3"),
            "New Customers":         dict(x=4.8, y=1.0, w=1.0, h=0.9, color="#FFD978"),
            "New customers":         dict(x=4.8, y=1.0, w=1.0, h=0.9, color="#FFD978"),
            "Promising":             dict(x=4.0, y=1.0, w=0.9, h=0.9, color="#BEE3F8"),
            "Need Attention":        dict(x=3.0, y=2.8, w=1.1, h=0.9, color="#16A9DD"),
            "Need attention":        dict(x=3.0, y=2.8, w=1.1, h=0.9, color="#16A9DD"),
            "About To Sleep":        dict(x=3.0, y=1.5, w=1.1, h=0.9, color="#8BD3EC"),
            "About to sleep":        dict(x=3.0, y=1.5, w=1.1, h=0.9, color="#8BD3EC"),
            "Hibernating":           dict(x=2.0, y=1.5, w=1.1, h=0.9, color="#75B9EA"),
            "Lost":                  dict(x=1.0, y=1.0, w=1.1, h=1.2, color="#D7F4C8"),
            "Lost Customers":        dict(x=1.0, y=1.0, w=1.1, h=1.2, color="#D7F4C8"),
            "At Risk":               dict(x=1.6, y=3.0, w=2.2, h=1.6, color="#FFD35C"),
            "At risk":               dict(x=1.6, y=3.0, w=2.2, h=1.6, color="#FFD35C"),
            "Cannot Lose Them":      dict(x=1.0, y=4.5, w=1.1, h=0.8, color="#13A8DD"),
            "Cannot lose them":      dict(x=1.0, y=4.5, w=1.1, h=0.8, color="#13A8DD"),
            "Regular Customers":     dict(x=3.0, y=3.6, w=1.1, h=0.9, color="#E4F4D8"),
            "High Value":            dict(x=3.4, y=4.3, w=1.1, h=0.9, color="#DFF4D5")
        }

        fig_matrix = go.Figure()
        used_segments = set()
        for _, row in matrix_df.iterrows():
            seg = row["RFM_Segment"]
            if seg not in matrix_layout:
                continue
            used_segments.add(seg)
            box = matrix_layout[seg]
            x0 = box["x"] - box["w"] / 2; x1 = box["x"] + box["w"] / 2
            y0 = box["y"] - box["h"] / 2; y1 = box["y"] + box["h"] / 2
            fig_matrix.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                                 line=dict(color="white", width=1), fillcolor=box["color"])
            fig_matrix.add_annotation(x=box["x"], y=box["y"],
                                      text=f"<b>{seg}</b><br>{int(row['Customers'])}",
                                      showarrow=False, font=dict(size=12, color=CN))

        # If a segment in the data is not mapped above, show it as a small note.
        unmapped = [s for s in matrix_df["RFM_Segment"].dropna().tolist() if s not in used_segments and s not in matrix_layout]
        if unmapped:
            fig_matrix.add_annotation(x=3, y=0.55, text="Other: " + ", ".join(unmapped[:3]),
                                      showarrow=False, font=dict(size=12, color=CN))

        fig_matrix.update_layout(height=325, margin=dict(l=50, r=8, t=8, b=38),
                                 paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#EAF7DE",
                                 xaxis=dict(range=[0.3, 5.5], title="Recency score", showgrid=False,
                                            zeroline=False, visible=True, tickvals=[1,2,3,4,5], tickfont=dict(size=12)),
                                 yaxis=dict(range=[0.3, 5.3], title="Frequency & Monetary score", showgrid=False,
                                            zeroline=False, visible=True, tickvals=[1,2,3,4,5], tickfont=dict(size=12)),
                                 showlegend=False)
        st.plotly_chart(fig_matrix, use_container_width=True, config=CFG)
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# ORDER DETAILS
# ════════════════════════════════════════════════════════════
elif page == "Order Details":
    st.markdown('<div class="dtitle">Order Details</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: f_year=st.selectbox("Year",     ["All"]+[str(y) for y in YEARS],index=len(YEARS))
    with c2: f_reg =st.selectbox("Region",   ["All"]+sorted(df["Region"].unique()))
    with c3: f_seg =st.selectbox("Segment",  ["All"]+sorted(df["Segment"].unique()))
    with c4: f_cat =st.selectbox("Category", ["All"]+sorted(df["Category"].unique()))
    with c5: f_ship=st.selectbox("Ship Mode",["All"]+sorted(df["Ship Mode"].unique()))
    render_pills("ord")

    d_kpi,d_cy,d_py,yr,yr_py = get_cy_py(df,f_year,f_reg,f_seg,f_cat)
    d = slice_df(df,f_year,f_reg,f_seg,f_cat)
    if f_ship != "All": d=d[d["Ship Mode"]==f_ship]

    aov   =d_cy.groupby("Order ID")["Sales"].sum().mean() if len(d_cy) else 0
    aov_py=d_py.groupby("Order ID")["Sales"].sum().mean() if len(d_py) else 0
    avg_s =(d_cy["Ship Date"]-d_cy["Order Date"]).dt.days.mean() if len(d_cy) else 0
    avg_sp=(d_py["Ship Date"]-d_py["Order Date"]).dt.days.mean() if len(d_py) else 0

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi_card("ORDERS",    f"{d_kpi['Order ID'].nunique():,}",
        _gr(d_cy['Order ID'].nunique(),d_py['Order ID'].nunique()),"PY"),unsafe_allow_html=True)
    k2.markdown(kpi_card("SALES",     _fmt(d_kpi["Sales"].sum()),
        _gr(d_cy["Sales"].sum(),d_py["Sales"].sum()),"PY"),unsafe_allow_html=True)
    k3.markdown(kpi_card("AVG ORDER", f"${aov:,.0f}",_gr(aov,aov_py),"PY"),unsafe_allow_html=True)
    k4.markdown(kpi_card("AVG SHIP",  f"{avg_s:.1f}d",-_gr(avg_s,avg_sp),f"{avg_sp:.1f}d PY"),unsafe_allow_html=True)

    od1,od2 = st.columns(2)
    with od1:
        ship_d=d.groupby("Ship Mode").agg(Orders=("Order ID","nunique")).reset_index()
        fig_ship=px.pie(ship_d,values="Orders",names="Ship Mode",
            color="Ship Mode",color_discrete_map=SHIP_C,hole=0.42)
        fig_ship.update_traces(textinfo="label+percent",textfont_size=12)
        fig_ship.update_layout(**_lo(225),showlegend=False)
        cht("Orders by Ship Mode")
        st.plotly_chart(fig_ship,use_container_width=True,config=CFG)

    with od2:
        mo=d.groupby(["Year","Month"]).agg(Orders=("Order ID","nunique")).reset_index()
        mo["Date"]=pd.to_datetime(mo.assign(Day=1)[["Year","Month","Day"]])
        fig_mo=px.line(mo,x="Date",y="Orders",color="Year",
            color_discrete_sequence=[CLB,"#90CAF9",CB,CN])
        fig_mo.update_layout(**_lo(225),
            xaxis=dict(showgrid=False,tickformat="%b"),
            yaxis=dict(showgrid=True,gridcolor=CGR),
            legend=dict(orientation="h",y=1.1,font_size=9,x=0))
        cht("Monthly Orders by Year")
        st.plotly_chart(fig_mo,use_container_width=True,config=CFG)

    cols_show=["Order ID","Order Date","Customer Name","Segment","Region","State",
               "Category","Sub-Category","Product Name","Sales","Quantity","Discount",
               "Profit","Ship Mode","RFM_Segment"]
    cht("Transaction Detail")
    st.dataframe(d[cols_show].sort_values("Order Date",ascending=False).head(500),
        use_container_width=True,hide_index=True,height=285,
        column_config={
            "Sales":   st.column_config.NumberColumn("Sales ($)", format="$%.2f"),
            "Profit":  st.column_config.NumberColumn("Profit ($)",format="$%.2f"),
            "Discount":st.column_config.NumberColumn("Disc",      format="%.0f%%"),
        })