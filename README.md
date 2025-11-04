# Scenario C — Revenue Reconciliation & Anomaly Detection

This repo is my submission for the **AI Solutions Analyst — Assessment (Entry Level)**, focusing on Scenario C. It demonstrates a practical approach to detect, reconcile, and explain deltas between external client job data (via API/JSON) and our internal ledger, then route fixes efficiently.

## 1) Problem Framing

**Business goal:** Ensure revenue accuracy and fast month-end close by reconciling differences between **external job data** and **internal ledger** with <1% acceptable variance (ignore cents).  
**Primary risks:** leakage from missed jobs, rate drift, duplicates, mis-keyed sites, and unit mismatches.  
**Success =** lower exception rate, faster reconciliation cycle, and clear ownership of fixes.

### Assumptions
- External data ingested monthly as JSON; internal ledger as CSV/DB export.
- Matching keys: `job_date`, `site` (free-text), `service_type`. Site names may have abbreviations/misspellings.
- Acceptable variance target: **< 1% of monthly revenue**.
- Non-union/simple rate model; currency = USD; cents ignored for tolerance checks.
- Security: credentials via environment variables (`.env`) and never committed.
- This prototype uses **sample data** and a local run; in prod, scheduled job runs nightly during close-week and weekly otherwise.

## 2) Solution Overview

**Hybrid matching**: deterministic on date + service_type, **fuzzy on site** (RapidFuzz token set ratio).  
**Confidence scoring** to decide: auto-match vs. human-in-the-loop (HIL) queue.  
**Root-cause classifier** (rule-based) labels deltas as:
- `MISSING_INTERNAL` (exists externally, not internally)
- `MISSING_EXTERNAL` (exists internally, not externally)
- `RATE_CHANGE`
- `DUPLICATE`
- `UNIT_MISMATCH`
- `OTHER`

**Exception queue**: CSV artifact plus a summary report. Owners & cadence below.

## 3) Architecture (logical)

- **Ingest**: External JSON + Internal CSV
- **Normalize**: trim, casefold, canonicalize sites (regex + mapping table if available)
- **Match**: date + service_type + fuzzy(site) → match_id + confidence
- **Compare**: revenue/units/rates → labeled delta
- **Queue**: write `outputs/exceptions.csv` + `outputs/summary.md`
- **Notify**: (future) email/Teams webhook digest with top sites & amounts
- **HIL**: review low-confidence matches and high-amount exceptions

See `docs/diagram.md` for a Mermaid diagram.

## 4) Data & Metrics

- **Offline metrics**: match precision/recall on a labeled sample; % auto-matched; avg confidence; # exceptions per 10k jobs.
- **Ops scorecard**: % auto-resolved, avg decision time, exceptions aging, $ impact by root cause, sites with repeated issues.
- **Alerting**: if absolute variance > 1% of monthly revenue → raise to Finance Lead.

## 5) How to Run

```bash
# 1) Optional: create and activate a virtual env
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)

# 2) Install deps
pip install -r requirements.txt

# 3) Run pipeline (uses sample data in data/)
python -m reconcile

# 4) See artifacts
ls outputs/
# -> exceptions.csv, summary.md
```

## 6) Tests

```bash
pytest -q
```

## 7) Deployment & Ops (non-code plan)

- Schedule a nightly job via GitHub Actions/Argo/Airflow.
- Secrets via GitHub Envs or Vault; provide `.env.example`.
- Outputs to a data lake table and a BI dashboard (e.g., Power BI) for trends.
- Rollback: pipeline is idempotent; deployments are versioned; toggle feature flags to disable fuzzy matching during incidents.

## 8) Trade-offs, Risks & Next Steps

**Trade-offs**  
- Rule-based root-cause is transparent but limited; ML classifier could improve recall later.  
- Fuzzy thresholds (defaults here) may vary by client; we expose config.

**Risks**  
- Over-matching similar sites across a metro; we cap by date + service_type and require min confidence.  
- Upstream data drift; add schema checks & contracts.

**Next steps**  
- Add caching for external API; add Teams/Email digests.  
- Add labeled training set and ML matcher.  
- Add site-canonical map learned from history.

---

**Author**: Candidate — AI Solutions Analyst (Entry Level)  
**Scenario**: C — Revenue Reconciliation & Anomaly Detection
