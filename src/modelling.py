"""Pre-call propensity models with two validation schemes:
 1. stratified random 80/20 split (comparable with the original analysis)
 2. out-of-time split: train on the earliest 80% of calls, test on the latest 20%
    (closer to real deployment, where the model scores *future* campaigns)."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import LEAKY, RANDOM_STATE, TEST_SIZE

CAT = ["job", "marital", "education", "default", "housing", "loan", "contact",
       "month", "day_of_week", "poutcome"]
CUSTOMER_NUM = ["age", "campaign", "pdays", "previous", "was_contacted_before"]
MACRO = ["emp_var_rate", "cons_price_idx", "cons_conf_idx", "euribor3m", "nr_employed"]
TARGET = "subscribed"


def feature_cols(include_macro=True, exclude=()):
    cols = [c for c in CAT + CUSTOMER_NUM + (MACRO if include_macro else []) if c not in exclude]
    assert not set(cols) & set(LEAKY), "leaky column in feature set"
    return cols


def make_models():
    def prep(cols_num, cols_cat, scale):
        num = StandardScaler() if scale else "passthrough"
        return ColumnTransformer([("num", num, cols_num),
                                  ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cols_cat)])
    return {
        "Logistic Regression": lambda n: Pipeline([("p", prep(n, CAT, True)), ("m", LogisticRegression(
            max_iter=2000, class_weight="balanced"))]),
        "Random Forest": lambda n: Pipeline([("p", prep(n, CAT, False)), ("m", RandomForestClassifier(
            n_estimators=300, min_samples_leaf=20, class_weight="balanced_subsample",
            n_jobs=-1, random_state=RANDOM_STATE))]),
        "Gradient Boosting": lambda n: Pipeline([("p", prep(n, CAT, False)), ("m", HistGradientBoostingClassifier(
            learning_rate=0.05, max_iter=300, max_leaf_nodes=15, l2_regularization=1.0,
            early_stopping=True, random_state=RANDOM_STATE))]),
    }


def split(df, scheme):
    if scheme == "random":
        return train_test_split(df, test_size=TEST_SIZE, stratify=df[TARGET], random_state=RANDOM_STATE)
    cut = int(len(df) * (1 - TEST_SIZE))
    d = df.sort_values("campaign_order")
    return d.iloc[:cut], d.iloc[cut:]


def evaluate(df, scheme, include_macro=True, exclude=()):
    cols = feature_cols(include_macro, exclude)
    num = [c for c in cols if c not in CAT]
    tr, te = split(df, scheme)
    out, fitted, scores = [], {}, {}
    for name, build in make_models().items():
        m = build(num).fit(tr[cols], tr[TARGET])
        p = m.predict_proba(te[cols])[:, 1]
        pred = (p >= 0.5).astype(int)
        out.append({"Model": name, "Validation": scheme, "Macro features": include_macro, "Excluded": ",".join(exclude),
                    "ROC_AUC": roc_auc_score(te[TARGET], p),
                    "PR_AUC": average_precision_score(te[TARGET], p),
                    "Precision@0.5": precision_score(te[TARGET], pred, zero_division=0),
                    "Recall@0.5": recall_score(te[TARGET], pred),
                    "F1@0.5": f1_score(te[TARGET], pred),
                    "Test base rate": te[TARGET].mean()})
        fitted[name], scores[name] = m, p
    return pd.DataFrame(out), fitted, scores, te
