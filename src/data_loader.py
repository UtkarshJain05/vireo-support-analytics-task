import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_tickets():
    df = pd.read_csv(os.path.join(DATA_DIR, "tickets.csv"))
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["first_response_at"] = pd.to_datetime(df["first_response_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"])

    legacy_mask = df["source_system"] == "legacy_fd"
    df.loc[legacy_mask, "resolved_at"] = df.loc[legacy_mask, "resolved_at"] + pd.Timedelta(hours=5, minutes=30)

    return df


def load_agents():
    df = pd.read_csv(os.path.join(DATA_DIR, "agents.csv"))
    return df


def load_products():
    df = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    return df


def get_agent_lookup(agents_df):
    latest = agents_df.sort_values("from_date").drop_duplicates(subset="agent_id", keep="last")
    return latest.set_index("agent_id")[["name", "site", "team", "shift", "tier"]]


def get_resolved_tickets(tickets_df):
    return tickets_df[tickets_df["status"].isin(["resolved", "closed"])].copy()
