import pandas as pd
import numpy as np


def compute_handle_time_hours(df):
    mask = df["resolved_at"].notna() & df["first_response_at"].notna()
    result = pd.Series(np.nan, index=df.index)
    result[mask] = (df.loc[mask, "resolved_at"] - df.loc[mask, "first_response_at"]).dt.total_seconds() / 3600
    return result


def compute_first_response_minutes(df):
    return (df["first_response_at"] - df["created_at"]).dt.total_seconds() / 60


def compute_sla_breach(df):
    fr_minutes = compute_first_response_minutes(df)
    targets = {"chat": 15, "voice": 120, "social": 240, "email": 480}
    target_minutes = df["channel"].map(targets)
    return fr_minutes > target_minutes


def agent_performance(df, agent_lookup):
    df = df.copy()
    df["handle_time_hrs"] = compute_handle_time_hours(df)
    df["sla_breach"] = compute_sla_breach(df)

    csat_valid = df[df["csat_score"].notna()]

    csat_agg = csat_valid.groupby("agent_id").agg(
        csat_mean=("csat_score", "mean"),
        csat_count=("csat_score", "count"),
    )

    handle_agg = df[df["handle_time_hrs"].notna() & (df["handle_time_hrs"] >= 0)].groupby("agent_id").agg(
        avg_handle_time_hrs=("handle_time_hrs", "mean"),
        median_handle_time_hrs=("handle_time_hrs", "median"),
    )

    ticket_agg = df.groupby("agent_id").agg(
        ticket_count=("ticket_id", "count"),
        breach_count=("sla_breach", "sum"),
        replacement_count=("replacement_issued", lambda x: (x == "Y").sum()),
    )

    perf = ticket_agg.join(csat_agg, how="left").join(handle_agg, how="left")

    if agent_lookup is not None:
        perf = perf.join(agent_lookup[["name", "team", "site", "tier"]], how="left")

    perf["csat_mean"] = perf["csat_mean"].round(2)
    perf["avg_handle_time_hrs"] = perf["avg_handle_time_hrs"].round(2)
    perf["median_handle_time_hrs"] = perf["median_handle_time_hrs"].round(2)
    perf["breach_rate"] = (perf["breach_count"] / perf["ticket_count"]).round(3)

    return perf.reset_index()


def overall_kpis(df):
    resolved = df[df["status"].isin(["resolved", "closed"])]
    csat_valid = resolved[resolved["csat_score"].notna()]
    handle_times = compute_handle_time_hours(resolved)
    valid_ht = handle_times[handle_times.notna() & (handle_times >= 0)]

    return {
        "total_tickets": len(df),
        "resolved_tickets": len(resolved),
        "num_agents": df["agent_id"].nunique(),
        "overall_csat": round(csat_valid["csat_score"].mean(), 2),
        "csat_response_rate": round(len(csat_valid) / len(resolved) * 100, 1),
        "avg_handle_time_hrs": round(valid_ht.mean(), 2),
        "median_handle_time_hrs": round(valid_ht.median(), 2),
        "open_tickets": len(df[df["status"].isin(["open", "pending"])]),
        "total_replacements": int((df["replacement_issued"] == "Y").sum()),
        "total_refund_amount": round(df["refund_amount_inr"].sum(), 0),
    }


def monthly_trend(df):
    df = df.copy()
    df["month"] = df["created_at"].dt.to_period("M")
    csat_valid = df[df["csat_score"].notna()]

    csat_trend = csat_valid.groupby("month")["csat_score"].mean().reset_index()
    csat_trend.columns = ["month", "avg_csat"]

    df["handle_time_hrs"] = compute_handle_time_hours(df)
    ht_valid = df[df["handle_time_hrs"].notna() & (df["handle_time_hrs"] >= 0)]
    ht_trend = ht_valid.groupby("month")["handle_time_hrs"].mean().reset_index()
    ht_trend.columns = ["month", "avg_handle_time_hrs"]

    vol_trend = df.groupby("month")["ticket_id"].count().reset_index()
    vol_trend.columns = ["month", "ticket_count"]

    result = vol_trend.merge(csat_trend, on="month", how="left").merge(ht_trend, on="month", how="left")
    result["month"] = result["month"].astype(str)
    return result
