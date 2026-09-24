import pandas as pd
import numpy as np


COST_PER_CONTACT = {"chat": 210, "email": 260, "voice": 520, "social": 240}
BLENDED_COST = 290
COST_PER_TRANSFER = 305
SLA_BREACH_CREDIT = 350
REPLACEMENT_SHIPPING = 340
AGENT_HOUR_COST = 165
TRAINING_BUDGET = 400000


def compute_replacement_cost(tickets_df, products_df):
    replacements = tickets_df[tickets_df["replacement_issued"] == "Y"].copy()
    merged = replacements.merge(products_df[["sku", "unit_cost_inr"]], left_on="product_sku", right_on="sku", how="left")
    merged["replacement_cost"] = merged["unit_cost_inr"] + REPLACEMENT_SHIPPING
    return merged


def quarterly_replacement_analysis(tickets_df, products_df):
    repl = compute_replacement_cost(tickets_df, products_df)
    repl["quarter"] = repl["created_at"].dt.to_period("Q")

    quarterly = repl.groupby("quarter").agg(
        replacement_count=("ticket_id", "count"),
        total_cost=("replacement_cost", "sum"),
        avg_cost=("replacement_cost", "mean"),
    ).reset_index()
    quarterly["quarter"] = quarterly["quarter"].astype(str)
    return quarterly


def compute_sla_breach_cost(tickets_df):
    from src.metrics import compute_sla_breach
    tickets_df = tickets_df.copy()
    tickets_df["sla_breach"] = compute_sla_breach(tickets_df)
    breach_count = tickets_df["sla_breach"].sum()
    return {
        "breach_count": int(breach_count),
        "breach_cost": int(breach_count * SLA_BREACH_CREDIT),
        "credit_per_breach": SLA_BREACH_CREDIT,
    }


def compute_transfer_cost(tickets_df):
    total_transfers = tickets_df["transfers"].sum()
    return {
        "total_transfers": int(total_transfers),
        "transfer_cost": int(total_transfers * COST_PER_TRANSFER),
        "cost_per_transfer": COST_PER_TRANSFER,
    }


def compute_business_goal(tickets_df, products_df, bottom_10_agent_ids):
    resolved = tickets_df[tickets_df["status"].isin(["resolved", "closed"])]

    repl_all = compute_replacement_cost(resolved, products_df)
    avg_replacement_cost = repl_all["replacement_cost"].mean()

    resolved_with_q = resolved.copy()
    resolved_with_q["quarter"] = resolved_with_q["created_at"].dt.to_period("Q")

    baseline_period = resolved[(resolved["created_at"] >= "2025-01-01") & (resolved["created_at"] < "2025-10-01")]
    baseline_repl_rate = (baseline_period["replacement_issued"] == "Y").mean()

    recent_period = resolved[resolved["created_at"] >= "2026-01-01"]
    recent_repl_rate = (recent_period["replacement_issued"] == "Y").mean()

    repl_recent = compute_replacement_cost(recent_period, products_df)
    repl_recent["quarter"] = repl_recent["created_at"].dt.to_period("Q")
    recent_quarters = repl_recent.groupby("quarter")["replacement_cost"].sum()
    recent_quarterly_avg_cost = recent_quarters.mean()

    repl_baseline = compute_replacement_cost(baseline_period, products_df)
    repl_baseline["quarter"] = repl_baseline["created_at"].dt.to_period("Q")
    baseline_quarters = repl_baseline.groupby("quarter")["replacement_cost"].sum()
    baseline_quarterly_avg_cost = baseline_quarters.mean()

    quarterly_savings = recent_quarterly_avg_cost - baseline_quarterly_avg_cost

    overall_csat = resolved[resolved["csat_score"].notna()]["csat_score"].mean()
    pre_festive_csat = baseline_period[baseline_period["csat_score"].notna()]["csat_score"].mean()
    post_festive_csat = recent_period[recent_period["csat_score"].notna()]["csat_score"].mean()

    bottom_10_tickets = resolved[resolved["agent_id"].isin(bottom_10_agent_ids)]
    bottom_10_csat = bottom_10_tickets[bottom_10_tickets["csat_score"].notna()]["csat_score"].mean()

    from src.metrics import compute_sla_breach
    breach_overall = compute_sla_breach(resolved).mean()
    breach_bottom = compute_sla_breach(bottom_10_tickets).mean()

    return {
        "baseline_replacement_rate_pct": round(baseline_repl_rate * 100, 1),
        "recent_replacement_rate_pct": round(recent_repl_rate * 100, 1),
        "avg_replacement_cost_inr": round(avg_replacement_cost, 0),
        "recent_quarterly_replacement_cost": round(recent_quarterly_avg_cost, 0),
        "baseline_quarterly_replacement_cost": round(baseline_quarterly_avg_cost, 0),
        "quarterly_savings_potential": round(quarterly_savings, 0),
        "overall_csat": round(overall_csat, 2),
        "pre_festive_csat": round(pre_festive_csat, 2),
        "post_festive_csat": round(post_festive_csat, 2),
        "bottom_10_csat": round(bottom_10_csat, 2),
        "overall_breach_rate_pct": round(breach_overall * 100, 1),
        "bottom_10_breach_rate_pct": round(breach_bottom * 100, 1),
        "training_budget": TRAINING_BUDGET,
        "replacement_shipping_cost": REPLACEMENT_SHIPPING,
        "sla_breach_credit": SLA_BREACH_CREDIT,
    }
