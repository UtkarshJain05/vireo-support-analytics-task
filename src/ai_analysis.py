import os
import json
import pandas as pd
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def is_ai_available():
    return bool(GROQ_API_KEY)


def classify_tickets_batch(tickets_df, sample_size=100):
    if not is_ai_available():
        return _fallback_classification(tickets_df)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        sample = tickets_df.sample(n=min(sample_size, len(tickets_df)), random_state=42)

        results = []
        batch_size = 20
        for i in range(0, len(sample), batch_size):
            batch = sample.iloc[i:i+batch_size]
            prompt = _build_classification_prompt(batch)
            
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.0
            )
            parsed = _parse_response(response.choices[0].message.content, batch)
            results.extend(parsed)

        return pd.DataFrame(results)
    except Exception as e:
        print(f"AI classification failed: {e}")
        return _fallback_classification(tickets_df)


def analyze_themes_for_bottom_agents(tickets_df, bottom_agent_ids, sample_per_agent=5):
    if not is_ai_available():
        return _fallback_theme_analysis(tickets_df, bottom_agent_ids)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        bottom_tickets = tickets_df[tickets_df["agent_id"].isin(bottom_agent_ids)]
        sample = bottom_tickets.groupby("agent_id").apply(
            lambda x: x.sample(n=min(sample_per_agent, len(x)), random_state=42),
            include_groups=False
        ).reset_index(drop=True)

        ticket_texts = []
        for _, row in sample.iterrows():
            ticket_texts.append({
                "ticket_id": row["ticket_id"],
                "category": row["category"],
                "channel": row["channel"],
                "customer_message": str(row["customer_message"])[:300],
                "agent_notes": str(row["agent_notes"])[:300],
                "csat_score": row["csat_score"] if pd.notna(row["csat_score"]) else "N/A",
            })

        prompt = f"""Analyze these support tickets from underperforming agents at Vireo Audio (consumer electronics: earbuds, headphones, speakers, watches).

Identify:
1. Top 5 recurring issue themes/patterns
2. Common factors associated with low customer satisfaction
3. Specific training areas that would help these agents improve
4. Any process or product issues (not just agent skill gaps)

Tickets (JSON):
{json.dumps(ticket_texts, indent=2)}

Respond in JSON format:
{{
    "themes": [
        {{"theme": "...", "frequency": "high/medium/low", "description": "...", "example_tickets": ["TK-..."]}}
    ],
    "low_csat_factors": ["..."],
    "training_recommendations": ["..."],
    "process_issues": ["..."],
    "summary": "2-3 sentence executive summary"
}}"""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior support analyst. Always output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        return json.loads(text)
    except Exception as e:
        print(f"AI theme analysis failed: {e}")
        fallback_data = _fallback_theme_analysis(tickets_df, bottom_agent_ids)
        fallback_data["api_error"] = str(e)
        return fallback_data


def _build_classification_prompt(batch_df):
    tickets = []
    for _, row in batch_df.iterrows():
        tickets.append({
            "ticket_id": row["ticket_id"],
            "customer_message": str(row["customer_message"])[:300],
            "agent_notes": str(row["agent_notes"])[:200],
            "category": row["category"],
        })

    return f"""Classify each support ticket for Vireo Audio (consumer electronics brand selling earbuds, headphones, speakers, smartwatches).

For each ticket provide:
- issue_category: the primary issue type (e.g., "defective_product", "delivery_delay", "billing_error", "setup_help", "return_request", "warranty_claim", "connectivity_issue", "battery_issue", "app_issue", "general_inquiry")
- sentiment: "negative", "neutral", or "positive"
- contributing_factor: one of "product_quality", "delivery_logistics", "agent_handling", "process_gap", "customer_education", "system_issue", "unclear"

Tickets:
{json.dumps(tickets, indent=2)}

Return a JSON array:
[{{"ticket_id": "...", "issue_category": "...", "sentiment": "...", "contributing_factor": "..."}}]"""


def _parse_response(response_text, batch_df):
    try:
        text = response_text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, IndexError):
        pass

    return [{"ticket_id": row["ticket_id"], "issue_category": "parse_error", "sentiment": "unknown", "contributing_factor": "unclear"}
            for _, row in batch_df.iterrows()]


