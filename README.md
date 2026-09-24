# Vireo Audio — Support Analytics Dashboard

An AI-assisted support analytics tool built for Vireo Audio's Head of Customer Experience. Measures CSAT and handle time per agent, flags the bottom 10 agents for review, identifies ticket themes via AI, and quantifies a business goal with quarterly financial impact.

---

## Business Problem

Vireo Audio's CSAT has been sliding since the festive season (Q4 2025). Priya Raman needs to know which agents to retrain with a Q3 training budget of Rs 4 lakh. She needs:
- CSAT and handle time per agent
- The bottom 10 agents flagged for review
- Actionable themes from ticket data
- A concrete business goal stated in rupees

## Solution

A Streamlit dashboard that:
1. Computes CSAT and handle time per agent from 11,750 tickets (Jan 2025 - Jun 2026)
2. Ranks Tier 1 agents using a composite score (60% CSAT percentile + 40% handle time percentile) and flags the bottom 10
3. Uses Groq (GPT OSS 120B) (or keyword-based fallback) to classify tickets and surface retraining themes
4. Quantifies a business goal: reduce replacement rate from 22% to the pre-festive baseline of ~10%, worth approximately Rs 8.5 lakh per quarter

## Architecture

```
app.py                  Streamlit dashboard (single entry point)
src/
  data_loader.py        CSV loading + UTC-to-IST fix for legacy tickets
  metrics.py            CSAT, handle time, SLA breach, agent aggregation
  ranking.py            Bottom-10 composite ranking (Tier 2 excluded)
  business_impact.py    Replacement cost analysis, quarterly savings
  ai_analysis.py        LLM ticket classification + fallback
tests/
  test_metrics.py       8 validation tests
evaluation/
  evaluate_ai.py        AI classification accuracy evaluation
outputs/
  memo.md               One-page memo for Priya Raman
data/
  tickets.csv           11,750 support tickets
  agents.csv            44-agent roster
  products.csv          14 product SKUs
```

## Technology Stack

- **Python 3.10+**
- **Pandas** — data manipulation and metric computation
- **Streamlit** — interactive dashboard
- **Plotly** — charts and visualizations
- **Groq (GPT OSS 120B)** — ticket classification and theme analysis (optional; keyword-based fallback runs without API key)
- **SciPy** — statistical functions

## Setup Instructions (Clean Machine)

### Prerequisites
- Python 3.10 or later
- pip

### Steps

