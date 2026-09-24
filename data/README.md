# Data Directory

This directory contains the Vireo Audio support data pack.

## Files Used

| File | Rows | Description | Used |
|------|------|-------------|------|
| `tickets.csv` | 11,750 | Support tickets Jan 2025 - Jun 2026 | Yes (primary dataset) |
| `agents.csv` | 44 | Agent roster (one row per assignment) | Yes (agent metadata, tier info) |
| `products.csv` | 14 | Product catalog with unit costs | Yes (replacement cost calculation) |

## Files Not Used

| File | Reason |
|------|--------|
| `customers.csv` | Customer demographics (city, state, care_plus) do not materially affect agent performance analysis |
| `orders.csv` | Order data with lot codes was included "because Finance asked"; Priya said to ignore what's not needed. Lot-code analysis could help identify product quality issues but is out of scope for agent retraining. |

## Data Quality Notes

- Legacy tickets (source_system = "legacy_fd", ~3,374 rows) have resolved_at in UTC rather than IST. The application adds +5:30 to correct this.
- CSAT response rate is ~44%. Blank scores are excluded from averages, not treated as zero.
- Two agents share the name "Kavya Pandey" (A3006 in Chat Frontline, A3029 in Logistics). Always join on agent_id.
- ~40 tickets have junk IVR transcripts in customer_message (failed phone system transcriptions, not agent errors).
- 567 tickets are open/pending with no resolved_at; excluded from handle time and CSAT analysis.
