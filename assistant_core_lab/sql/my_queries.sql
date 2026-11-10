-- Lab 5 Part F: analytics queries for the integrated assistant database.

-- F1: requests per intent
SELECT
    intent,
    COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY requests DESC, intent ASC;

-- F2: average latency per intent
SELECT
    intent,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY intent ASC;

-- F3: topic with the most thumbs-down feedback
SELECT
    i.topic,
    COUNT(*) AS thumbs_downs
FROM interaction AS i
JOIN feedback AS f ON f.request_id = i.request_id
WHERE f.rating = -1
  AND NULLIF(TRIM(i.topic), '') IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_downs DESC, i.topic ASC
LIMIT 1;