```bash
# 1. Clone or copy this directory
cd vireo-support-analytics

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up AI features
copy .env.example .env
# Edit .env and add your Groq (GPT OSS 120B) API key
# Get a free key at https://console.groq.com/keys

# 5. Run the dashboard
streamlit run app.py

# 6. Run tests
python tests/test_metrics.py

# 7. Run AI evaluation
python evaluation/evaluate_ai.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Groq (GPT OSS 120B) API key for LLM-powered ticket analysis. Without it, the app uses a keyword-based fallback. |

## How to Run

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

## Analytical Methodology

### CSAT
- Source: `csat_score` column in tickets.csv (1-5 scale)
- Blank scores = no survey response, excluded from averages (not treated as zero) per support-policy.pdf section 8
- Overall CSAT: 3.33 (44.2% response rate)
- Aggregated per agent on resolved/closed tickets only

### Handle Time
- Definition: `first_response_at` to `resolved_at` (per support-policy.pdf section 10)
- **Critical fix:** Legacy tickets (source_system = "legacy_fd") have `resolved_at` in UTC while all other timestamps are IST. Adding +5:30 to legacy resolved_at eliminates all 2,309 negative handle times.
- Open/pending tickets excluded (no resolved_at)

### SLA Breach
- Targets per support-policy.pdf section 3: chat 15 min, voice 2 hrs, social 4 hrs, email 8 hrs
- Breach = first_response_at - created_at exceeds channel target
- Each breach costs Rs 350 in automatic store credits

## Bottom-10 Methodology

**Composite Score = 60% CSAT Percentile + 40% Handle Time Percentile (inverted)**

Rationale:
- CSAT is weighted higher because it directly reflects customer satisfaction, which is Priya's primary concern
- Handle time is included because excessively long resolution times also indicate process issues
- Handle time percentile is inverted (lower is worse) so that longer times reduce the score

**Exclusions:**
- **Tier 2 agents (6 agents, Escalations & Warranty):** Policy section 6 explicitly states Tier 2 agents handle multi-touch warranty cases and "are not to be compared with Tier 1 on volume metrics." Their structurally longer handle times and harder cases would unfairly penalize them.
- **Agents with fewer than 10 CSAT responses:** Excluded for statistical stability. A single low score on a small sample would be misleading.

**Result:** 38 eligible Tier 1 agents ranked; bottom 10 flagged.

**Important caveat (from Neha Kulkarni's email):** 8 of the 10 flagged agents are in Logistics and Returns Desk. These teams receive the most difficult cases (lost deliveries, returns, angry customers) by design. Their lower scores partly reflect queue difficulty, not solely individual performance. The dashboard notes this explicitly.

## AI Usage

AI is used **only** for unstructured text analysis where Pandas cannot help:
- **Ticket classification:** Categorizing customer messages into issue types, sentiment, and contributing factors
- **Theme analysis:** Identifying recurring patterns in bottom-10 agents' tickets and suggesting training areas

AI is **not** used for:
- CSAT calculations (deterministic)
- Handle time calculations (deterministic)
- Agent aggregation or ranking (deterministic)
- Financial calculations (deterministic)

**Model:** Groq (GPT OSS 120B) 2.0 Flash (chosen for low cost and speed)
**Fallback:** If no API key is provided, a keyword-based classifier runs entirely locally.

## Validation / Evaluation

### Deterministic Analytics (tests/test_metrics.py — 8 tests)
1. **Data loading** — verifies all CSVs load with correct columns and datetime types
2. **No negative handle times** — confirms the UTC-to-IST fix eliminates all 2,309 legacy anomalies
3. **CSAT range** — all scores are between 1 and 5
4. **CSAT excludes blanks** — response rate matches expected ~45%
5. **Agent aggregation** — ticket counts sum correctly across all agents
6. **Bottom-10 exclusions** — exactly 10 flagged, zero Tier 2 agents included
7. **SLA breach logic** — independently verified chat breach count matches manual calculation
8. **CSAT spot check** — agent CSAT computed independently matches aggregated value

### AI Classification (evaluation/evaluate_ai.py)
- 5 manually labeled tickets compared against classifier output
- Reports category accuracy and sentiment accuracy
- Broader 50-ticket sample analyzed for distribution reasonableness
- **Observed fallback accuracy:** Category accuracy depends on keyword coverage; sentiment accuracy is reasonable for clearly negative/neutral messages. LLM accuracy (with API key) is expected to be higher.

## Business Goal and Impact Calculation

**Goal:** Reduce the replacement rate from the current ~22% back toward the pre-festive baseline of ~10%.

**Calculation:**
- Pre-festive (Jan-Sep 2025) replacement rate: 9.6%, quarterly cost: ~Rs 2.0 lakh
- Post-festive (Jan-Jun 2026) replacement rate: 22.1%, quarterly cost: ~Rs 10.5 lakh
- Difference: ~Rs 8.5 lakh per quarter
- Average replacement cost per unit: ~Rs 1,800 (product unit cost + Rs 340 shipping, per policy section 5)
- Training budget: Rs 4 lakh — pays for itself within one quarter if even half the gap is closed

**Sources:** All numbers from tickets.csv, products.csv, and support-policy.pdf. No numbers are invented.

## Key Assumptions and Decisions

1. **Legacy timestamp fix:** Added +5:30 to legacy_fd resolved_at based on policy section 9 (legacy event log stores UTC) and empirical validation (all 2,309 negative handle times eliminated).
2. **Tier 2 exclusion:** Policy section 6 is explicit — these agents are not comparable.
3. **CSAT weighting at 60%:** Priya's primary ask is "who to retrain" based on sliding CSAT. CSAT is more directly actionable than handle time.
4. **Minimum 10 CSAT responses:** Avoids penalizing agents whose few scores might be noise.
5. **Agent join on agent_id, not name:** Two agents share the name "Kavya Pandey" (per Sameer's email).
6. **Datasets excluded:** `customers.csv` (customer demographics don't materially affect agent performance analysis) and `orders.csv` (lot codes and order data could inform product-quality investigation but are out of scope for agent retraining).
7. **Replacement cost formula:** Unit cost + Rs 340 shipping (per policy). Priya's email corrects Arjun Mehta's Rs 2,500 estimate.

## Limitations

- **Queue bias in bottom-10:** Most flagged agents are in Logistics/Returns, which handle harder cases. The ranking reflects queue difficulty alongside agent skill. A fairer comparison would require within-team percentiles (more agents per team needed for statistical significance).
- **CSAT non-response bias:** Only 44% of customers respond. Non-respondents may skew differently.
- **AI fallback is basic:** Without an API key, the keyword classifier has limited accuracy. LLM classification is significantly better but requires a key.
- **Product quality vs agent behavior:** The replacement spike may be driven by lot-level product defects rather than agent handling. Investigating lot_code data would help but is out of scope.
- **Handle time definition:** "First response to resolution" includes wait time between agent replies, not just active work time.

## What Was Intentionally Not Built

1. **Per-product or per-lot analysis** — Would require deeper orders.csv/products.csv integration. Priya said "dashboard first, causes later."
2. **Customer segmentation** — customers.csv has care_plus flag and geography, but agent performance analysis doesn't require it.
3. **Real-time monitoring** — This is a batch analytics tool, not a live dashboard.
4. **Authentication / multi-user access** — Not required for a take-home assessment.
5. **Cloud deployment** — Runs locally. Could be deployed to Streamlit Cloud trivially.
6. **Within-team percentile ranking** — Would be more fair but most teams have 3-7 agents, too few for meaningful percentiles.
7. **Detailed lot-code defect analysis** — Finance asked for lot codes, Priya said to ignore what's not needed.
8. **Top-5 Diwali bonus identification** — Mentioned in Priya's email but not the primary ask. The dashboard's agent table sorted by score implicitly shows top performers.

## AI and Developer Tools Used

- **Google Antigravity (Claude)** — used as a coding assistant for implementation, code generation, and analysis
- **Groq (GPT OSS 120B) 2.0 Flash** — used in the application itself for ticket classification (optional, with free API key)
- **Cost:** GPT OSS 120B usage for 100-ticket classification is well under $0.01
