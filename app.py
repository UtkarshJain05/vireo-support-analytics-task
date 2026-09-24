import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import load_tickets, load_agents, load_products, get_agent_lookup, get_resolved_tickets
from src.metrics import agent_performance, overall_kpis, monthly_trend
from src.ranking import compute_bottom_10
from src.business_impact import compute_business_goal, quarterly_replacement_analysis, compute_sla_breach_cost, compute_transfer_cost
from src.ai_analysis import analyze_themes_for_bottom_agents, classify_tickets_batch, is_ai_available

st.set_page_config(page_title="Vireo Audio — Support Analytics", page_icon="🎧", layout="wide")

st.title("🎧 Vireo Audio — Support Analytics Dashboard")
st.caption("CSAT & Handle Time per Agent · Bottom 10 Flagged for Review · AI-Assisted Ticket Insights")


@st.cache_data
def load_all_data():
    tickets = load_tickets()
    agents = load_agents()
    products = load_products()
    agent_lookup = get_agent_lookup(agents)
    resolved = get_resolved_tickets(tickets)
    return tickets, agents, products, agent_lookup, resolved


@st.cache_data
def compute_agent_perf(_resolved, _agent_lookup):
    return agent_performance(_resolved, _agent_lookup)


@st.cache_data
def compute_ranking(_agent_perf):
    return compute_bottom_10(_agent_perf)


tickets, agents, products, agent_lookup, resolved = load_all_data()
agent_perf = compute_agent_perf(resolved, agent_lookup)
all_agents_df, eligible_df, ranking_meta = compute_ranking(agent_perf)

kpis = overall_kpis(tickets)

st.header("📊 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Tickets", f"{kpis['total_tickets']:,}")
col2.metric("Active Agents", kpis["num_agents"])
col3.metric("Overall CSAT", f"{kpis['overall_csat']:.2f} / 5")
col4.metric("Avg Handle Time", f"{kpis['avg_handle_time_hrs']:.1f} hrs")
col5.metric("Open / Pending", kpis["open_tickets"])

col6, col7, col8 = st.columns(3)
col6.metric("CSAT Response Rate", f"{kpis['csat_response_rate']}%")
col7.metric("Total Replacements", f"{kpis['total_replacements']:,}")
col8.metric("Total Refunds (₹)", f"₹{kpis['total_refund_amount']:,.0f}")

st.divider()

st.header("📈 Monthly Trends")
trend = monthly_trend(resolved)

trend_tab1, trend_tab2, trend_tab3 = st.tabs(["CSAT Trend", "Handle Time Trend", "Volume Trend"])

with trend_tab1:
    fig = px.line(trend, x="month", y="avg_csat", markers=True, title="Average CSAT by Month")
    fig.update_layout(yaxis_title="Avg CSAT (1-5)", xaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True)

with trend_tab2:
    fig = px.line(trend, x="month", y="avg_handle_time_hrs", markers=True, title="Average Handle Time by Month", color_discrete_sequence=["orange"])
    fig.update_layout(yaxis_title="Avg Handle Time (hrs)", xaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True)

