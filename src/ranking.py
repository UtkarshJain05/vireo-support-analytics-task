import numpy as np
from scipy import stats


MINIMUM_CSAT_RESPONSES = 10
CSAT_WEIGHT = 0.6
HANDLE_TIME_WEIGHT = 0.4


def compute_bottom_10(agent_perf_df):
    df = agent_perf_df.copy()

    tier1 = df[df["tier"] == 1].copy()
    tier2_ids = set(df[df["tier"] == 2]["agent_id"].tolist())

    eligible = tier1[tier1["csat_count"] >= MINIMUM_CSAT_RESPONSES].copy()

    csat_values = eligible["csat_mean"].values
    ht_values = eligible["avg_handle_time_hrs"].values

    eligible["csat_percentile"] = eligible["csat_mean"].rank(pct=True)

    eligible["ht_percentile"] = 1 - eligible["avg_handle_time_hrs"].rank(pct=True)

    eligible["composite_score"] = (
        CSAT_WEIGHT * eligible["csat_percentile"]
        + HANDLE_TIME_WEIGHT * eligible["ht_percentile"]
    ).round(3)

    eligible = eligible.sort_values("composite_score", ascending=True)
    eligible["rank"] = range(1, len(eligible) + 1)

    bottom_10_ids = set(eligible.head(10)["agent_id"].tolist())

    df["review_flag"] = False
    df.loc[df["agent_id"].isin(bottom_10_ids), "review_flag"] = True

    df["tier2_excluded"] = df["agent_id"].isin(tier2_ids)

    df["insufficient_data"] = (df["csat_count"] < MINIMUM_CSAT_RESPONSES) & (~df["tier2_excluded"])

    eligible_with_flag = eligible.copy()
    eligible_with_flag["review_flag"] = eligible_with_flag["agent_id"].isin(bottom_10_ids)

    return df, eligible_with_flag, {
        "csat_weight": CSAT_WEIGHT,
        "handle_time_weight": HANDLE_TIME_WEIGHT,
        "min_csat_responses": MINIMUM_CSAT_RESPONSES,
        "tier2_excluded_count": len(tier2_ids),
        "eligible_count": len(eligible),
        "total_agents": len(df),
    }
