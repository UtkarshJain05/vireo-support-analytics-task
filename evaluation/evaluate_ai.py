import sys
import os
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_tickets, load_agents, load_products, get_agent_lookup, get_resolved_tickets
from src.ai_analysis import _fallback_classification, is_ai_available, classify_tickets_batch


MANUAL_LABELS = [
    {"ticket_id": "TK-240001", "expected_category": "defective_product", "expected_sentiment": "negative"},
    {"ticket_id": "TK-240002", "expected_category": "delivery_delay", "expected_sentiment": "negative"},
    {"ticket_id": "TK-240005", "expected_category": "defective_product", "expected_sentiment": "negative"},
    {"ticket_id": "TK-240006", "expected_category": "delivery_delay", "expected_sentiment": "neutral"},
    {"ticket_id": "TK-240007", "expected_category": "delivery_delay", "expected_sentiment": "neutral"},
]


def evaluate_classification(tickets_df, method_name="fallback"):
    labeled_ids = [l["ticket_id"] for l in MANUAL_LABELS]
    sample = tickets_df[tickets_df["ticket_id"].isin(labeled_ids)].copy()

    if method_name == "fallback":
        predictions = _fallback_classification(sample)
    elif method_name == "ai":
        if not is_ai_available():
            print("SKIP: AI evaluation skipped — no API key")
            return None
        predictions = classify_tickets_batch(sample, sample_size=len(sample))
    else:
        return None

    manual_df = pd.DataFrame(MANUAL_LABELS)
    pred_df = predictions if isinstance(predictions, pd.DataFrame) else pd.DataFrame(predictions)

    merged = manual_df.merge(pred_df, on="ticket_id", how="inner")

    if len(merged) == 0:
        print(f"WARNING: No matches found between manual labels and predictions for {method_name}")
        return None

    category_match = (merged["expected_category"] == merged["issue_category"]).sum()
    sentiment_match = (merged["expected_sentiment"] == merged["sentiment"]).sum()

    category_accuracy = category_match / len(merged)
    sentiment_accuracy = sentiment_match / len(merged)

    results = {
        "method": method_name,
        "sample_size": len(merged),
        "category_accuracy": round(category_accuracy, 3),
        "sentiment_accuracy": round(sentiment_accuracy, 3),
        "category_matches": int(category_match),
        "sentiment_matches": int(sentiment_match),
        "details": [],
    }

    for _, row in merged.iterrows():
        results["details"].append({
            "ticket_id": row["ticket_id"],
            "expected_category": row["expected_category"],
            "predicted_category": row["issue_category"],
            "category_match": row["expected_category"] == row["issue_category"],
            "expected_sentiment": row["expected_sentiment"],
            "predicted_sentiment": row["sentiment"],
            "sentiment_match": row["expected_sentiment"] == row["sentiment"],
        })

    return results


def run_broader_evaluation(tickets_df, sample_size=50):
    sample = tickets_df.sample(n=min(sample_size, len(tickets_df)), random_state=42)
    predictions = _fallback_classification(sample)

    if isinstance(predictions, pd.DataFrame):
        pred_df = predictions
    else:
        pred_df = pd.DataFrame(predictions)

    stats = {
        "total_classified": len(pred_df),
        "category_distribution": pred_df["issue_category"].value_counts().to_dict(),
        "sentiment_distribution": pred_df["sentiment"].value_counts().to_dict(),
        "contributing_factor_distribution": pred_df["contributing_factor"].value_counts().to_dict() if "contributing_factor" in pred_df.columns else {},
        "parse_errors": int((pred_df["issue_category"] == "parse_error").sum()) if "issue_category" in pred_df.columns else 0,
    }

    return stats


if __name__ == "__main__":
    print("=" * 60)
    print("AI Classification Evaluation")
    print("=" * 60)

    tickets = load_tickets()

    print("\n1. Evaluating fallback (keyword-based) classification:")
    fallback_results = evaluate_classification(tickets, "fallback")
    if fallback_results:
        print(f"   Category accuracy: {fallback_results['category_accuracy']*100:.1f}% ({fallback_results['category_matches']}/{fallback_results['sample_size']})")
        print(f"   Sentiment accuracy: {fallback_results['sentiment_accuracy']*100:.1f}% ({fallback_results['sentiment_matches']}/{fallback_results['sample_size']})")
        print("\n   Details:")
        for d in fallback_results["details"]:
            cat_mark = "OK" if d["category_match"] else "X"
            sent_mark = "OK" if d["sentiment_match"] else "X"
            print(f"   {d['ticket_id']}: category {cat_mark} (exp={d['expected_category']}, pred={d['predicted_category']}), sentiment {sent_mark} (exp={d['expected_sentiment']}, pred={d['predicted_sentiment']})")

    print("\n2. Evaluating AI (Gemini) classification:")
    ai_results = evaluate_classification(tickets, "ai")
    if ai_results:
        print(f"   Category accuracy: {ai_results['category_accuracy']*100:.1f}% ({ai_results['category_matches']}/{ai_results['sample_size']})")
        print(f"   Sentiment accuracy: {ai_results['sentiment_accuracy']*100:.1f}% ({ai_results['sentiment_matches']}/{ai_results['sample_size']})")

    print("\n3. Broader fallback classification stats (50-ticket sample):")
    broad_stats = run_broader_evaluation(tickets)
    print(f"   Total classified: {broad_stats['total_classified']}")
    print(f"   Category distribution: {json.dumps(broad_stats['category_distribution'], indent=4)}")
    print(f"   Sentiment distribution: {json.dumps(broad_stats['sentiment_distribution'], indent=4)}")
    if broad_stats["parse_errors"] > 0:
        print(f"   Parse errors: {broad_stats['parse_errors']}")

    print("\n" + "=" * 60)
    print("Evaluation complete")
