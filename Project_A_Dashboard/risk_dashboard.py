from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px# Navigate to your local repo
#cd C:\Users\7777\RiskManagement_Portfolio

# Check status
git status

# Copy the new file (replace old one)
copy "C:\Users\7777\Downloads\risk_dashboard.py" "Project_A_Dashboard\risk_dashboard.py"

# Add changes
git add Project_A_Dashboard/risk_dashboard.py

# Commit with message
git commit -m "Fix: Dashboard data validation bug + add docstrings"

# Push to GitHub
git push origin main
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title="Betting Risk Dashboard", page_icon="⚠️", layout="wide")

# Paths relative to this script — works on any machine
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "sample_data"


@st.cache_data
def load_bettor_mapping():
    """Load anonymization mapping from private file."""
    try:
        mapping_df = pd.read_excel(DATA_DIR / "bettor_mapping_PRIVATE.xlsx")
        return dict(zip(mapping_df["Original_Wallet"], mapping_df["Anonymous_ID"]))
    except FileNotFoundError:
        st.warning("⚠️ bettor_mapping_PRIVATE.xlsx not found — bettors will show as-is")
        return {}


@st.cache_data
def load_data():
    try:
        # Load main betting data
        bets_df = pd.read_excel(DATA_DIR / "mydata_sample.xlsx", sheet_name="Raw_Data")
        bets_df["bet_datetime"] = pd.to_datetime(bets_df["bet_time"], errors="coerce")
        
        # Load anonymization map
        bettor_map = load_bettor_mapping()
        
        # Anonymize bettor column
        if bettor_map:
            bets_df["bettor"] = bets_df["bettor"].map(bettor_map).fillna(bets_df["bettor"])
        
        # Load risk data (bettor is index)
        try:
            risk_df = pd.read_excel(DATA_DIR / "player_risk_scores.xlsx", sheet_name="All_Players")
            if bettor_map:
                risk_df.index = risk_df.index.map(lambda x: bettor_map.get(x, x))
        except FileNotFoundError:
            risk_df = None
        
        # Load multi-account data
        try:
            multi_df = pd.read_excel(DATA_DIR / "multi_account_detection.xlsx", sheet_name="All_Pairs")
            if bettor_map:
                multi_df["Account_1"] = multi_df["Account_1"].map(bettor_map).fillna(multi_df["Account_1"])
                multi_df["Account_2"] = multi_df["Account_2"].map(bettor_map).fillna(multi_df["Account_2"])
        except FileNotFoundError:
            multi_df = None
        
        return bets_df, risk_df, multi_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None