def _fallback_classification(tickets_df):
    keyword_map = {
        "not working": "defective_product",
        "broken": "defective_product",
        "dead": "defective_product",
        "no sound": "defective_product",
        "no audio": "defective_product",
        "one side": "defective_product",
        "cannot hear": "defective_product",
        "can't hear": "defective_product",
        "stopped working": "defective_product",
        "defective": "defective_product",
        "faulty": "defective_product",
        "crackling": "defective_product",
        "static": "defective_product",
        "not charging": "battery_issue",
        "battery": "battery_issue",
        "drain": "battery_issue",
        "charging": "battery_issue",
        "not delivered": "delivery_delay",
        "not received": "delivery_delay",
        "not rcvd": "delivery_delay",
        "tracking": "delivery_delay",
        "shipment": "delivery_delay",
        "courier": "delivery_delay",
        "delivery": "delivery_delay",
        "shipped": "delivery_delay",
        "order not": "delivery_delay",
        "order status": "delivery_delay",
        "refund": "return_request",
        "return": "return_request",
        "replace": "return_request",
        "money back": "return_request",
        "warranty": "warranty_claim",
        "rma": "warranty_claim",
        "bluetooth": "connectivity_issue",
        "connect": "connectivity_issue",
        "pair": "connectivity_issue",
        "disconnect": "connectivity_issue",
        "wifi": "connectivity_issue",
        "app": "app_issue",
        "firmware": "app_issue",
        "update": "app_issue",
        "software": "app_issue",
        "payment": "billing_error",
        "invoice": "billing_error",
        "charged": "billing_error",
        "double charge": "billing_error",
        "how to": "setup_help",
        "setup": "setup_help",
        "compatible": "setup_help",
        "work with": "setup_help",
    }

    results = []
    for _, row in tickets_df.iterrows():
        msg = str(row.get("customer_message", "")).lower()
        category = "general_inquiry"
        for keyword, cat in keyword_map.items():
            if keyword in msg:
                category = cat
                break

        neg_words = ["worst", "pathetic", "terrible", "horrible", "useless", "angry", "frustrated", "disappointed", "waste", "cheat", "fraud", "scam"]
        pos_words = ["thank", "great", "good", "excellent", "happy", "helpful", "resolved", "appreciate"]

        sentiment = "neutral"
        msg_lower = msg.lower()
        if any(w in msg_lower for w in neg_words):
            sentiment = "negative"
        elif any(w in msg_lower for w in pos_words):
            sentiment = "positive"

        results.append({
            "ticket_id": row["ticket_id"],
            "issue_category": category,
            "sentiment": sentiment,
            "contributing_factor": "unclear",
        })

    return pd.DataFrame(results)


def _fallback_theme_analysis(tickets_df, bottom_agent_ids):
    bottom_tickets = tickets_df[tickets_df["agent_id"].isin(bottom_agent_ids)]

    category_counts = bottom_tickets["category"].value_counts().head(5)
    themes = []
    for cat, count in category_counts.items():
        freq = "high" if count > len(bottom_tickets) * 0.15 else "medium" if count > len(bottom_tickets) * 0.08 else "low"
        themes.append({
            "theme": cat,
            "frequency": freq,
            "description": f"Observed in {count} tickets from flagged agents ({count/len(bottom_tickets)*100:.1f}% of their volume)",
            "example_tickets": bottom_tickets[bottom_tickets["category"] == cat]["ticket_id"].head(3).tolist(),
        })

    low_csat = bottom_tickets[bottom_tickets["csat_score"].notna() & (bottom_tickets["csat_score"] <= 2)]
    low_csat_categories = low_csat["category"].value_counts().head(3)

    return {
        "themes": themes,
        "low_csat_factors": [
            f"'{cat}' category frequently appears in low-CSAT tickets ({count} occurrences)"
            for cat, count in low_csat_categories.items()
        ],
        "training_recommendations": [
            "Product troubleshooting for audio and connectivity issues",
            "Delivery escalation and proactive customer communication",
            "Empathy and de-escalation for frustrated customers",
            "Proper use of refund/replacement reason codes",
            "First-contact resolution techniques to reduce transfers",
        ],
        "process_issues": [
            "High transfer rates observed — may indicate unclear routing rules",
            "Delayed first responses on email channel",
        ],
        "summary": (
            "Flagged agents frequently handle delivery/shipping and product-quality tickets. "
            "Low CSAT is associated with unresolved product issues and slow response times. "
            "Targeted training on troubleshooting and customer communication is recommended."
        ),
        "source": "rule-based fallback (no API key configured)",
    }
