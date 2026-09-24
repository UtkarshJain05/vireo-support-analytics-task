# 🎧 Vireo Support Analytics Dashboard

A streamlined, data-driven Streamlit dashboard designed to identify underperforming customer support agents for retraining, calculate SLA breaches, and estimate the business cost of unnecessary product replacements.

## 🛠️ HOW TO RUN THE PROJECT (Step-by-Step)

Follow these exact steps to run the dashboard on a clean machine:

1. **Clone or Download the Repository:**
   Ensure your terminal is in the project root folder.

2. **Create a Virtual Environment (Recommended):**
   `ash
   python -m venv venv
   
   # On Windows:
   venv\\Scripts\\activate
   
   # On Mac/Linux:
   source venv/bin/activate
   `

3. **Install the Required Packages:**
   `ash
   pip install -r requirements.txt
   `

4. **Configure the API Key (Required for AI Insights):**
   - Go to https://console.groq.com/keys to get a free API key.
   - In the project root, create a file named exactly .env
   - Add this single line to the file:
     GROQ_API_KEY=your_actual_api_key_here

5. **Start the Dashboard:**
   `ash
   streamlit run app.py
   `
   *The dashboard will automatically open in your web browser at http://localhost:8501*

---

## 📊 Analytical Methodology

### CSAT & Handle Time
*   **CSAT:** Excludes blank scores (per Policy §8).
*   **Handle Time:** Measures irst_response_at to 
esolved_at. **Crucial Fix:** Legacy UTC timestamps were converted to IST (+5:30), eliminating 2,309 impossible negative handle times.

### Bottom-10 Methodology
**Composite score = 60% CSAT percentile + 40% Handle Time percentile (inverted)**

**Exclusions:**
*   **Tier 2 agents (Escalations & Warranty):** Policy section 6 explicitly states Tier 2 agents handle multi-touch cases and are not to be compared with Tier 1 on volume metrics.
*   **Agents with <10 reviews:** Excluded for statistical stability.

**Queue Bias Caveat:** 
8 of the 10 flagged agents are in Logistics and Returns Desk. They're the bottom 10 under the defined performance metric, but I wouldn't interpret that as proof that they're individually the worst performers. Eight are in Logistics and Returns, where the case mix is inherently more difficult. I'd use this list as a retraining review cohort rather than as a punitive ranking.

## 🤖 AI Integration

We use the **Groq API with GPT-OSS 120B model** for rapid, cost-free unstructured text analysis.
*   **What it does:** Extracts themes, sentiment, and training gaps from bottom-10 agent tickets.
*   **What it DOES NOT do:** All financial, CSAT, and ranking metrics are strictly deterministic (Pandas).
*   **Fallback:** If the API key is missing or rate-limited, a local rule-based keyword matcher runs instead.

## 💰 Business Impact Goal

*   **Objective:** Reduce the massive post-festive spike in product replacement rates (from 9.6% baseline to 22.1%).
*   **Financial Impact:** Returning to the baseline saves ~**₹8.5 Lakh quarterly**.
*   **Replacement Cost Formula:** Unit Cost + ₹340 logistics (overriding the incorrect ₹2,500 estimate in the email thread based on Policy §5).

## 🧪 Validation & Evaluation

**Deterministic Analytics (	ests/test_metrics.py):**
8 tests covering data loading, negative handle times, CSAT range, blank CSAT handling, aggregation, bottom-10 exclusions, SLA logic, and CSAT spot checks.

**AI Classification:**
The keyword fallback has limited accuracy on informal and misspelled text. The LLM path is intended to provide more context-aware classification, but its accuracy was not independently benchmarked in this evaluation.

## ⚠️ Limitations & Scope Decisions

### What Was Intentionally Left Out
*   **Per-product / Lot-code Analysis (orders.csv):** Finance requested lot codes, but the primary mandate was an *agent retraining* dashboard. Deep-diving into manufacturing defects was deemed out of scope.
*   **Customer Segmentation (customers.csv):** Irrelevant to individual agent performance metrics.
*   **Cloud Deployment:** Cloud deployment was intentionally left out to stay within the assignment scope.
*   **Authentication & Live Monitoring:** This is a batch analytics tool designed for take-home assessment constraints.
