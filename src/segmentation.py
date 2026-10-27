"""Customer segmentation on customer + contact-history traits ONLY.
Macro-economic indicators (euribor, employment) describe *when* a call happened,
not *who* the customer is, so they are excluded. The original k=3 solution split
customers mainly by euribor level, i.e. by calendar period."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import RANDOM_STATE

NUM = ["age", "campaign", "previous", "was_contacted_before"]
CAT = ["job", "education", "housing", "loan", "poutcome"]


def _prep():
    return ColumnTransformer([("n", StandardScaler(), NUM),
                              ("c", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])


def diagnostics(df, ks=range(2, 9), sample=5000):
    X = _prep().fit_transform(df)
    rng = np.random.default_rng(RANDOM_STATE)
    idx = rng.choice(len(df), sample, replace=False)
    rows = []
    for k in ks:
        km = KMeans(k, n_init=10, random_state=RANDOM_STATE).fit(X)
        rows.append({"k": k, "inertia": km.inertia_,
                     "silhouette_sample": silhouette_score(X[idx], km.labels_[idx])})
    return pd.DataFrame(rows)


def fit_segments(df, k):
    pipe = Pipeline([("prep", _prep()), ("km", KMeans(k, n_init=10, random_state=RANDOM_STATE))])
    return pipe.fit_predict(df)
