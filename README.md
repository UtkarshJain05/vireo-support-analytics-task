# 🎧 Vireo Support Analytics Dashboard

A streamlined, data-driven Streamlit dashboard designed to identify underperforming customer support agents for retraining, calculate SLA breaches, and estimate the business cost of unnecessary product replacements.

## 🚀 Quickstart

1. **Install Dependencies:**
   `ash
   pip install -r requirements.txt
   `
2. **Add API Key (Optional but Recommended):**
   Copy .env.example to .env and add your free Groq API key for AI-powered insights.
   `ash
   GROQ_API_KEY=your_key_here
   `
3. **Run the Dashboard:**
   `ash
   streamlit run app.py
   `

## 📊 Core Methodology

*   **CSAT Calculation:** Excludes blank scores (per Policy §8).
*   **Handle Time:** Measures irst_response_at to 
esolved_at. **Crucial Fix:** Legacy UTC timestamps were converted to IST (+5:30), eliminating 2,309 impossible negative handle times.
*   **Bottom-10 Ranking:** 60% CSAT Percentile + 40% Handle Time Percentile. 
    *   *Exclusions:* Tier 2 agents (Escalations/Warranty) are excluded from volume metric comparisons (per Policy §6). Agents with <10 reviews are excluded for statistical relevance.
*   **Queue Bias Warning:** 8 of the 10 flagged agents are in Logistics/Returns. These queues inherently receive the hardest cases, so scores reflect queue difficulty, not just skill.

## 🤖 AI Integration

We use **Groq (GPT OSS 120B)** for rapid, cost-free unstructured text analysis.
*   **What it does:** Extracts themes, sentiment, and training gaps from bottom-10 agent tickets.
*   **What it DOES NOT do:** All financial, CSAT, and ranking metrics are strictly deterministic (Pandas). No numbers are hallucinated.
*   **Fallback:** If the API key is missing or rate-limited, a local rule-based keyword matcher runs instead.

## 💰 Business Impact Goal

*   **Objective:** Reduce the massive post-festive spike in product replacement rates (from 9.6% baseline to 22.1%).
*   **Financial Impact:** Returning to the baseline saves ~**₹8.5 Lakh quarterly**.
*   *(Note: Replacement cost calculated exactly as Unit Cost + ₹340 logistics, overriding the incorrect ₹2,500 estimate in the email thread).*

## 🧪 Testing

Run pytest tests/test_metrics.py to execute the 8-test validation suite verifying:
*   Timezone fixes (0 negative handle times).
*   Correct Tier-2 exclusions.
*   Deterministic SLA breach counts.
*   Perfect ticket aggregation sums.

## 📝 What Was Intentionally Left Out

*   **orders.csv (Lot Codes):** Finance requested lot codes, but the primary mandate was an *agent retraining* dashboard. Deep-diving into manufacturing defects was deemed out of scope.
*   **customers.csv (Demographics):** Irrelevant to individual agent performance metrics.
