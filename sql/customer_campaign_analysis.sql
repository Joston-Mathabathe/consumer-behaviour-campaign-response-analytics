-- Table: bank_marketing (loaded from data/processed/powerbi_customer_campaign.csv)
-- Dialect: SQLite / ANSI (window functions). Run all with: python sql/run_queries.py

-- name: 01_segment_performance
-- Which segments deliver the subscribers, and how concentrated is the opportunity?
SELECT segment,
       COUNT(*)                                        AS customers,
       SUM(subscribed)                                 AS subscribers,
       ROUND(100.0 * AVG(subscribed), 2)               AS subscription_rate_pct,
       ROUND(100.0 * SUM(subscribed) / SUM(SUM(subscribed)) OVER (), 1) AS pct_of_all_subscribers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)               AS pct_of_customers
FROM bank_marketing
GROUP BY segment
ORDER BY subscription_rate_pct DESC;

-- name: 02_diminishing_returns_by_contact_attempts
-- Marginal value of repeated calls within one campaign.
SELECT CASE WHEN campaign >= 10 THEN '10+' ELSE CAST(campaign AS TEXT) END AS attempts,
       COUNT(*)                          AS customers,
       ROUND(100.0 * AVG(subscribed), 2) AS subscription_rate_pct
FROM bank_marketing
GROUP BY 1
ORDER BY MIN(campaign);

-- name: 03_month_ranked_with_volume_share
-- Months with the highest conversion are the smallest-volume months: a capacity/seasonality question.
SELECT month, COUNT(*) AS contacts,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_contacts,
       ROUND(100.0 * AVG(subscribed), 2)                    AS subscription_rate_pct,
       RANK() OVER (ORDER BY AVG(subscribed) DESC)          AS conversion_rank
FROM bank_marketing
GROUP BY month
ORDER BY conversion_rank;

-- name: 04_channel_by_age_group
-- Does the cellular advantage hold within every age group (rules out a mix effect)?
SELECT age_group, contact,
       COUNT(*)                          AS customers,
       ROUND(100.0 * AVG(subscribed), 2) AS subscription_rate_pct
FROM bank_marketing
GROUP BY age_group, contact
ORDER BY age_group, contact;

-- name: 05_high_value_pockets
-- Job x prior-outcome cells with enough volume (>=100) to act on, ranked by conversion.
SELECT job, poutcome, COUNT(*) AS customers,
       ROUND(100.0 * AVG(subscribed), 2) AS subscription_rate_pct
FROM bank_marketing
GROUP BY job, poutcome
HAVING COUNT(*) >= 100
ORDER BY AVG(subscribed) DESC
LIMIT 10;
