SELECT cluster,
       COUNT(*) AS customers,
       AVG(subscribed) AS subscription_rate,
       AVG(age) AS avg_age,
       AVG(campaign) AS avg_campaign,
       AVG(previous) AS avg_previous_contacts
FROM bank_marketing_segments
GROUP BY cluster
ORDER BY subscription_rate DESC;
