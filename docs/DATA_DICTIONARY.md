# Data dictionary (key fields)

| Field | Type | Description |
|---|---|---|
| age, job, marital, education | customer | Demographics; 'unknown' kept as a level |
| default, housing, loan | customer | Credit default / housing loan / personal loan |
| contact, month, day_of_week | campaign | Channel (cellular/telephone) and timing of last contact |
| duration | **post-call** | Call length (s). Descriptive only; never used for targeting (leakage) |
| campaign | campaign | Contacts made to this customer in this campaign, **including the last one**. Not strictly known pre-call, and calls stop once a customer subscribes. Kept in the model; removing it costs ~0.002 ROC-AUC (random split) and ~0.014 (out-of-time), see `data/processed/campaign_feature_ablation.csv` |
| pdays, previous, poutcome | history | Days since previous campaign (999 = never), prior contacts, prior outcome |
| emp_var_rate … nr_employed | macro | Quarterly/monthly economic indicators; act partly as a time proxy |
| subscribed | target | 1 = term deposit subscribed |
| was_contacted_before, previous_success, age_group, campaign_intensity | engineered | See `src/data.py` |
| campaign_order | engineered | Row order (chronological), used for out-of-time validation and period comparisons |
| segment, segment_id | model | Behavioural segment from K-Means (k=4); only in `powerbi_customer_campaign.csv` |

## Provenance of `data/raw/bank-additional-full.csv`
Table of 41,188 rows from Moro, Rita & Cortez (2014), UCI "Bank Marketing" (`bank-additional-full`).
The copy in this repo is comma-separated, with 'unknown' values blank and a few columns added in an earlier
iteration of this project (`subscribed`, `previous_contacted`, `previous_success`, `was_contacted_before`,
`age_group`, `campaign_intensity`, `cluster`). `src/data.py` drops the stale `cluster` and `previous_contacted`
columns and rebuilds the others. The 21 original UCI columns are unchanged. To start from the pristine file,
download it from UCI and place it at the same path; `load_raw` auto-detects the separator.
