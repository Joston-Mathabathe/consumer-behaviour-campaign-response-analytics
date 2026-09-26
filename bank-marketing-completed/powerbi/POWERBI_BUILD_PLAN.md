# Power BI Dashboard Build Guide

Use `data/processed/powerbi_customer_campaign.csv`.

## Page 1 — Campaign Overview
Cards: Customers, Subscribers, Subscription Rate, Average Campaign Contacts.
Charts: subscription rate by job, month and contact method.

## Page 2 — Customer Behaviour
Charts: subscription rate by age group, education, housing/loan status and campaign intensity.
Slicers: job, education, contact, month, marital status.

## Page 3 — Customer Segments
Show segment size, subscription rate, average age, campaign contacts and previous contacts.

## Page 4 — Predictive Analytics
Use `model_metrics.csv` and `feature_importance_top25.csv`.
Do not present predictive features as causal drivers.

## Modelling note
`duration` is available for descriptive analysis but was excluded from the pre-call prediction model to prevent target leakage.
