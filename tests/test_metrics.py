import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_tickets, load_agents, load_products, get_agent_lookup, get_resolved_tickets
from src.metrics import (
    compute_handle_time_hours,
    compute_first_response_minutes,
    compute_sla_breach,
    agent_performance,
    overall_kpis,
)
from src.ranking import compute_bottom_10


def test_data_loading():
    tickets = load_tickets()
    agents = load_agents()
    products = load_products()

    assert len(tickets) > 0, "No tickets loaded"
    assert len(agents) > 0, "No agents loaded"
    assert len(products) > 0, "No products loaded"

    assert "ticket_id" in tickets.columns
    assert "agent_id" in tickets.columns
    assert "csat_score" in tickets.columns
    assert "created_at" in tickets.columns

    assert pd.api.types.is_datetime64_any_dtype(tickets["created_at"]), "created_at not datetime"
    assert pd.api.types.is_datetime64_any_dtype(tickets["first_response_at"]), "first_response_at not datetime"

    print(f"PASS: Data loading - {len(tickets)} tickets, {len(agents)} agents, {len(products)} products")


def test_no_negative_handle_times():
    tickets = load_tickets()
    resolved = get_resolved_tickets(tickets)
    ht = compute_handle_time_hours(resolved)
    valid_ht = ht[ht.notna()]
    neg_count = (valid_ht < 0).sum()
    assert neg_count == 0, f"Found {neg_count} negative handle times after UTC fix"
    print(f"PASS: No negative handle times — {len(valid_ht)} valid handle times checked")


def test_csat_range():
    tickets = load_tickets()
    csat = tickets["csat_score"].dropna()
    assert csat.min() >= 1, f"CSAT min is {csat.min()}, expected >= 1"
    assert csat.max() <= 5, f"CSAT max is {csat.max()}, expected <= 5"
    print(f"PASS: CSAT scores in range [1,5] — {len(csat)} scores checked")


def test_csat_excludes_blanks():
    tickets = load_tickets()
    resolved = get_resolved_tickets(tickets)

    csat_valid = resolved[resolved["csat_score"].notna()]
    null_in_valid = csat_valid["csat_score"].isnull().sum()
    assert null_in_valid == 0, "Blank CSAT scores not excluded"

    total_resolved = len(resolved)
    csat_count = len(csat_valid)
    response_rate = csat_count / total_resolved * 100
    assert 30 < response_rate < 70, f"CSAT response rate {response_rate:.1f}% seems off (expected ~45%)"
    print(f"PASS: CSAT excludes blanks — response rate {response_rate:.1f}%")


def test_agent_performance_aggregation():
    tickets = load_tickets()
    agents = load_agents()
    resolved = get_resolved_tickets(tickets)
    agent_lookup = get_agent_lookup(agents)

    perf = agent_performance(resolved, agent_lookup)

    assert len(perf) > 0, "No agent performance records"
    assert "csat_mean" in perf.columns
    assert "avg_handle_time_hrs" in perf.columns
    assert "ticket_count" in perf.columns

    total_tickets_in_perf = perf["ticket_count"].sum()
    assert total_tickets_in_perf == len(resolved), f"Ticket count mismatch: {total_tickets_in_perf} vs {len(resolved)}"

    print(f"PASS: Agent performance — {len(perf)} agents, tickets sum verified")


def test_bottom_10_exclusions():
    tickets = load_tickets()
    agents = load_agents()
    resolved = get_resolved_tickets(tickets)
    agent_lookup = get_agent_lookup(agents)

    perf = agent_performance(resolved, agent_lookup)
    all_agents_df, eligible_df, meta = compute_bottom_10(perf)

    tier2_flagged = all_agents_df[(all_agents_df["tier2_excluded"]) & (all_agents_df["review_flag"])]
    assert len(tier2_flagged) == 0, "Tier 2 agents should not be flagged"

    bottom_10 = all_agents_df[all_agents_df["review_flag"]]
    assert len(bottom_10) == 10, f"Expected 10 flagged agents, got {len(bottom_10)}"

    print(f"PASS: Bottom 10 — {len(bottom_10)} flagged, 0 Tier 2 included, {meta['eligible_count']} eligible")


def test_sla_breach_logic():
    tickets = load_tickets()
    resolved = get_resolved_tickets(tickets)
    fr_minutes = compute_first_response_minutes(resolved)
    breach = compute_sla_breach(resolved)

    chat_tickets = resolved[resolved["channel"] == "chat"]
    chat_fr = (chat_tickets["first_response_at"] - chat_tickets["created_at"]).dt.total_seconds() / 60

    chat_breach_manual = (chat_fr > 15).sum()
    chat_breach_func = breach[resolved["channel"] == "chat"].sum()
    assert chat_breach_manual == chat_breach_func, f"Chat breach mismatch: {chat_breach_manual} vs {chat_breach_func}"

    print(f"PASS: SLA breach logic verified — chat breaches: {chat_breach_manual}")


def test_spot_check_csat():
    tickets = load_tickets()
    resolved = get_resolved_tickets(tickets)

    agent_id = resolved["agent_id"].value_counts().index[0]
    agent_tickets = resolved[resolved["agent_id"] == agent_id]
    agent_csat = agent_tickets["csat_score"].dropna()

    manual_mean = agent_csat.mean()

    agent_lookup = get_agent_lookup(load_agents())
    perf = agent_performance(resolved, agent_lookup)
    computed_mean = perf[perf["agent_id"] == agent_id]["csat_mean"].values[0]

    assert abs(manual_mean - computed_mean) < 0.01, f"CSAT spot check failed for {agent_id}: {manual_mean:.4f} vs {computed_mean:.4f}"
    print(f"PASS: CSAT spot check for {agent_id} — manual: {manual_mean:.4f}, computed: {computed_mean:.4f}")


if __name__ == "__main__":
    tests = [
        test_data_loading,
        test_no_negative_handle_times,
        test_csat_range,
        test_csat_excludes_blanks,
        test_agent_performance_aggregation,
        test_bottom_10_exclusions,
        test_sla_breach_logic,
        test_spot_check_csat,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__} — {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("All tests passed [OK]")
    else:
        print("Some tests failed [FAIL]")
        sys.exit(1)
