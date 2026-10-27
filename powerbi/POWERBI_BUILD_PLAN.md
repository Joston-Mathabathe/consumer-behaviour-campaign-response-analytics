# Power BI Dashboard Guide

Source: `data/processed/powerbi_customer_campaign.csv` (includes the 4 behavioural `segment` labels). This file is a **build plan**: the dashboard (`.pbix`) is not included in this repository. When you build it, export screenshots to `images/dashboard_*.png` and embed them in the README.

| Page | Business question | Visuals |
|---|---|---|
| 1 Campaign overview | How is the campaign performing? | KPI cards (customers, subscribers, rate, avg contacts); rate by month, channel, job |
| 2 Customer behaviour | Who responds? | Rate by age group, education, prior outcome; slicers: job, contact, month |
| 3 Segments | Where should effort go? | Segment size vs rate vs share of subscribers |
| 4 Targeting value | What is ranking worth? | `gains_table_random_forest.csv` lift chart; `profit_sensitivity.csv` heatmap |

## Useful DAX
```DAX
Subscription Rate = DIVIDE(SUM(powerbi_customer_campaign[subscribed]), COUNTROWS(powerbi_customer_campaign))
Rate vs Average = [Subscription Rate] - CALCULATE([Subscription Rate], ALL(powerbi_customer_campaign))
Subscribers Share = DIVIDE(SUM(powerbi_customer_campaign[subscribed]), CALCULATE(SUM(powerbi_customer_campaign[subscribed]), ALL(powerbi_customer_campaign)))
```
Notes: `duration` is for descriptive use only (post-call). Do not present model features as causal drivers.
