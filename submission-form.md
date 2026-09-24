# Submission Form — Vireo Audio Task 1 (Set B)

## Candidate Information
- **Name:** Utkarsh Jain
- **Date:** September 2026

---

## 1. What does your tool do?

A Streamlit dashboard that analyzes 11,750 support tickets from Vireo Audio's helpdesk (Jan 2025 to Jun 2026). It computes CSAT and handle time per agent, flags the bottom 10 Tier 1 agents for review using a weighted composite score (60% CSAT + 40% handle time), uses Groq API with GPT-OSS 120B model to classify ticket themes and identify retraining areas, and quantifies a business goal: reducing the replacement rate from 22% to the pre-festive baseline of ~10%, worth approximately Rs 8.5 lakh per quarter in cost avoidance.

## 2. What is the business goal, stated as a number?

Reduce the replacement rate from 22.1% (post-festive, Jan-Jun 2026) to the pre-festive baseline of 9.6% (Jan-Sep 2025), saving approximately Rs 8.5 lakh per quarter in replacement costs (product unit cost + Rs 340 shipping per replacement, per support-policy.pdf section 5).

## 3. How do you know your tool's output is correct, and how often is it not?

**Deterministic analytics:** 8 automated tests verify data loading, the UTC-to-IST timestamp fix (eliminating 2,309 negative handle times), CSAT range and blank-exclusion, agent aggregation correctness (ticket counts sum exactly), bottom-10 exclusion rules (exactly 10 flagged, zero Tier 2), SLA breach logic (independently cross-checked for chat channel), and a spot-check of one agent's CSAT against manual calculation. All 8 pass.

**AI classification:** Evaluated against 5 manually labeled tickets. The keyword-based fallback correctly classifies clear cases (delivery delays, defective products) but misses nuanced or multi-issue tickets. LLM-based classification (with API key) handles ambiguity better. The evaluation script reports accuracy per run. The fallback's main failure mode is defaulting to "general_inquiry" when no keyword matches — this affects roughly 20-30% of tickets depending on the sample.

## 4. What stack/tools did you use?

- Python 3.11
- Pandas (data manipulation, all deterministic metrics)
- Streamlit (dashboard UI)
- Plotly (charts)
- Groq API with GPT-OSS 120B model (ticket classification and theme analysis, optional)
- SciPy (statistical functions)
- python-dotenv (environment variable management)

## 5. What AI tools did you use during development?

- Google Antigravity (Claude) as a coding assistant for implementation, analysis, and code generation
- Groq API with GPT-OSS 120B model within the application itself for ticket classification

## 6. What did the AI tools cost?

- Antigravity: included in existing subscription
- Groq API: well under $0.01 for the ~100-ticket classification used during development (free tier)

## 7. What did you discard or decide not to build?

1. **Per-product/lot-code defect analysis** — would help distinguish product quality issues from agent performance, but Priya asked for "dashboard first, causes later"
2. **Customer segmentation** — customers.csv has care_plus and geography, but irrelevant for agent performance ranking
3. **Within-team percentile ranking** — would be more fair for Logistics/Returns agents, but most teams have only 3-7 agents (too few for meaningful percentiles)
4. **orders.csv integration** — Finance asked for lot codes; Priya said to ignore what's not needed; agent performance doesn't require order data
5. **Real-time monitoring** — batch analytics tool is appropriate for the use case
6. **RAG / vector databases / LangChain** — unnecessary complexity for this scope
7. **Top-5 Diwali bonus identification** — mentioned in Priya's email but not the primary deliverable

## 8. What decisions did you make, and why?

1. **UTC fix for legacy tickets:** Added +5:30 to resolved_at for legacy_fd tickets based on support-policy.pdf section 9 stating the legacy event log stores UTC. Validated empirically: all 2,309 negative handle times became positive.
2. **Tier 2 exclusion from bottom-10:** Policy section 6 explicitly says Tier 2 agents should not be compared with Tier 1 on volume metrics.
3. **60/40 CSAT/handle time weighting:** CSAT is Priya's primary concern. Handle time is secondary but still relevant.
4. **Minimum 10 CSAT responses threshold:** Avoids ranking instability from small samples.
5. **Join on agent_id, never name:** Two Kavya Pandeys exist (per Sameer's email).
6. **Replacement cost = unit cost + Rs 340:** Per policy section 5. Priya corrected Arjun Mehta's Rs 2,500 estimate in the email thread.
7. **Business goal focused on replacement rate, not CSAT directly:** The replacement cost spike is the largest identifiable financial impact in the data, and it's directly quantifiable in rupees.

## 9. How long did it take?

Approximately 4-5 hours total.

## 10. Anything else?

The bottom-10 result should be read with Neha Kulkarni's caveat in mind: 8 of the 10 flagged agents work in Logistics and Returns Desk, which receive the structurally hardest cases (angry customers with missing/defective products). Their lower scores partly reflect queue difficulty, not solely individual skill gaps. Training should address both agent skills and systemic process issues (courier escalation workflows, return timelines, product quality feedback loops).
