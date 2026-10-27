"""End-to-end pipeline:  python -m src.run_pipeline
Regenerates every table in data/processed/ and every chart in images/."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import RocCurveDisplay

from . import business, data, modelling, segmentation
from .config import (COST_PER_CALL, IMAGES, PROCESSED, RANDOM_STATE,
                     VALUE_PER_SUBSCRIBER)

NAVY, TEAL, GREY, ORANGE = "#1f3a5f", "#1a9e8f", "#9aa5b1", "#e07a1f"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.titleweight": "bold", "font.size": 10})
SEG_NAMES = {}  # filled after profiling


def rate_bar(df, col, title, fname, order=None, top=None):
    g = df.groupby(col).agg(n=("subscribed", "size"), rate=("subscribed", "mean"))
    g = g.loc[order] if order else g.sort_values("rate", ascending=False)
    if top: g = g.head(top)
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(g) + 1.4))
    ax.barh(g.index.astype(str), g["rate"] * 100, color=TEAL)
    ax.axvline(df["subscribed"].mean() * 100, color=ORANGE, ls="--", lw=1.2, label="Overall 11.3%")
    for i, (r, n) in enumerate(zip(g["rate"], g["n"])):
        ax.text(r * 100 + 0.6, i, f"{r:.1%}  (n={n:,})", va="center", fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("Subscription rate (%)"); ax.set_title(title)
    ax.set_xlim(0, g["rate"].max() * 100 * 1.35); ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(IMAGES / fname); plt.close(fig)
    return g.reset_index()


def name_segments(df):
    """Rule-based labels derived from segment profiles (see notebook 03)."""
    prof = df.groupby("segment_id").agg(camp=("campaign", "mean"), succ=("previous_success", "mean"),
                                        age=("age", "mean"))
    names = {}
    for sid, r in prof.iterrows():
        if r.succ > 0.5: names[sid] = "Re-engaged past successes"
        elif r.camp > 8: names[sid] = "Over-contacted prospects"
        elif r.age >= prof.loc[prof.camp <= 8, "age"].median(): names[sid] = "Established first-time prospects"
        else: names[sid] = "Younger first-time prospects"
    return names


def main():
    PROCESSED.mkdir(exist_ok=True, parents=True); IMAGES.mkdir(exist_ok=True)
    raw = data.load_raw()
    df = data.clean(raw)
    n_dupes = int(df.drop(columns="campaign_order").duplicated().sum())

    # ---------- KPIs
    kpis = {"records": len(df), "variables": raw.shape[1], "subscribers": int(df.subscribed.sum()),
            "subscription_rate": float(df.subscribed.mean()), "avg_age": float(df.age.mean()),
            "avg_campaign_contacts": float(df.campaign.mean()), "exact_duplicate_rows": n_dupes,
            "share_never_previously_contacted": float(1 - df.was_contacted_before.mean())}

    # ---------- descriptive summaries + charts
    summaries = {
        "job": rate_bar(df, "job", "Subscription rate by job", "subscription_rate_by_job.png"),
        "age_group": rate_bar(df, "age_group", "Subscription rate by age group",
                              "subscription_rate_by_age.png", order=data.AGE_LABELS),
        "month": rate_bar(df, "month", "Subscription rate by month",
                          "subscription_rate_by_month.png",
                          order=["mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]),
        "contact": rate_bar(df, "contact", "Subscription rate by contact channel",
                            "subscription_rate_by_contact.png"),
        "education": rate_bar(df, "education", "Subscription rate by education",
                              "subscription_rate_by_education.png"),
        "campaign_intensity": rate_bar(df, "campaign_intensity", "Subscription rate by contacts in this campaign",
                                       "subscription_rate_by_intensity.png",
                                       order=["1 contact", "2-3", "4-6", "7+"]),
        "poutcome": rate_bar(df, "poutcome", "Subscription rate by previous-campaign outcome",
                             "subscription_rate_by_prior_outcome.png"),
    }
    for k, v in summaries.items():
        v.rename(columns={"n": "Customers", "rate": "SubscriptionRate"}).to_csv(PROCESSED / f"{k}_summary.csv", index=False)

    # ---------- segmentation
    diag = segmentation.diagnostics(df)
    diag.to_csv(PROCESSED / "segmentation_diagnostics.csv", index=False)
    K = 4  # chosen for business interpretability; silhouette shown for transparency
    df["segment_id"] = segmentation.fit_segments(df, K)
    SEG_NAMES.update(name_segments(df))
    df["segment"] = df["segment_id"].map(SEG_NAMES)
    seg = df.groupby("segment").agg(Customers=("age", "size"), SubscriptionRate=("subscribed", "mean"),
                                    AvgAge=("age", "mean"), AvgCampaign=("campaign", "mean"),
                                    AvgPreviousContacts=("previous", "mean")).reset_index()
    seg["CustomerShare"] = seg["Customers"] / len(df)
    seg["Subscribers"] = (seg["Customers"] * seg["SubscriptionRate"]).round().astype(int)
    seg["ShareOfAllSubscribers"] = seg["Subscribers"] / seg["Subscribers"].sum()
    seg = seg.sort_values("SubscriptionRate", ascending=False)
    seg.to_csv(PROCESSED / "customer_segment_profile.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    ax.barh(seg["segment"], seg["SubscriptionRate"] * 100, color=[TEAL, GREY, GREY, ORANGE])
    for i, (r, n) in enumerate(zip(seg["SubscriptionRate"], seg["Customers"])):
        ax.text(r * 100 + 1, i, f"{r:.1%}  (n={n:,})", va="center", fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(0, 80); ax.set_xlabel("Subscription rate (%)")
    ax.set_title("Behavioural segments (k=4)"); fig.tight_layout()
    fig.savefig(IMAGES / "subscription_rate_by_segment.png"); plt.close(fig)

    # ---------- modelling: random vs out-of-time, with/without macro features
    results, store = [], {}
    for scheme in ("random", "oot"):
        for macro in (True, False):
            r, fitted, scores, te = modelling.evaluate(df, scheme, macro)
            results.append(r); store[(scheme, macro)] = (fitted, scores, te)
    metrics = pd.concat(results, ignore_index=True)
    metrics.to_csv(PROCESSED / "model_metrics.csv", index=False)

    # champion = Random Forest (best/most stable across schemes); report on random split
    fitted, scores, te = store[("random", True)]
    rf, p_rf = fitted["Random Forest"], scores["Random Forest"]
    cm = pd.crosstab(te.subscribed, (p_rf >= 0.5).astype(int))
    cm.index = ["Actual No", "Actual Yes"]; cm.columns = ["Predicted No", "Predicted Yes"]
    cm.to_csv(PROCESSED / "random_forest_confusion_matrix.csv")

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for n, c in zip(scores, [GREY, TEAL, NAVY]):
        RocCurveDisplay.from_predictions(te.subscribed, scores[n], name=n, ax=ax, curve_kwargs={"color": c})
    ax.plot([0, 1], [0, 1], ls="--", color="k", lw=0.8); ax.set_title("ROC curves (random hold-out)")
    fig.tight_layout(); fig.savefig(IMAGES / "roc_curve_models.png"); plt.close(fig)

    # permutation importance on original (pre-encoding) columns
    cols = modelling.feature_cols(True)
    pi = permutation_importance(rf, te[cols], te.subscribed, scoring="roc_auc", n_repeats=5,
                                random_state=RANDOM_STATE, n_jobs=-1)
    imp = pd.DataFrame({"Feature": cols, "AUC_drop": pi.importances_mean}).sort_values("AUC_drop", ascending=False)
    imp.to_csv(PROCESSED / "permutation_importance.csv", index=False)
    top = imp.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 4.2)); ax.barh(top.Feature, top.AUC_drop, color=NAVY)
    ax.set_xlabel("Drop in ROC-AUC when feature is shuffled"); ax.set_title("Permutation importance (Random Forest)")
    fig.tight_layout(); fig.savefig(IMAGES / "permutation_importance.png"); plt.close(fig)

    # model comparison chart
    m = metrics[metrics["Macro features"]].pivot(index="Model", columns="Validation", values="ROC_AUC")
    fig, ax = plt.subplots(figsize=(6.5, 3.4)); x = np.arange(len(m)); w = 0.38
    ax.bar(x - w/2, m["random"], w, label="Random split", color=TEAL)
    ax.bar(x + w/2, m["oot"], w, label="Out-of-time split", color=ORANGE)
    ax.set_xticks(x); ax.set_xticklabels(m.index); ax.set_ylim(0.5, 0.9); ax.set_ylabel("ROC-AUC")
    ax.set_title("Performance drops when scoring a later campaign period"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(IMAGES / "model_validation_comparison.png"); plt.close(fig)

    # ---------- robustness: is the model leaning on `campaign`?
    # `campaign` counts contacts in this campaign *including the final call* and stops once a
    # customer says yes, so it is not strictly known before the call. Re-fit without it.
    abl = []
    for scheme in ("random", "oot"):
        for exclude in ((), ("campaign",)):
            r, _, sc, t = modelling.evaluate(df, scheme, True, exclude)
            r = r[r["Model"] == "Random Forest"].copy()
            r["top_decile_lift"] = float(business.gains_table(t.subscribed, sc["Random Forest"]).loc[0, "lift"])
            abl.append(r)
    pd.concat(abl)[["Validation", "Excluded", "ROC_AUC", "PR_AUC", "top_decile_lift"]].to_csv(
        PROCESSED / "campaign_feature_ablation.csv", index=False)

    # ---------- robustness: cellular vs landline *within* the same period of the campaign
    # Landline calls are concentrated in the earliest part of the file, when rates were lowest, so the
    # pooled gap mixes channel with calendar period. Compare channels inside each chronological decile.
    df["period"] = pd.qcut(df["campaign_order"], 10, labels=False) + 1
    per = df.groupby(["period", "contact"]).agg(n=("subscribed", "size"), rate=("subscribed", "mean")).unstack("contact")
    per.columns = [f"{a}_{b}" for a, b in per.columns]
    per = per.reset_index()
    ok = per[(per["n_telephone"] >= 100) & (per["n_cellular"] >= 100)].copy()
    w = ok["n_telephone"]
    kpis["channel_within_period"] = {
        "periods_with_both_channels": int(len(ok)),
        "cellular_higher_in_periods": int((ok["rate_cellular"] > ok["rate_telephone"]).sum()),
        "cellular_rate_period_adjusted": float((ok["rate_cellular"] * w).sum() / w.sum()),
        "telephone_rate_period_adjusted": float((ok["rate_telephone"] * w).sum() / w.sum()),
    }
    per.to_csv(PROCESSED / "contact_by_period.csv", index=False)
    df = df.drop(columns="period")

    # ---------- business impact
    g = business.gains_table(te.subscribed, p_rf); g.to_csv(PROCESSED / "gains_table_random_forest.csv", index=False)
    cur = business.profit_curve(te.subscribed, p_rf, COST_PER_CALL, VALUE_PER_SUBSCRIBER)
    cur.to_csv(PROCESSED / "profit_curve_random_forest.csv", index=False)
    impact = business.summarise(cur, COST_PER_CALL, VALUE_PER_SUBSCRIBER)
    impact["top_decile_lift"] = float(g.loc[0, "lift"])
    impact["top_3_deciles_capture_pct"] = float(g.loc[2, "cum_capture_pct"])
    impact["test_set_contacts"] = int(len(te))
    impact["break_even_conversion_rate"] = COST_PER_CALL / VALUE_PER_SUBSCRIBER
    # Capacity-constrained view: the team can only call a fixed share of customers.
    cap = {}
    for share in (0.2, 0.3, 0.5):
        row = cur.iloc[(cur.pct_contacted - share).abs().argmin()]
        cap[f"{int(share*100)}pct"] = {
            "model_capture": float(row["subscribers"] / cur.iloc[-1]["subscribers"]),
            "random_capture": float(row["pct_contacted"]),
            "conversion_rate": float(row["subscribers"] / row["contacts"])}
    impact["capacity_constrained"] = cap
    fo, so, teo = store[("oot", True)]
    curo = business.profit_curve(teo.subscribed, so["Random Forest"], COST_PER_CALL, VALUE_PER_SUBSCRIBER)
    impact["out_of_time"] = business.summarise(curo, COST_PER_CALL, VALUE_PER_SUBSCRIBER)
    impact["out_of_time"]["top_decile_lift"] = float(business.gains_table(teo.subscribed, so["Random Forest"]).loc[0, "lift"])
    sens = business.sensitivity(te.subscribed, p_rf, [2, 5, 10, 20], [50, 100, 150, 300])
    sens.to_csv(PROCESSED / "profit_sensitivity.csv", index=False)

    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].bar(g["decile"].astype(str), g["lift"], color=TEAL); axs[0].axhline(1, color=ORANGE, ls="--")
    axs[0].set_xlabel("Score decile (1 = highest propensity)"); axs[0].set_ylabel("Lift vs average")
    axs[0].set_title("Lift by decile")
    for i, v in enumerate(g["lift"]): axs[0].text(i, v + 0.1, f"{v:.1f}x", ha="center", fontsize=8)
    axs[1].plot(cur.pct_contacted * 100, cur.profit, color=NAVY, label="Model-ranked targeting")
    axs[1].plot(cur.pct_contacted * 100, cur.profit_random_targeting, color=GREY, ls="--", label="Random targeting")
    axs[1].axvline(impact["best_pct_contacted"] * 100, color=ORANGE, lw=1)
    axs[1].set_xlabel("% of customers contacted"); axs[1].set_ylabel("Campaign profit, test set")
    axs[1].set_title(f"Profit at \\${COST_PER_CALL:.0f}/call, \\${VALUE_PER_SUBSCRIBER:.0f}/subscriber")
    axs[1].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"\\${v/1000:.0f}k")); axs[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(IMAGES / "lift_and_profit.png"); plt.close(fig)

    # ---------- Power BI export + metadata
    df.drop(columns=["y"]).to_csv(PROCESSED / "powerbi_customer_campaign.csv", index=False)
    df.drop(columns=["campaign_order", "segment_id", "segment"]).to_csv(PROCESSED / "bank_marketing_clean.csv", index=False)
    kpis["segments_k"] = K
    kpis["impact"] = impact
    (PROCESSED / "kpis.json").write_text(json.dumps(kpis, indent=2))
    print(json.dumps(kpis, indent=2))


if __name__ == "__main__":
    main()
