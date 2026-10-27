-- name: segment_profile
SELECT segment,
       COUNT(*)                          AS customers,
       ROUND(AVG(subscribed), 4)         AS subscription_rate,
       ROUND(AVG(age), 1)                AS avg_age,
       ROUND(AVG(campaign), 2)           AS avg_campaign_contacts,
       ROUND(AVG(previous), 2)           AS avg_previous_contacts
FROM bank_marketing
GROUP BY segment
ORDER BY subscription_rate DESC;
