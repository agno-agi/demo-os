-- =============================================================================
-- Common SaaS Metrics Queries
-- Validated patterns for Acme Analytics dataset
-- =============================================================================

-- <query current_mrr>
-- <description>Current total MRR from active subscriptions</description>
-- <query>
SELECT
    SUM(mrr) AS total_mrr,
    COUNT(*) AS active_subscriptions
FROM subscriptions
WHERE status = 'active';
-- </query>

-- <query mrr_by_plan>
-- <description>MRR breakdown by plan tier</description>
-- <query>
SELECT
    plan,
    COUNT(*) AS subscriptions,
    SUM(mrr) AS plan_mrr,
    ROUND(AVG(mrr), 2) AS avg_mrr,
    ROUND(100.0 * SUM(mrr) / (SELECT SUM(mrr) FROM subscriptions WHERE status = 'active'), 1) AS pct_of_total
FROM subscriptions
WHERE status = 'active'
GROUP BY plan
ORDER BY plan_mrr DESC;
-- </query>

-- <query monthly_mrr_trend>
-- <description>Monthly MRR trend over time — uses started_at for new MRR and ended_at for lost MRR</description>
-- <query>
WITH months AS (
    SELECT generate_series(
        (SELECT DATE_TRUNC('month', MIN(started_at))::date FROM subscriptions),
        CURRENT_DATE,
        '1 month'::interval
    )::date AS month_start
),
active_at_month AS (
    SELECT
        m.month_start,
        SUM(s.mrr) AS mrr
    FROM months m
    JOIN subscriptions s ON s.started_at::date <= m.month_start
        AND (s.ended_at IS NULL OR s.ended_at::date > m.month_start)
    GROUP BY m.month_start
)
SELECT month_start, mrr
FROM active_at_month
ORDER BY month_start;
-- </query>

-- <query churn_rate_by_plan>
-- <description>Lifetime churn rate by plan — cancelled subscriptions / total subscriptions</description>
-- <query>
SELECT
    plan,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS churned,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'cancelled') / NULLIF(COUNT(*), 0), 1) AS churn_rate_pct
FROM subscriptions
GROUP BY plan
ORDER BY churn_rate_pct DESC;
-- </query>

-- <query cohort_retention>
-- <description>Cohort retention — customers grouped by signup month, tracked N months later</description>
-- <query>
WITH cohorts AS (
    SELECT
        id AS customer_id,
        DATE_TRUNC('month', signup_date)::date AS cohort_month
    FROM customers
),
retention AS (
    SELECT
        c.cohort_month,
        COUNT(DISTINCT c.customer_id) AS cohort_size,
        COUNT(DISTINCT CASE WHEN cu.status = 'active' THEN c.customer_id END) AS still_active
    FROM cohorts c
    JOIN customers cu ON cu.id = c.customer_id
    GROUP BY c.cohort_month
)
SELECT
    cohort_month,
    cohort_size,
    still_active,
    ROUND(100.0 * still_active / NULLIF(cohort_size, 0), 1) AS retention_pct
FROM retention
ORDER BY cohort_month;
-- </query>

-- <query revenue_by_source>
-- <description>Revenue contribution by acquisition source</description>
-- <query>
SELECT
    c.source,
    COUNT(DISTINCT c.id) AS customers,
    SUM(s.mrr) AS total_mrr,
    ROUND(AVG(s.mrr), 2) AS avg_mrr
FROM customers c
JOIN subscriptions s ON s.customer_id = c.id AND s.status = 'active'
GROUP BY c.source
ORDER BY total_mrr DESC;
-- </query>

-- <query at_risk_customers>
-- <description>Customers at risk of churning — low usage + support tickets + failed payments</description>
-- <query>
WITH usage_avg AS (
    SELECT
        customer_id,
        AVG(api_calls) AS avg_api_calls,
        AVG(active_users) AS avg_active_users
    FROM usage_metrics
    WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY customer_id
),
recent_tickets AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY customer_id
),
failed_payments AS (
    SELECT
        customer_id,
        COUNT(*) AS failed_count
    FROM invoices
    WHERE status = 'failed' AND issued_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY customer_id
)
SELECT
    c.company_name,
    s.plan,
    s.mrr,
    COALESCE(u.avg_api_calls, 0) AS avg_api_calls,
    COALESCE(t.ticket_count, 0) AS recent_tickets,
    COALESCE(f.failed_count, 0) AS failed_payments
FROM customers c
JOIN subscriptions s ON s.customer_id = c.id AND s.status = 'active'
LEFT JOIN usage_avg u ON u.customer_id = c.id
LEFT JOIN recent_tickets t ON t.customer_id = c.id
LEFT JOIN failed_payments f ON f.customer_id = c.id
WHERE COALESCE(u.avg_api_calls, 0) < 100
   OR COALESCE(t.ticket_count, 0) >= 3
   OR COALESCE(f.failed_count, 0) >= 1
ORDER BY s.mrr DESC
LIMIT 20;
-- </query>

-- <query net_revenue_retention>
-- <description>Net revenue retention — expansion vs contraction vs churn</description>
-- <query>
SELECT
    DATE_TRUNC('month', changed_at)::date AS month,
    SUM(CASE WHEN change_type = 'upgrade' THEN new_mrr - previous_mrr ELSE 0 END) AS expansion,
    SUM(CASE WHEN change_type = 'downgrade' THEN new_mrr - previous_mrr ELSE 0 END) AS contraction,
    SUM(CASE WHEN change_type = 'cancellation' THEN -previous_mrr ELSE 0 END) AS churn,
    SUM(new_mrr - previous_mrr) AS net_change
FROM plan_changes
GROUP BY DATE_TRUNC('month', changed_at)
ORDER BY month;
-- </query>

-- <query cancellation_reasons>
-- <description>Top cancellation reasons with MRR impact</description>
-- <query>
SELECT
    cancellation_reason,
    COUNT(*) AS cancellations,
    SUM(mrr) AS lost_mrr,
    ROUND(AVG(mrr), 2) AS avg_lost_mrr
FROM subscriptions
WHERE status = 'cancelled' AND cancellation_reason IS NOT NULL
GROUP BY cancellation_reason
ORDER BY lost_mrr DESC;
-- </query>

-- <query support_quality>
-- <description>Support metrics — resolution time and satisfaction by category</description>
-- <query>
SELECT
    category,
    COUNT(*) AS tickets,
    ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 86400), 1) AS avg_resolution_days,
    ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction,
    COUNT(*) FILTER (WHERE satisfaction_score IS NOT NULL) AS rated_tickets
FROM support_tickets
WHERE resolved_at IS NOT NULL
GROUP BY category
ORDER BY avg_resolution_days DESC;
-- </query>
