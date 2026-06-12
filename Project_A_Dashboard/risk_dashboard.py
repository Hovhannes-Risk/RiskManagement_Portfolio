from pathlib import Path
from datetime import datetime
import io

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title="Betting Risk Dashboard", page_icon="⚠️", layout="wide")

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "sample_data"


# NOTE: All data in sample_data/ is FULLY SYNTHETIC — a one-day slice of
# the deterministic dataset produced by data_generator/ (seed 42).
# No real player exists behind any P-ID.
@st.cache_data
def load_data():
    try:
        bets_df = pd.read_excel(DATA_DIR / "mydata_sample.xlsx", sheet_name="Raw_Data")
        bets_df["bet_datetime"] = pd.to_datetime(bets_df["bet_time"], errors="coerce")
        try:
            risk_df = pd.read_excel(DATA_DIR / "player_risk_scores.xlsx", sheet_name="All_Players")
        except FileNotFoundError:
            risk_df = None
        try:
            multi_df = pd.read_excel(DATA_DIR / "multi_account_detection.xlsx", sheet_name="All_Pairs")
        except FileNotFoundError:
            multi_df = None
        return bets_df, risk_df, multi_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None


@st.cache_data
def compute_bot_suspects(df):
    d = df.dropna(subset=["bet_datetime"]).copy()
    d["sec"] = d["bet_datetime"].dt.floor("s")
    counts = d.groupby(["bettor", "sec"]).size()
    return counts[counts > 1].reset_index()["bettor"].nunique()


def color_risk(val):
    colors = {
        "CRITICAL": "background-color: #ff4444; color: white",
        "HIGH": "background-color: #ff8800; color: white",
        "MEDIUM": "background-color: #ffcc00; color: black",
        "LOW": "background-color: #44cc44; color: black",
        "MINIMAL": "background-color: #aaaaaa; color: black"
    }
    return colors.get(val, "")


