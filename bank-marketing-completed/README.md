# Bank Customer Behaviour & Marketing Campaign Analytics

## Business Problem
How can a bank use customer characteristics, previous interactions and campaign information to understand customer behaviour, identify customer segments and improve marketing campaign targeting?

## Dataset
**Bank Marketing — bank-additional-full.csv**, supplied in the uploaded archive. The analysis uses the 21-column `bank-additional-full` version.

Dataset size: **41,188 records**  
Target: `y` — whether the client subscribed to a term deposit.

## Important analytical note
This dataset is a **marketing-campaign dataset**, not a transaction/spending dataset. It does not contain customer purchase history or account spending behaviour. The project therefore focuses on customer/campaign behaviour, segmentation and subscription propensity.

`duration` is retained for descriptive Power BI analysis but is **excluded from the pre-call predictive model** because call duration is only known after the contact and would create target leakage if used to target customers before a call.

## Objectives
- Explore customer and campaign behaviour
- Identify differences in subscription rates across customer groups
- Build behavioural customer segments
- Develop pre-call classification models
- Compare Logistic Regression and Random Forest
- Translate analytical findings into commercial insights
- Prepare Power BI-ready data

## Key Results
- Subscription rate: **11.27%**
- Records: **41,188**
- Average customer age: **40.0**
- Average campaign contacts: **2.57**
- Segmentation candidate selected from diagnostics: **k=3**

## Methods
### Descriptive analytics
Job, age group, education, contact method, campaign month and campaign intensity.

### Segmentation
K-Means clustering on standardised pre-outcome customer/campaign characteristics. Cluster count was evaluated using silhouette scoring on a 5,000-record sample.

### Predictive modelling
- Logistic Regression
- Random Forest
- Stratified 80/20 train/test split
- Class weighting for the imbalanced target
- Metrics: accuracy, precision, recall, F1 and ROC-AUC

## Repository Structure
```text
data/processed/     cleaned data, summaries, model and segmentation outputs
images/             generated charts
sql/                reusable SQL analyses
notebooks/          analysis workflow notes
powerbi/            Power BI build guide
src/                reproducible pipeline
README.md
requirements.txt
```

## Business Interpretation Framework
The project focuses on identifying observable differences in customer/campaign behaviour and translating those differences into testable marketing opportunities. Model predictions are not treated as causal evidence.

## Limitations
- The dataset is historical and comes from a specific marketing campaign context.
- It does not contain transaction/spending history.
- Segment definitions depend on selected variables.
- Predictive performance does not imply that a variable causes subscription.
- Further testing would be needed before using model scores operationally.
