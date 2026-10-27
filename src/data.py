"""Load, clean and engineer features. Works with the UCI original (';' separated,
'unknown' strings) and the already-processed comma-separated file."""
import numpy as np
import pandas as pd

from .config import RAW

CAT_MISSING = ["job", "marital", "education", "default", "housing", "loan"]
AGE_BINS = [0, 25, 35, 45, 55, 65, 120]
AGE_LABELS = ["<=25", "26-35", "36-45", "46-55", "56-65", "66+"]


def load_raw(path=RAW) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [c.strip().replace(".", "_") for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Row order is preserved: the file is chronological (May 2008 -> Nov 2010),
    which the modelling step uses for an out-of-time test."""
    df = df.copy()
    df["campaign_order"] = np.arange(len(df))
    for c in CAT_MISSING:  # 'unknown' is informative for the bank -> keep as a level
        df[c] = df[c].replace("unknown", np.nan).fillna("unknown")
    df["subscribed"] = (df["y"].astype(str).str.lower() == "yes").astype(int)
    df["was_contacted_before"] = (df["pdays"] != 999).astype(int)
    df["previous_success"] = (df["poutcome"] == "success").astype(int)
    df["age_group"] = pd.cut(df["age"], AGE_BINS, labels=AGE_LABELS).astype(str)
    df["campaign_intensity"] = pd.cut(
        df["campaign"], [0, 1, 3, 6, 100], labels=["1 contact", "2-3", "4-6", "7+"]
    ).astype(str)
    keep = [c for c in df.columns if c not in ("cluster", "previous_contacted")]
    return df[keep]


def drop_exact_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cols = [c for c in df.columns if c != "campaign_order"]
    n = int(df.duplicated(subset=cols).sum())
    return df.drop_duplicates(subset=cols, keep="first").reset_index(drop=True), n