def generate_pdf(filtered_bets, total_ggr, start_date, end_date, risk_df, multi_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Colors
    NAVY = (26, 26, 46)
    RED = (192, 57, 43)
    GREEN = (29, 122, 78)
    AMBER = (180, 83, 9)
    GRAY = (107, 114, 128)
    LIGHT = (248, 249, 250)
    
    # === HEADER BAR ===
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(10, 8)
    pdf.cell(0, 8, "RISK MANAGEMENT REPORT", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10)
    pdf.cell(0, 5, f"Period: {start_date} to {end_date}  |  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # === CONFIDENTIAL BANNER ===
    pdf.set_fill_color(*LIGHT)
    pdf.set_y(35)
    pdf.rect(10, pdf.get_y(), 190, 7, "F")
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(10, pdf.get_y() + 1.5)
    pdf.cell(0, 4, "  SYNTHETIC DATASET  -  generated, seed 42  -  no real player data", ln=True)
    pdf.ln(4)
    
    # === ALERTS ===
    pdf.set_text_color(0, 0, 0)
    
    alerts = []
    if total_ggr < 0:
        alerts.append(("NEGATIVE GGR", f"House is losing ${abs(total_ggr):,.2f}", RED))
    if multi_df is not None:
        critical = len(multi_df[multi_df["Risk_Level"] == "CRITICAL"])
        if critical > 0:
            alerts.append(("MULTI-ACCOUNT", f"{critical} CRITICAL suspicious pairs detected", RED))
    if risk_df is not None:
        crit_players = len(risk_df[risk_df["Risk_Level"] == "CRITICAL"])
        if crit_players > 0:
            alerts.append(("CRITICAL PLAYERS", f"{crit_players} players flagged as CRITICAL risk", RED))
    
    if alerts:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, "ALERTS", ln=True)
        pdf.set_draw_color(*NAVY)
        pdf.line(10, pdf.get_y(), 50, pdf.get_y())
        pdf.ln(3)
        
        for title, msg, color in alerts:
            pdf.set_fill_color(255, 240, 240)
            pdf.set_draw_color(*color)
            pdf.set_line_width(0.5)
            y_start = pdf.get_y()
            pdf.rect(10, y_start, 190, 10, "DF")
            pdf.set_xy(13, y_start + 2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*color)
            pdf.cell(45, 6, f"[!] {title}")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, msg, ln=True)
            pdf.ln(1)
        pdf.ln(3)
    
    # === KEY METRICS ===
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "KEY METRICS", ln=True)
    pdf.set_draw_color(*NAVY)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)
    
    total_stake = filtered_bets['usd_amount'].sum()
    hold_pct = (total_ggr / total_stake * 100) if total_stake else 0
    
    metrics = [
        ("TOTAL BETS", f"{len(filtered_bets):,}", (0, 0, 0)),
        ("TOTAL PLAYERS", f"{filtered_bets['bettor'].nunique():,}", (0, 0, 0)),
        ("TOTAL STAKE", f"${total_stake:,.0f}", (0, 0, 0)),
        ("TOTAL GGR", f"${total_ggr:,.0f}", RED if total_ggr < 0 else GREEN),
        ("HOLD %", f"{hold_pct:+.2f}%", RED if hold_pct < 0 else GREEN),
        ("AVG BET", f"${(total_stake/max(len(filtered_bets),1)):,.0f}", (0, 0, 0)),
    ]
    
    box_w = 31
    box_h = 18
    start_x = 10
    y = pdf.get_y()
    
    for i, (label, value, color) in enumerate(metrics):
        x = start_x + i * (box_w + 1)
        pdf.set_fill_color(*LIGHT)
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(x, y, box_w, box_h, "DF")
        pdf.set_xy(x, y + 2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*GRAY)
        pdf.cell(box_w, 4, label, align="C")
        pdf.set_xy(x, y + 8)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*color)
        pdf.cell(box_w, 6, value, align="C")
    
    pdf.set_y(y + box_h + 6)
    pdf.set_text_color(0, 0, 0)
    
    # === SPORT BREAKDOWN ===
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "TOP SPORTS BY VOLUME", ln=True)
    pdf.set_draw_color(*NAVY)
    pdf.line(10, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(3)
    
    sport_table = filtered_bets.groupby("sports").agg(
        Bets=("bet_id", "count"),
        Stake=("usd_amount", "sum"),
        GGR=("usd_ggr", "sum")
    ).reset_index().sort_values("Bets", ascending=False).head(10)
    
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(60, 7, "  Sport", border=0, fill=True)
    pdf.cell(35, 7, "Bets", border=0, fill=True, align="R")
    pdf.cell(50, 7, "Stake ($)", border=0, fill=True, align="R")
    pdf.cell(45, 7, "GGR ($)  ", border=0, fill=True, align="R", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for i, (_, row) in enumerate(sport_table.iterrows()):
        if i % 2 == 0:
            pdf.set_fill_color(*LIGHT)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(60, 6, f"  {row['sports']}", border=0, fill=True)
        pdf.cell(35, 6, f"{row['Bets']:,}", border=0, fill=True, align="R")
        pdf.cell(50, 6, f"${row['Stake']:,.0f}", border=0, fill=True, align="R")
        ggr_val = row['GGR']
        if ggr_val < 0:
            pdf.set_text_color(*RED)
        else:
            pdf.set_text_color(*GREEN)
        pdf.cell(45, 6, f"${ggr_val:,.0f}  ", border=0, fill=True, align="R", ln=True)
        pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    
    # === RISK SUMMARY ===
    if risk_df is not None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, "RISK BAND DISTRIBUTION", ln=True)
        pdf.set_draw_color(*NAVY)
        pdf.line(10, pdf.get_y(), 80, pdf.get_y())
        pdf.ln(3)
        
        risk_counts = risk_df["Risk_Level"].value_counts()
        order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
        colors_map = {"CRITICAL": RED, "HIGH": (220, 80, 60), "MEDIUM": AMBER, "LOW": GREEN, "MINIMAL": GRAY}
        
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(60, 7, "  Risk Level", border=0, fill=True)
        pdf.cell(50, 7, "Players", border=0, fill=True, align="R")
        pdf.cell(80, 7, "% of Total", border=0, fill=True, align="R", ln=True)
        
        total_players = len(risk_df)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        for i, level in enumerate(order):
            count = risk_counts.get(level, 0)
            pct = (count / total_players * 100) if total_players else 0
            if i % 2 == 0:
                pdf.set_fill_color(*LIGHT)
            else:
                pdf.set_fill_color(255, 255, 255)
            color = colors_map[level]
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(60, 6, f"  {level}", border=0, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(50, 6, f"{count}", border=0, fill=True, align="R")
            pdf.cell(80, 6, f"{pct:.1f}%  ", border=0, fill=True, align="R", ln=True)
    
    # === FOOTER ===
    pdf.set_y(280)
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 280, 210, 17, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(10, 283)
    pdf.cell(0, 4, "Risk Management Portfolio", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_x(10)
    pdf.cell(0, 4, "github.com/Hovhannes-Risk/RiskManagement_Portfolio", ln=True)
    pdf.set_x(10)
    pdf.cell(0, 4, "CONFIDENTIAL  -  For internal review only", ln=True)
    
    return bytes(pdf.output())


bets_df, risk_df, multi_df = load_data()
if bets_df is None:
    st.error("Could not load data")
    st.stop()

st.sidebar.title("⚠️ Risk Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["📊 Overview", "🔍 Player Risk", "⚠️ Multi-Account Alerts", "📈 Analytics"])
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Date Filter")
min_date = bets_df["bet_datetime"].min().date()
max_date = bets_df["bet_datetime"].max().date()
start_date = st.sidebar.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
mask = (bets_df["bet_datetime"].dt.date >= start_date) & (bets_df["bet_datetime"].dt.date <= end_date)
filtered_bets = bets_df[mask]
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.sidebar.markdown(f"**Total Bets:** {len(filtered_bets):,}")
st.sidebar.markdown(f"**Total Players:** {filtered_bets['bettor'].nunique():,}")
st.sidebar.markdown(f"**Total GGR:** ${filtered_bets['usd_ggr'].sum():,.2f}")

if page == "📊 Overview":
    st.title("📊 Risk Management Overview")
    if risk_df is not None:
        critical_count = len(risk_df[risk_df["Risk_Level"] == "CRITICAL"])
        high_count = len(risk_df[risk_df["Risk_Level"] == "HIGH"])
        if critical_count > 0:
            st.error(f"🚨 **CRITICAL ALERT:** {critical_count} players flagged as CRITICAL risk!")
        if high_count > 5:
            st.warning(f"⚠️ **HIGH RISK:** {high_count} players require immediate review")
    if multi_df is not None:
        critical_pairs = len(multi_df[multi_df["Risk_Level"] == "CRITICAL"])
        if critical_pairs > 0:
            st.error(f"🚨 **MULTI-ACCOUNT ALERT:** {critical_pairs} CRITICAL suspicious pairs detected!")

    total_ggr = filtered_bets["usd_ggr"].sum()
    total_stake = filtered_bets["usd_amount"].sum()
    hold_pct = (total_ggr / total_stake * 100) if total_stake else 0
    bot_suspects = compute_bot_suspects(filtered_bets)

    if total_ggr < 0:
        st.error(f"🚨 **NEGATIVE GGR:** House is losing ${abs(total_ggr):,.2f}  (Hold {hold_pct:+.2f}%)")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Bets", f"{len(filtered_bets):,}")
    c2.metric("Total Players", f"{filtered_bets['bettor'].nunique():,}")
    c3.metric("Total Stake", f"${total_stake:,.0f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Total GGR", f"${total_ggr:,.0f}")
    c5.metric("Hold %", f"{hold_pct:+.2f}%")
    c6.metric("🤖 Bot Suspects", f"{bot_suspects:,}")

    st.markdown("---")
    st.subheader("📉 GGR Trend (Daily)")
    st.caption("Public sample covers a single trading day (2026-05-20) — in production this chart shows a rolling multi-week trend.")
    daily = (
        filtered_bets.dropna(subset=["bet_datetime"])
        .assign(day=lambda d: d["bet_datetime"].dt.date)
        .groupby("day")["usd_ggr"].sum().reset_index()
    )
    if len(daily) > 0:
        max_abs = max(abs(daily["usd_ggr"].min()), abs(daily["usd_ggr"].max()), 1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["day"], y=daily["usd_ggr"], mode="lines+markers",
            line=dict(width=2, color="#1f77b4"),
            marker=dict(size=8, color=daily["usd_ggr"], colorscale="RdYlGn",
                        cmin=-max_abs, cmax=max_abs, line=dict(width=1, color="white")),
            name="Daily GGR",
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(xaxis_title="Date", yaxis_title="GGR ($)",
                          height=350, margin=dict(l=40, r=20, t=20, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in selected date range.")

    st.markdown("---")
    st.subheader("📄 Download PDF Report")
    pdf_bytes = generate_pdf(filtered_bets, total_ggr, start_date, end_date, risk_df, multi_df)
    st.download_button(label="📄 Download PDF Report", data=pdf_bytes,
        file_name=f"risk_summary_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Top Risk Players")
        if risk_df is not None:
            top_risk = risk_df.head(10)[["Bets", "Total_Stake", "GGR", "Risk_Score", "Risk_Level"]]
            st.dataframe(top_risk.style.map(color_risk, subset=["Risk_Level"]), use_container_width=True)
        else:
            st.info("Run player_risk_scoring.py first")
    with col2:
        st.subheader("📊 Bets by Sport")
        sport_counts = filtered_bets["sports"].value_counts().head(10).sort_values()
        fig = go.Figure(go.Bar(
            x=sport_counts.values, y=sport_counts.index, orientation="h",
            marker_color="#1f77b4",
            text=[f"{v:,}" for v in sport_counts.values], textposition="outside",
        ))
        fig.update_layout(xaxis_title="Bets", yaxis_title="",
                          height=350, margin=dict(l=20, r=60, t=20, b=40))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💰 GGR by Sport")
    sport_ggr = filtered_bets.groupby("sports")["usd_ggr"].sum().sort_values(ascending=True).tail(10)
    max_abs_sport = max(abs(sport_ggr.min()), abs(sport_ggr.max()), 1)
    fig = go.Figure(go.Bar(
        x=sport_ggr.values, y=sport_ggr.index, orientation="h",
        marker=dict(color=sport_ggr.values, colorscale="RdYlGn",
                    cmin=-max_abs_sport, cmax=max_abs_sport)))
    fig.update_layout(xaxis_title="GGR ($)", yaxis_title="Sport",
                      height=350, margin=dict(l=40, r=20, t=20, b=40))
    st.plotly_chart(fig, use_container_width=True)

elif page == "🔍 Player Risk":
    st.title("🔍 Player Risk Analysis")
    if risk_df is None:
        st.warning("No risk data. Run player_risk_scoring.py first.")
        st.stop()
    col1, col2 = st.columns([1, 3])
    with col1:
        risk_levels = ["All"] + list(risk_df["Risk_Level"].unique())
        selected_level = st.selectbox("Filter by Risk Level", risk_levels)
    with col2:
        search_account = st.text_input("Search Player ID", "")
    filtered_df = risk_df.copy()
    if selected_level != "All":
        filtered_df = filtered_df[filtered_df["Risk_Level"] == selected_level]
    if search_account:
        filtered_df = filtered_df[filtered_df.index.astype(str).str.contains(search_account, case=False)]
    st.subheader(f"Found {len(filtered_df)} players")
    col1, col2 = st.columns(2)
    with col1:
        risk_counts = filtered_df["Risk_Level"].value_counts()
        colors_map = {"CRITICAL": "#ff4444", "HIGH": "#ff8800", "MEDIUM": "#ffcc00",
                      "LOW": "#44cc44", "MINIMAL": "#aaaaaa"}
        bar_colors = [colors_map.get(l, "#888") for l in risk_counts.index]
        fig = go.Figure(go.Bar(x=risk_counts.index, y=risk_counts.values, marker_color=bar_colors))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.metric("Total Players", len(filtered_df))
        st.metric("Total Bets", f"{filtered_df['Bets'].sum():,}")
        st.metric("Total GGR", f"${filtered_df['GGR'].sum():,.2f}")
    display_cols = ["Bets", "Total_Stake", "GGR", "Avg_CLV", "Win_Rate", "Risk_Score", "Risk_Level"]
    st.dataframe(filtered_df[display_cols].style.map(color_risk, subset=["Risk_Level"]), use_container_width=True)
    buf = io.BytesIO()
    filtered_df[display_cols].to_excel(buf, index=True)
    buf.seek(0)
    st.download_button(
        label="📥 Download Player Data as Excel",
        data=buf,
        file_name=f"player_risk_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif page == "⚠️ Multi-Account Alerts":
    st.title("⚠️ Multi-Account Detection")
    if multi_df is None:
        st.warning("No data.")
        st.stop()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚨 CRITICAL", len(multi_df[multi_df["Risk_Level"] == "CRITICAL"]))
    with col2:
        st.metric("⚠️ HIGH", len(multi_df[multi_df["Risk_Level"] == "HIGH"]))
    with col3:
        st.metric("🟡 MEDIUM", len(multi_df[multi_df["Risk_Level"] == "MEDIUM"]))
    with col4:
        st.metric("Total Pairs", f"{len(multi_df):,}")
    risk_filter = st.selectbox("Filter", ["CRITICAL", "HIGH", "MEDIUM", "LOW", "ALL"])
    display_df = multi_df if risk_filter == "ALL" else multi_df[multi_df["Risk_Level"] == risk_filter]
    display_cols = ["Account_1", "Account_2", "Similarity_Score", "Sport_Sim", "Time_Sim", "Stake_Sim", "Risk_Level"]
    st.dataframe(display_df[display_cols].head(20).style.map(color_risk, subset=["Risk_Level"]), use_container_width=True)
    buf2 = io.BytesIO()
    display_df[display_cols].to_excel(buf2, index=False)
    buf2.seek(0)
    st.download_button(
        label="📥 Download Suspicious Pairs as Excel",
        data=buf2,
        file_name=f"multi_account_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    fig = px.histogram(display_df, x="Similarity_Score", nbins=50)
    st.plotly_chart(fig, use_container_width=True)

elif page == "📈 Analytics":
    st.title("📈 Betting Analytics")
    sport_data = filtered_bets.groupby("sports").agg(
        Bets=("bet_id", "count"), Stake=("usd_amount", "sum"), GGR=("usd_ggr", "sum")
    ).reset_index()
    fig = px.scatter(sport_data, x="Bets", y="GGR", size="Stake", color="sports", hover_name="sports")
    st.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Odds Distribution")
        fig = px.histogram(filtered_bets, x="odds", nbins=50)
        fig.update_xaxes(range=[1, 20])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Stake Distribution")
        fig = px.histogram(filtered_bets, x="usd_amount", nbins=50)
        fig.update_xaxes(range=[0, 1000])
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Betting by Hour")
    filtered_bets["Hour"] = filtered_bets["bet_datetime"].dt.hour
    hourly = filtered_bets.groupby("Hour").size().reset_index(name="Bets")
    fig = px.line(hourly, x="Hour", y="Bets", markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("**Risk Management Dashboard** | Built with Streamlit | *Bettor IDs anonymized for confidentiality*")
