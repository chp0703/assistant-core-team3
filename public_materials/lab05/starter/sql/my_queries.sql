-- Lab 5 Part F: write your queries for the assistant database here.
-- Q1 requests per intent
SELECT
    intent,
    COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY requests DESC, intent ASC;

-- Q2 average latency per intent
SELECT
    intent,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY intent ASC;

-- Q3 topics with the most thumbs-down (JOIN feedback with interaction)
