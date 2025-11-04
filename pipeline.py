import os, json, pandas as pd
from pathlib import Path
from .matching import match_records
from .classify import classify_delta, detect_duplicates

BASE = Path(__file__).resolve().parents[2]  # repo root
DATA = BASE / "data"
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True, parents=True)

def load_data():
    with open(DATA / "sample_external.json") as f:
        external = pd.DataFrame(json.load(f))
    internal = pd.read_csv(DATA / "sample_internal.csv")
    # normalize types
    for df in (external, internal):
        df['job_date'] = pd.to_datetime(df['job_date']).dt.date.astype(str)
        df['site'] = df['site'].astype(str).str.strip()
        df['service_type'] = df['service_type'].astype(str).str.strip()
    return external, internal

def reconcile(external, internal, min_conf=85):
    matched = match_records(external, internal, min_conf=min_conf)
    rows = []
    for i, row in matched.iterrows():
        if pd.isna(row['internal_match_index']):
            # Missing internally
            rows.append({
                "job_id_ext": row['job_id'],
                "job_date": row['job_date'],
                "site_ext": row['site'],
                "service_type": row['service_type'],
                "amount_ext": row['amount'],
                "rate_ext": row['rate'],
                "root_cause": "MISSING_INTERNAL",
                "match_confidence": row['match_confidence']
            })
        else:
            int_row = internal.loc[int(row['internal_match_index'])]
            delta_label = classify_delta(pd.Series({
                "internal_match_index": row['internal_match_index'],
                "rate_ext": row['rate'],
                "rate_int": int_row['rate'],
                "amount_ext": row['amount'],
                "amount_int": int_row['amount']
            }))
            if delta_label != "OK":
                rows.append({
                    "job_id_ext": row['job_id'],
                    "internal_id": int_row['internal_id'],
                    "job_date": row['job_date'],
                    "site_ext": row['site'],
                    "site_int": int_row['site'],
                    "service_type": row['service_type'],
                    "amount_ext": row['amount'],
                    "amount_int": int_row['amount'],
                    "rate_ext": row['rate'],
                    "rate_int": int_row['rate'],
                    "root_cause": delta_label,
                    "match_confidence": row['match_confidence']
                })
    # add duplicates from internal
    dups = detect_duplicates(internal)
    for _, d in dups.iterrows():
        rows.append({
            "internal_id": d['internal_id'],
            "job_date": d['job_date'],
            "site_int": d['site'],
            "service_type": d['service_type'],
            "amount_int": d['amount'],
            "rate_int": d['rate'],
            "root_cause": "DUPLICATE",
            "match_confidence": 100
        })
    exceptions = pd.DataFrame(rows)
    return exceptions

def write_summary(exceptions: pd.DataFrame):
    total = len(exceptions)
    by_cause = exceptions['root_cause'].value_counts().to_dict() if total else {}
    content = [
        "# Reconciliation Summary",
        "",
        f"- Exceptions: **{total}**",
        "- By cause:"
    ]
    for cause, cnt in by_cause.items():
        content.append(f"  - {cause}: {cnt}")
    (OUT / "summary.md").write_text("\n".join(content))

def main():
    ext, intr = load_data()
    exceptions = reconcile(ext, intr, min_conf=85)
    if not exceptions.empty:
        exceptions.to_csv(OUT / "exceptions.csv", index=False)
    write_summary(exceptions)
    print(f"Wrote {len(exceptions)} exceptions to {OUT/'exceptions.csv'} and summary to {OUT/'summary.md'}")

if __name__ == "__main__":
    main()
