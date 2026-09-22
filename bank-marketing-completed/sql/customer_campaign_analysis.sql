-- Campaign performance by customer/job characteristics
SELECT job, COUNT(*) AS customers,
       AVG(CASE WHEN y='yes' THEN 1.0 ELSE 0 END) AS subscription_rate
FROM bank_marketing
GROUP BY job
ORDER BY subscription_rate DESC;

SELECT contact, COUNT(*) AS customers,
       AVG(CASE WHEN y='yes' THEN 1.0 ELSE 0 END) AS subscription_rate
FROM bank_marketing
GROUP BY contact
ORDER BY subscription_rate DESC;

SELECT month, COUNT(*) AS customers,
       AVG(CASE WHEN y='yes' THEN 1.0 ELSE 0 END) AS subscription_rate
FROM bank_marketing
GROUP BY month
ORDER BY subscription_rate DESC;

SELECT campaign, COUNT(*) AS customers,
       AVG(CASE WHEN y='yes' THEN 1.0 ELSE 0 END) AS subscription_rate
FROM bank_marketing
GROUP BY campaign
ORDER BY campaign;