with trend_tab3:
    fig = px.bar(trend, x="month", y="ticket_count", title="Ticket Volume by Month", color_discrete_sequence=["#636EFA"])
    fig.update_layout(yaxis_title="Tickets", xaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("👤 Agent Performance")

display_df = all_agents_df.copy()
display_df["Review Flag"] = display_df["review_flag"].map({True: "⚠️ Flagged", False: ""})
display_df["Tier 2 (Excluded)"] = display_df["tier2_excluded"].map({True: "✓", False: ""})

display_cols = ["agent_id", "name", "team", "site", "tier", "ticket_count", "csat_mean",
                "csat_count", "avg_handle_time_hrs", "median_handle_time_hrs",
                "breach_rate", "replacement_count", "Review Flag", "Tier 2 (Excluded)"]
available_cols = [c for c in display_cols if c in display_df.columns]

if "composite_score" in eligible_df.columns:
    score_map = eligible_df.set_index("agent_id")["composite_score"].to_dict()
    display_df["composite_score"] = display_df["agent_id"].map(score_map)
    available_cols.insert(-2, "composite_score")

st.dataframe(
    display_df[available_cols].sort_values("csat_mean", ascending=True),
    use_container_width=True,
    height=600,
    column_config={
        "agent_id": "Agent ID",
        "name": "Name",
        "team": "Team",
        "site": "Site",
        "tier": "Tier",
        "ticket_count": "Tickets",
        "csat_mean": st.column_config.NumberColumn("Avg CSAT", format="%.2f"),
        "csat_count": "CSAT Responses",
        "avg_handle_time_hrs": st.column_config.NumberColumn("Avg HT (hrs)", format="%.2f"),
        "median_handle_time_hrs": st.column_config.NumberColumn("Median HT (hrs)", format="%.2f"),
        "breach_rate": st.column_config.NumberColumn("SLA Breach Rate", format="%.1%%"),
        "replacement_count": "Replacements",
        "composite_score": st.column_config.NumberColumn("Score", format="%.3f"),
        "Review Flag": "Review Flag",
        "Tier 2 (Excluded)": "Tier 2",
    }
)

st.divider()

st.header("📊 Agent Visualizations")
viz_tab1, viz_tab2, viz_tab3 = st.tabs(["CSAT by Agent", "Handle Time by Agent", "CSAT vs Handle Time"])

tier1_display = display_df[~display_df["tier2_excluded"]].copy()
tier1_display = tier1_display.sort_values("csat_mean", ascending=True)
tier1_display["color"] = tier1_display["review_flag"].map({True: "Flagged for Review", False: "Normal"})

with viz_tab1:
    fig = px.bar(
        tier1_display, x="name", y="csat_mean", color="color",
        color_discrete_map={"Flagged for Review": "#EF553B", "Normal": "#636EFA"},
        title="Average CSAT by Agent (Tier 1 Only)",
        labels={"csat_mean": "Avg CSAT", "name": "Agent", "color": "Status"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with viz_tab2:
    fig = px.bar(
        tier1_display.sort_values("avg_handle_time_hrs", ascending=False),
        x="name", y="avg_handle_time_hrs", color="color",
        color_discrete_map={"Flagged for Review": "#EF553B", "Normal": "#636EFA"},
        title="Average Handle Time by Agent (Tier 1 Only)",
        labels={"avg_handle_time_hrs": "Avg Handle Time (hrs)", "name": "Agent", "color": "Status"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with viz_tab3:
    fig = px.scatter(
        tier1_display, x="avg_handle_time_hrs", y="csat_mean",
        size="ticket_count", color="color", hover_data=["name", "team", "ticket_count"],
        color_discrete_map={"Flagged for Review": "#EF553B", "Normal": "#636EFA"},
        title="CSAT vs Handle Time (bubble size = ticket volume)",
        labels={"avg_handle_time_hrs": "Avg Handle Time (hrs)", "csat_mean": "Avg CSAT", "color": "Status"}
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("🚩 Bottom 10 — Agents Flagged for Review")

st.info(f"""**Methodology:** Composite score = {ranking_meta['csat_weight']*100:.0f}% CSAT percentile + {ranking_meta['handle_time_weight']*100:.0f}% Handle Time percentile (inverted).
Tier 2 agents ({ranking_meta['tier2_excluded_count']} agents in Escalations & Warranty) are excluded per policy §6.
Agents with fewer than {ranking_meta['min_csat_responses']} CSAT responses are excluded for statistical stability.
{ranking_meta['eligible_count']} of {ranking_meta['total_agents']} agents were eligible for ranking.""")

bottom_10 = eligible_df[eligible_df["review_flag"]].sort_values("composite_score", ascending=True)
bottom_display_cols = ["rank", "agent_id", "name", "team", "site", "ticket_count",
                        "csat_mean", "csat_count", "avg_handle_time_hrs",
                        "csat_percentile", "ht_percentile", "composite_score"]
available_bottom_cols = [c for c in bottom_display_cols if c in bottom_10.columns]

st.dataframe(
    bottom_10[available_bottom_cols],
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "agent_id": "Agent ID",
        "name": "Name",
        "team": "Team",
        "site": "Site",
        "ticket_count": "Tickets",
        "csat_mean": st.column_config.NumberColumn("Avg CSAT", format="%.2f"),
        "csat_count": "CSAT Responses",
        "avg_handle_time_hrs": st.column_config.NumberColumn("Avg HT (hrs)", format="%.2f"),
        "csat_percentile": st.column_config.NumberColumn("CSAT %ile", format="%.2f"),
        "ht_percentile": st.column_config.NumberColumn("HT %ile", format="%.2f"),
        "composite_score": st.column_config.NumberColumn("Score", format="%.3f"),
    }
)

for _, agent_row in bottom_10.iterrows():
    with st.expander(f"Agent: {agent_row['name']} ({agent_row['agent_id']}) — Score: {agent_row['composite_score']:.3f}"):
        st.markdown(f"""
- **Team:** {agent_row['team']} | **Site:** {agent_row['site']}
- **Tickets:** {agent_row['ticket_count']} | **CSAT Responses:** {agent_row['csat_count']}
- **Average CSAT:** {agent_row['csat_mean']:.2f} (percentile: {agent_row['csat_percentile']:.2f})
- **Average Handle Time:** {agent_row['avg_handle_time_hrs']:.2f} hrs (percentile: {agent_row['ht_percentile']:.2f})
- **SLA Breach Rate:** {agent_row.get('breach_rate', 'N/A')}

**Why flagged:** This agent's composite score ({agent_row['composite_score']:.3f}) places them in the bottom 10 of eligible Tier 1 agents based on a weighted combination of CSAT performance and handle time efficiency.
""")

st.divider()

st.header("🤖 AI-Powered Ticket Insights")

bottom_10_ids = bottom_10["agent_id"].tolist()

if is_ai_available():
    st.success("✅ AI analysis powered by Groq (GPT OSS 120B)")
else:
    st.warning("⚠️ No GROQ_API_KEY found in .env — using rule-based fallback analysis. Set GROQ_API_KEY for LLM-powered insights.")

if st.button("Run AI Theme Analysis", type="primary"):
    with st.spinner("Analyzing ticket themes for bottom-10 agents..."):
        themes = analyze_themes_for_bottom_agents(resolved, bottom_10_ids)

    if "api_error" in themes:
        st.error(f"⚠️ Groq API Call Failed (Falling back to rules):\n\n{themes['api_error']}")
    elif "source" in themes and "fallback" in themes.get("source", ""):
        st.caption("📋 Rule-based analysis (no API key)")

    st.subheader("Recurring Issue Themes")
    if themes.get("themes"):
        for theme in themes["themes"]:
            freq_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(theme.get("frequency", ""), "⚪")
            st.markdown(f"{freq_color} **{theme['theme']}** ({theme.get('frequency', 'N/A')}) — {theme.get('description', '')}")

    st.subheader("Factors Associated with Low CSAT")
    if themes.get("low_csat_factors"):
        for factor in themes["low_csat_factors"]:
            st.markdown(f"- {factor}")

    st.subheader("Recommended Training Focus Areas")
    if themes.get("training_recommendations"):
        for rec in themes["training_recommendations"]:
            st.markdown(f"- {rec}")

    st.subheader("Observed Process / Product Issues")
    if themes.get("process_issues"):
        for issue in themes["process_issues"]:
            st.markdown(f"- {issue}")

    if themes.get("summary"):
        st.info(f"**Summary:** {themes['summary']}")

st.divider()

st.header("💰 Business Goal & Financial Impact")

business = compute_business_goal(resolved, products, bottom_10_ids)

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Current Replacement Rate", f"{business['recent_replacement_rate_pct']}%")
    st.metric("Pre-Festive Baseline", f"{business['baseline_replacement_rate_pct']}%")
    st.metric("CSAT Pre vs Post Festive", f"{business['pre_festive_csat']} -> {business['post_festive_csat']}")

with col_b:
    st.metric("Est. Quarterly Savings", f"₹{business['quarterly_savings_potential']:,.0f}")
    st.metric("Recent Q Replacement Cost", f"₹{business['recent_quarterly_replacement_cost']:,.0f}")
    st.metric("Baseline Q Replacement Cost", f"₹{business['baseline_quarterly_replacement_cost']:,.0f}")

st.success(f"""**Business Goal:** Reduce the replacement rate from the current {business['recent_replacement_rate_pct']}% back toward the pre-festive baseline of {business['baseline_replacement_rate_pct']}%.

**Estimated impact:** approximately ₹{business['quarterly_savings_potential']:,.0f} per quarter in reduced replacement costs (unit cost + ₹{business['replacement_shipping_cost']} shipping per unit, per support-policy.pdf section 5).

**Training budget:** ₹{business['training_budget']:,.0f} allocated for Q3. Target the 10 flagged agents and the teams/categories driving the replacement spike.""")

st.caption(f"""**Assumptions and caveats:**
- Replacement cost = product unit cost (from products.csv) + ₹340 reverse-pickup and forward-shipping (policy section 5). Refurbishment recovery not assumed (policy section 5).
- Baseline = Jan to Sep 2025 (pre-festive); recent = Jan to Jun 2026. The festive season (Q4 2025) drove a volume spike and replacement surge.
- Savings assume process and training interventions can return replacement rates to baseline. Part of the spike may be driven by product quality (lot-level issues) rather than agent behavior alone.
- CSAT dropped from {business['pre_festive_csat']} to {business['post_festive_csat']} post-festive. Bottom-10 CSAT is {business['bottom_10_csat']}. Improving these agents performance would lift the overall average.
- SLA breach credit: ₹350 per breach (policy section 3). Overall breach rate: {business['overall_breach_rate_pct']}%.""")

quarterly_repl = quarterly_replacement_analysis(resolved, products)
if len(quarterly_repl) > 0:
    fig = px.bar(quarterly_repl, x="quarter", y="total_cost", title="Quarterly Replacement Cost (₹)",
                 color_discrete_sequence=["#EF553B"])
    fig.update_layout(yaxis_title="Total Replacement Cost (₹)", xaxis_title="Quarter")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("ℹ️ Data Quality Notes")
st.markdown(f"""
- **Total tickets loaded:** {len(tickets):,} (Jan 2025 to Jun 2026)
- **Legacy (Freshdesk) tickets:** {(tickets['source_system'] == 'legacy_fd').sum():,} with resolved_at converted from UTC to IST
- **Current helpdesk tickets:** {(tickets['source_system'] == 'helpdesk').sum():,}
- **CSAT response rate:** {kpis['csat_response_rate']}% (blank = no response, excluded from averages per policy section 8)
- **Open/pending tickets excluded** from handle-time and CSAT calculations ({kpis['open_tickets']} tickets)
- **Tier 2 agents excluded** from bottom-10 ranking per policy section 6 (multi-touch cases, different measurement basis)
- **Two agents named Kavya Pandey** exist (A3006/Chat Frontline, A3029/Logistics), joined on agent_id not name
- **Approximately 40 tickets** may have junk IVR transcripts in customer_message (per Sameer email)
- **Neha Kulkarni caveat:** Logistics/Returns Desk agents handle structurally harder queues. Flagging reflects queue difficulty, not necessarily individual skill gaps.
""")
