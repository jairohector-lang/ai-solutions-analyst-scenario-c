import pandas as pd

def classify_delta(row: pd.Series) -> str:
    if pd.isna(row['internal_match_index']):
        return 'MISSING_INTERNAL'
    # Compare amounts ignoring cents threshold upstream; here we use exact float compare on sample
    if row['rate_ext'] != row['rate_int']:
        return 'RATE_CHANGE'
    if row['amount_ext'] != row['amount_int']:
        return 'UNIT_MISMATCH'  # generic placeholder; could be units vs amount mismatch
    return 'OK'

def detect_duplicates(internal_df: pd.DataFrame) -> pd.DataFrame:
    keys = ['job_date', 'site', 'service_type', 'amount', 'rate']
    dups = internal_df[internal_df.duplicated(subset=keys, keep=False)].copy()
    if not dups.empty:
        dups['root_cause'] = 'DUPLICATE'
    return dups
