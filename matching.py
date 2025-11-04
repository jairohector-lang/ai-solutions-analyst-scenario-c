from rapidfuzz import fuzz, process
import pandas as pd

def site_similarity(a: str, b: str) -> int:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    return fuzz.token_set_ratio(a, b)

def match_records(external_df: pd.DataFrame, internal_df: pd.DataFrame, min_conf: int = 85) -> pd.DataFrame:
    # Join on date + service_type; fuzzy on site
    pairs = []
    for i, ext in external_df.iterrows():
        candidates = internal_df[(internal_df['job_date'] == ext['job_date']) & (internal_df['service_type'] == ext['service_type'])]
        if candidates.empty:
            pairs.append((i, None, 0))
            continue
        # compute best match by site similarity
        scores = candidates['site'].apply(lambda s: site_similarity(ext['site'], s))
        best_idx = scores.idxmax()
        best_score = int(scores.loc[best_idx])
        if best_score >= min_conf:
            pairs.append((i, best_idx, best_score))
        else:
            pairs.append((i, None, best_score))
    out = external_df.copy()
    out['internal_match_index'] = [p[1] for p in pairs]
    out['match_confidence'] = [p[2] for p in pairs]
    return out