@st.cache_data
def compute_bot_suspects(df):
    """Count distinct bettors who placed >=2 bets in the exact same second."""
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
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Risk Management Summary Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Period: {start_date} to {end_date}", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    
    # Confidentiality notice
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "CONFIDENTIAL — Bettor IDs anonymized for data protection", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    
    if total_ggr < 0:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, f"ALERT: House is losing ${abs(total_ggr):,.2f}!", ln=True)
        pdf.set_text_color(0, 0, 0)
    if multi_df is not None:
        critical = len(multi_df[multi_df["Risk_Level"] == "CRITICAL"])
        if critical > 0:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 8, f"ALERT: {critical} CRITICAL multi-account pairs!", ln=True)
            pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Total Bets: {len(filtered_bets):,}", ln=True)
    pdf.cell(0, 8, f"Total Players: {filtered_bets['bettor'].nunique():,}", ln=True)
    pdf.cell(0, 8, f"Total GGR: ${total_ggr:,.2f}", ln=True)
    pdf.cell(0, 8, f"Total Stake: ${filtered_bets['usd_amount'].sum():,.2f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Top 10 Sports by Bets", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 8, "Sport", border=1)
    pdf.cell(40, 8, "Bets", border=1)
    pdf.cell(60, 8, "GGR ($)", border=1, ln=True)
    sport_table = filtered_bets.groupby("sports").agg(
        Bets=("bet_id", "count"), GGR=("usd_ggr", "sum")
    ).reset_index().sort_values("Bets", ascending=False).head(10)
    pdf.set_font("Helvetica", "", 10)
    for _, row in sport_table.iterrows():
        pdf.cell(80, 8, str(row["sports"]), border=1)
        pdf.cell(40, 8, f"{row['Bets']:,}", border=1)
        pdf.cell(60, 8, f"${row['GGR']:,.2f}", border=1, ln=True)
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

    # --- Alert banners ---
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

    # --- Core metrics ---
    total_ggr = filtered_bets["usd_ggr"].sum()
    total_stake = filtered_bets["usd_amount"].sum()
    hold_pct = (total_ggr / total_stake * 100) if total_stake else 0
    bot_suspects = compute_bot_suspects(filtered_bets)

    if total_ggr < 0:
        st.error(f"🚨 **NEGATIVE GGR:** House is losing ${abs(total_ggr):,.2f}  (Hold {hold_pct:+.2f}%)")

    # --- KPI row 1: volume ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Bets", f"{len(filtered_bets):,}")
    c2.metric("Total Players", f"{filtered_bets['bettor'].nunique():,}")
    c3.metric("Total Stake", f"${total_stake:,.0f}")

    # --- KPI row 2: risk-specific ---
    c4, c5, c6 = st.columns(3)
    c4.metric("Total GGR", f"${total_ggr:,.0f}")
    c5.metric(
        "Hold %",
        f"{hold_pct:+.2f}%",
        help="GGR / Stake × 100. Negative means the house is losing money.",
    )
    c6.metric(
        "🤖 Bot Suspects",
        f"{bot_suspects:,}",
        help="Distinct players who placed ≥2 bets in the exact same second.",
    )

    st.markdown("---")

    # --- GGR daily trend ---
    st.subheader("📉 GGR Trend (Daily)")
    daily = (
        filtered_bets.dropna(subset=["bet_datetime"])
        .assign(day=lambda d: d["bet_datetime"].dt.date)
        .groupby("day")["usd_ggr"].sum().reset_index()
    )
    if len(daily) > 0:
        max_abs = max(abs(daily["usd_ggr"].min()), abs(daily["usd_ggr"].max()), 1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["day"], y=daily["usd_ggr"],
            mode="lines+markers",
            line=dict(width=2, color="#1f77b4"),
            marker=dict(
                size=8,
                color=daily["usd_ggr"],
                colorscale="RdYlGn",
                cmin=-max_abs, cmax=max_abs,
                line=dict(width=1, color="white"),
            ),
            name="Daily GGR",
            hovertemplate="<b>%{x}</b><br>GGR: $%{y:,.2f}<extra></extra>",
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            xaxis_title="Date", yaxis_title="GGR ($)",
            height=350, margin=dict(l=40, r=20, t=20, b=40),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in selected date range.")

    st.markdown("---")

    # --- PDF download ---
    st.subheader("📄 Download PDF Report")
    pdf_bytes = generate_pdf(filtered_bets, total_ggr, start_date, end_date, risk_df, multi_df)
    st.download_button(label="📄 Download PDF Report", data=pdf_bytes,
        file_name=f"risk_summary_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
    st.markdown("---")

    # --- Top risk + Bets by sport (now bar chart instead of pie) ---
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
            x=sport_counts.values, y=sport_counts.index,
            orientation="h",
            marker_color="#1f77b4",
            text=[f"{v:,}" for v in sport_counts.values],
            textposition="outside",
        ))
        fig.update_layout(
            xaxis_title="Bets", yaxis_title="",
            height=350, margin=dict(l=20, r=60, t=20, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- GGR by sport ---
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
        colors_map = {"CRITICAL": "#ff4444", "HIGH": "#ff8800", "MEDIUM": "#ffcc00", "LOW": "#44cc44", "MINIMAL": "#aaaaaa"}
        bar_colors = [colors_map.get(l, "#888") for l in risk_counts.index]
        fig = go.Figure(go.Bar(x=risk_counts.index, y=risk_counts.values, marker_color=bar_colors))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.metric("Total Players", len(filtered_df))
        st.metric("Total Bets", f"{filtered_df['Bets'].sum():,}")
        st.metric("Total GGR", f"${filtered_df['GGR'].sum():,.2f}")
    display_cols = ["Bets", "Total_Stake", "GGR", "Avg_CLV", "Win_Rate", "Risk_Score", "Risk_Level"]
    st.dataframe(filtered_df[display_cols].style.map(color_risk, subset=["Risk_Level"]), use_container_width=True)
    csv = filtered_df[display_cols].to_csv(index=True).encode("utf-8")
    st.download_button(label="📥 Download Player Data as CSV", data=csv,
        file_name=f"player_risk_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

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
    csv = display_df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Download Suspicious Pairs as CSV", data=csv,
        file_name=f"multi_account_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
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
