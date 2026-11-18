/*
Bank Marketing Analytics — Microsoft SQL Server (T-SQL)
Repository: Joston-Mathabathe/consumer-behaviour-campaign-response-analytics
Source: data/processed/powerbi_customer_campaign.csv

PURPOSE
  Reproduce the five analyses in sql/customer_campaign_analysis.sql
  using Microsoft SQL Server 2017+ / SQL Server Management Studio (SSMS).

IMPORTANT
  - This is the SQL Server edition. The repository's sql/run_queries.py
    uses SQLite and should continue to run the original SQLite .sql file.
  - Import the processed CSV into dbo.bank_marketing using the SSMS
    Import Flat File wizard before running the analytical queries.
  - Verify that subscribed is numeric and coded 0/1; campaign is numeric.
  - These are observational associations, not causal effects.
*/

-- SECTION 0: DATABASE SETUP
IF DB_ID(N'BankMarketingAnalytics') IS NULL
BEGIN
    CREATE DATABASE BankMarketingAnalytics;
END;
GO

USE BankMarketingAnalytics;
GO

/*
IMPORT IN SSMS
1. Expand Databases > BankMarketingAnalytics.
2. Right-click the database > Tasks > Import Flat File.
3. Select data/processed/powerbi_customer_campaign.csv on your computer.
4. Set the destination table name to bank_marketing (schema dbo).
5. Review the inferred column types and complete the import.
6. Run the validation queries below.

Note: The Import Flat File wizard creates the table. Do not run an
additional CREATE TABLE or import the same records a second time.
*/

-- SECTION 1: VALIDATION
IF OBJECT_ID(N'dbo.bank_marketing', N'U') IS NULL
BEGIN
    THROW 50001, 'Missing dbo.bank_marketing. Import the processed CSV before running this script.', 1;
END;
GO

SELECT
    COUNT(*) AS total_contacts,
    SUM(CAST(subscribed AS BIGINT)) AS total_subscriptions,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct
FROM dbo.bank_marketing;
GO

-- name: 01_segment_performance
-- Which segments deliver subscribers, and how concentrated is the opportunity?
SELECT
    segment,
    COUNT(*) AS customers,
    SUM(CAST(subscribed AS BIGINT)) AS subscribers,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct,
    ROUND(
        100.0 * SUM(CAST(subscribed AS BIGINT)) /
        NULLIF(SUM(SUM(CAST(subscribed AS BIGINT))) OVER (), 0),
        1
    ) AS pct_of_all_subscribers,
    ROUND(
        100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0),
        1
    ) AS pct_of_customers
FROM dbo.bank_marketing
GROUP BY segment
ORDER BY subscription_rate_pct DESC;
GO

-- name: 02_diminishing_returns_by_contact_attempts
-- Observed subscription rates by FINAL number of campaign contacts.
-- Do not interpret this as causal marginal value of the nth call:
-- successful customers may stop being contacted after subscribing.
SELECT
    CASE
        WHEN campaign >= 10 THEN '10+'
        ELSE CAST(campaign AS VARCHAR(10))
    END AS attempts,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct
FROM dbo.bank_marketing
GROUP BY
    CASE
        WHEN campaign >= 10 THEN '10+'
        ELSE CAST(campaign AS VARCHAR(10))
    END
ORDER BY MIN(campaign);
GO

-- name: 03_month_ranked_with_volume_share
-- Compare monthly conversion rate with share of all campaign contacts.
SELECT
    [month],
    COUNT(*) AS contacts,
    ROUND(
        100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0),
        1
    ) AS pct_of_contacts,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct,
    RANK() OVER (
        ORDER BY AVG(CAST(subscribed AS FLOAT)) DESC
    ) AS conversion_rank
FROM dbo.bank_marketing
GROUP BY [month]
ORDER BY conversion_rank, [month];
GO

-- name: 04_channel_by_age_group
-- Compare observed contact-channel performance within age groups.
-- Channel and campaign period may be confounded.
SELECT
    age_group,
    contact,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct
FROM dbo.bank_marketing
GROUP BY age_group, contact
ORDER BY age_group, contact;
GO

-- name: 05_high_value_pockets
-- Top 10 job x prior-outcome groups with at least 100 records.
SELECT TOP (10)
    job,
    poutcome,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CAST(subscribed AS FLOAT)), 2) AS subscription_rate_pct
FROM dbo.bank_marketing
GROUP BY job, poutcome
HAVING COUNT(*) >= 100
ORDER BY AVG(CAST(subscribed AS FLOAT)) DESC, job, poutcome;
GO

/*
INTERPRETATION AND LIMITATIONS
- subscribed is assumed to be a binary 0/1 field. Its mean is the
  observed subscription proportion, multiplied by 100 for percentage.
- The file contains contact records; COUNT(*) counts records, not
  necessarily unique individual people.
- Grouping and ranking identify associations, not causal effects.
- Validate against the existing SQLite outputs in
  data/processed/sql_results/ after loading the same processed CSV.
- No machine-learning model is trained or scored by this script.
*/
