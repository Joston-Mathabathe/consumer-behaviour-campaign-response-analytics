"""Translate model scores into commercial terms: lift, gains and campaign profit."""
import numpy as np
import pandas as pd


def gains_table(y, score, bins=10):
    d = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score)}).sort_values("s", ascending=False)
    d["decile"] = pd.qcut(np.arange(len(d)), bins, labels=range(1, bins + 1))
    g = d.groupby("decile", observed=True).agg(contacts=("y", "size"), subscribers=("y", "sum")).reset_index()
    base = d["y"].mean()
    g["conv_rate"] = g["subscribers"] / g["contacts"]
    g["lift"] = g["conv_rate"] / base
    g["cum_contacts_pct"] = g["contacts"].cumsum() / g["contacts"].sum()
    g["cum_capture_pct"] = g["subscribers"].cumsum() / g["subscribers"].sum()
    return g


def profit_curve(y, score, cost_per_call, value_per_sub, points=100):
    """Profit if the bank contacts only the top-x% of customers ranked by score."""
    d = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score)}).sort_values("s", ascending=False)
    n, total = len(d), d["y"].sum()
    k = np.unique(np.linspace(1, n, points).astype(int))
    cum = d["y"].cumsum().to_numpy()[k - 1]
    out = pd.DataFrame({"pct_contacted": k / n, "contacts": k, "subscribers": cum})
    out["profit"] = out["subscribers"] * value_per_sub - out["contacts"] * cost_per_call
    out["profit_random_targeting"] = (k / n) * total * value_per_sub - k * cost_per_call
    return out


def summarise(curve, cost_per_call, value_per_sub):
    best = curve.loc[curve["profit"].idxmax()]
    full = curve.iloc[-1]
    return {
        "call_everyone_profit": float(full["profit"]),
        "best_pct_contacted": float(best["pct_contacted"]),
        "best_profit": float(best["profit"]),
        "subscribers_captured_pct": float(best["subscribers"] / full["subscribers"]),
        "calls_saved_pct": float(1 - best["pct_contacted"]),
        "profit_uplift_vs_call_everyone": float(best["profit"] - full["profit"]),
        "cost_per_call": cost_per_call, "value_per_subscriber": value_per_sub,
    }


def sensitivity(y, score, costs, values):
    rows = []
    for c in costs:
        for v in values:
            s = summarise(profit_curve(y, score, c, v), c, v)
            rows.append({"cost_per_call": c, "value_per_subscriber": v,
                         "optimal_pct_contacted": s["best_pct_contacted"],
                         "uplift_vs_call_everyone": s["profit_uplift_vs_call_everyone"]})
    return pd.DataFrame(rows)
