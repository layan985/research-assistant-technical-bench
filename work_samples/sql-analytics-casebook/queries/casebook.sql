-- 01. Revenue by month | grouping | SQLite
SELECT substr(order_date,1,7) month,ROUND(SUM(net_revenue),2) net_revenue FROM v_order_financials GROUP BY 1 ORDER BY 1;

-- 02. Trailing 3-month revenue | window frame | SQLite
WITH m AS (SELECT substr(order_date,1,7) month,SUM(net_revenue) revenue FROM v_order_financials GROUP BY 1) SELECT month,revenue,AVG(revenue) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) rolling_3m FROM m;

-- 03. Channel rank within country | partitioned ranking | SQLite
WITH x AS (SELECT c.country,c.acquisition_channel,SUM(f.net_revenue) revenue FROM dim_customer c JOIN fact_order o USING(customer_id) JOIN v_order_financials f USING(order_id) GROUP BY 1,2) SELECT *,DENSE_RANK() OVER(PARTITION BY country ORDER BY revenue DESC) channel_rank FROM x;

-- 04. Customer revenue deciles | NTILE | SQLite
WITH x AS (SELECT customer_id,SUM(net_revenue) revenue FROM v_order_financials GROUP BY 1) SELECT customer_id,revenue,NTILE(10) OVER(ORDER BY revenue DESC) revenue_decile FROM x;

-- 05. Repeat purchase rate | conditional aggregation | SQLite
WITH x AS (SELECT customer_id,COUNT(*) orders FROM fact_order WHERE status='completed' GROUP BY 1) SELECT AVG(CASE WHEN orders>=2 THEN 1.0 ELSE 0 END) repeat_rate FROM x;

-- 06. Return rate by category | joins | SQLite
SELECT p.category,AVG(CASE WHEN r.order_id IS NOT NULL THEN 1.0 ELSE 0 END) return_rate FROM fact_order_item i JOIN dim_product p USING(product_id) LEFT JOIN fact_return r USING(order_id) GROUP BY 1;

-- 07. Discount buckets | bucketing | SQLite
WITH x AS (SELECT CASE WHEN o.discount_pct=0 THEN '0%' WHEN o.discount_pct<=0.10 THEN '1-10%' WHEN o.discount_pct<=0.20 THEN '11-20%' ELSE '21%+' END bucket,f.net_revenue FROM fact_order o JOIN v_order_financials f USING(order_id)) SELECT bucket,COUNT(*) orders,AVG(net_revenue) avg_revenue FROM x GROUP BY 1;

-- 08. Days since previous order | LAG | SQLite
SELECT customer_id,order_date,julianday(order_date)-julianday(LAG(order_date) OVER(PARTITION BY customer_id ORDER BY order_date)) days_since_prev FROM fact_order WHERE status='completed';

-- 09. Customer cohort month | cohorts | SQLite
WITH f AS (SELECT customer_id,substr(MIN(order_date),1,7) cohort_month FROM fact_order WHERE status='completed' GROUP BY 1) SELECT cohort_month,COUNT(*) customers FROM f GROUP BY 1;

-- 10. Top product by category | ROW_NUMBER | SQLite
WITH x AS (SELECT p.category,p.product_id,SUM(i.quantity*i.unit_price) sales FROM fact_order_item i JOIN dim_product p USING(product_id) GROUP BY 1,2),r AS (SELECT x.*,ROW_NUMBER() OVER(PARTITION BY category ORDER BY sales DESC) rn FROM x) SELECT * FROM r WHERE rn=1;

-- 11. Pareto customer concentration | cumulative windows | SQLite
WITH x AS (SELECT customer_id,SUM(net_revenue) revenue FROM v_order_financials GROUP BY 1),r AS (SELECT *,SUM(revenue) OVER(ORDER BY revenue DESC) running,SUM(revenue) OVER() total FROM x) SELECT AVG(CASE WHEN running/total<=0.8 THEN 1.0 ELSE 0 END) share_customers_before_80pct FROM r;

-- 12. Return severity | operations KPI | SQLite
SELECT return_reason,COUNT(*) returns,SUM(refund_amount) refunds,AVG(refund_amount) avg_refund FROM fact_return GROUP BY 1;

-- 13. Monthly return rate | time series | SQLite
SELECT substr(o.order_date,1,7) month,AVG(CASE WHEN r.order_id IS NOT NULL THEN 1.0 ELSE 0 END) return_rate FROM fact_order o LEFT JOIN fact_return r USING(order_id) GROUP BY 1;

-- 14. Discount penetration | window denominator | SQLite
SELECT discount_pct,COUNT(*) orders,COUNT(*)*1.0/SUM(COUNT(*)) OVER() share FROM fact_order GROUP BY 1;

-- 15. Country AOV | multi-table joins | SQLite
SELECT c.country,AVG(f.net_revenue) aov FROM dim_customer c JOIN fact_order o USING(customer_id) JOIN v_order_financials f USING(order_id) GROUP BY 1;

-- 16. Category margin proxy | unit economics | SQLite
SELECT p.category,SUM(i.quantity*(i.unit_price-p.unit_cost)) margin_proxy FROM fact_order_item i JOIN dim_product p USING(product_id) GROUP BY 1;

-- 17. Customer recency rank | ranking | SQLite
WITH x AS (SELECT customer_id,MAX(order_date) last_order FROM fact_order WHERE status='completed' GROUP BY 1) SELECT *,DENSE_RANK() OVER(ORDER BY last_order DESC) recency_rank FROM x;

-- 18. Inactive customers | customer health | SQLite
WITH x AS (SELECT customer_id,MAX(order_date) last_order FROM fact_order WHERE status='completed' GROUP BY 1) SELECT COUNT(*) inactive FROM x WHERE last_order<'2025-01-01';

-- 19. Order-size quartiles | distribution | SQLite
SELECT order_id,net_revenue,NTILE(4) OVER(ORDER BY net_revenue) quartile FROM v_order_financials;

-- 20. Channel return-adjusted revenue | tradeoffs | SQLite
SELECT c.acquisition_channel,SUM(f.net_revenue) net_revenue,AVG(f.returned) return_rate FROM dim_customer c JOIN fact_order o USING(customer_id) JOIN v_order_financials f USING(order_id) GROUP BY 1;

-- 21. Customer lifetime days | date arithmetic | SQLite
SELECT customer_id,julianday(MAX(order_date))-julianday(MIN(order_date)) active_span_days FROM fact_order WHERE status='completed' GROUP BY 1;

-- 22. Product cross-sell pairs | self join | SQLite
SELECT a.product_id p1,b.product_id p2,COUNT(DISTINCT a.order_id) pair_orders FROM fact_order_item a JOIN fact_order_item b ON a.order_id=b.order_id AND a.product_id<b.product_id GROUP BY 1,2 ORDER BY pair_orders DESC LIMIT 20;

-- 23. Category breadth per order | distinct counts | SQLite
SELECT i.order_id,COUNT(DISTINCT p.category) category_breadth FROM fact_order_item i JOIN dim_product p USING(product_id) GROUP BY 1;

-- 24. New vs repeat monthly mix | ROW_NUMBER | SQLite
WITH n AS (SELECT order_id,customer_id,order_date,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY order_date) rn FROM fact_order WHERE status='completed') SELECT substr(order_date,1,7) month,AVG(CASE WHEN rn=1 THEN 1.0 ELSE 0 END) new_share FROM n GROUP BY 1;

-- 25. Longest gap per customer | window + aggregate | SQLite
WITH x AS (SELECT customer_id,order_date,julianday(order_date)-julianday(LAG(order_date) OVER(PARTITION BY customer_id ORDER BY order_date)) gap FROM fact_order WHERE status='completed') SELECT customer_id,MAX(gap) max_gap_days FROM x GROUP BY 1 ORDER BY max_gap_days DESC LIMIT 25;

-- 26. High-return customers | HAVING | SQLite
SELECT o.customer_id,COUNT(*) orders,SUM(CASE WHEN r.order_id IS NOT NULL THEN 1 ELSE 0 END) returned_orders FROM fact_order o LEFT JOIN fact_return r USING(order_id) WHERE o.status='completed' GROUP BY 1 HAVING returned_orders>=2;

-- 27. Product attach rate | subquery | SQLite
WITH orders AS (SELECT COUNT(DISTINCT order_id) n FROM fact_order_item) SELECT p.product_id,COUNT(DISTINCT i.order_id)*1.0/(SELECT n FROM orders) attach_rate FROM fact_order_item i JOIN dim_product p USING(product_id) GROUP BY 1;

-- 28. Monthly active customers | active users | SQLite
SELECT substr(order_date,1,7) month,COUNT(DISTINCT customer_id) active_customers FROM fact_order WHERE status='completed' GROUP BY 1;

-- 29. Revenue growth rate | growth with LAG | SQLite
WITH m AS (SELECT substr(order_date,1,7) month,SUM(net_revenue) revenue FROM v_order_financials GROUP BY 1),x AS (SELECT *,LAG(revenue) OVER(ORDER BY month) prev FROM m) SELECT month,revenue,(revenue-prev)/prev growth FROM x;

-- 30. Return reason rank | aggregate window | SQLite
SELECT return_reason,COUNT(*) n,DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) rank FROM fact_return GROUP BY 1;

-- 31. Country-segment matrix | matrix | SQLite
SELECT country,customer_segment,COUNT(*) customers FROM dim_customer GROUP BY 1,2;

-- 32. Discount by channel | join KPI | SQLite
SELECT c.acquisition_channel,AVG(o.discount_pct) avg_discount FROM dim_customer c JOIN fact_order o USING(customer_id) GROUP BY 1;

-- 33. High-value customer share | conditional aggregation | SQLite
SELECT country,AVG(CASE WHEN customer_segment='high_value' THEN 1.0 ELSE 0 END) share_high_value FROM dim_customer GROUP BY 1;

-- 34. Completed-order share | quality KPI | SQLite
SELECT AVG(CASE WHEN status='completed' THEN 1.0 ELSE 0 END) completed_share FROM fact_order;

-- 35. Duplicate-order audit | QA | SQLite
SELECT order_id,COUNT(*) n FROM fact_order GROUP BY 1 HAVING COUNT(*)>1;

-- 36. Orphan item audit | referential QA | SQLite
SELECT COUNT(*) orphan_items FROM fact_order_item i LEFT JOIN fact_order o USING(order_id) WHERE o.order_id IS NULL;

-- 37. Orphan return audit | referential QA | SQLite
SELECT COUNT(*) orphan_returns FROM fact_return r LEFT JOIN fact_order o USING(order_id) WHERE o.order_id IS NULL;

-- 38. Negative-value audit | data quality | SQLite
SELECT SUM(CASE WHEN unit_price<0 OR quantity<=0 THEN 1 ELSE 0 END) invalid_lines FROM fact_order_item;

-- 39. Customer duplicate audit | dimension QA | SQLite
SELECT customer_id,COUNT(*) n FROM dim_customer GROUP BY 1 HAVING n>1;

-- 40. Product duplicate audit | dimension QA | SQLite
SELECT product_id,COUNT(*) n FROM dim_product GROUP BY 1 HAVING n>1;

-- 41. Revenue reconciliation | reconciliation | SQLite
SELECT ROUND(SUM(net_revenue),2) view_revenue FROM v_order_financials;

-- 42. Monthly category trend | multidimensional trend | SQLite
SELECT substr(o.order_date,1,7) month,p.category,SUM(i.quantity*i.unit_price) gross_sales FROM fact_order o JOIN fact_order_item i USING(order_id) JOIN dim_product p USING(product_id) GROUP BY 1,2;

-- 43. Customer top category | customer preference | SQLite
WITH x AS (SELECT o.customer_id,p.category,SUM(i.quantity*i.unit_price) sales FROM fact_order o JOIN fact_order_item i USING(order_id) JOIN dim_product p USING(product_id) GROUP BY 1,2),r AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY sales DESC) rn FROM x) SELECT customer_id,category,sales FROM r WHERE rn=1;

-- 44. Channel monthly growth | partitioned LAG | SQLite
WITH m AS (SELECT c.acquisition_channel,substr(o.order_date,1,7) month,SUM(f.net_revenue) revenue FROM dim_customer c JOIN fact_order o USING(customer_id) JOIN v_order_financials f USING(order_id) GROUP BY 1,2) SELECT *,revenue-LAG(revenue) OVER(PARTITION BY acquisition_channel ORDER BY month) abs_growth FROM m;

-- 45. RFM base | RFM | SQLite
SELECT customer_id,CAST(julianday('2025-05-31')-julianday(MAX(order_date)) AS INT) recency_days,COUNT(*) frequency FROM fact_order WHERE status='completed' GROUP BY 1;

-- 46. RFM score | scoring windows | SQLite
WITH rfm AS (SELECT customer_id,CAST(julianday('2025-05-31')-julianday(MAX(order_date)) AS INT) recency,COUNT(*) frequency FROM fact_order WHERE status='completed' GROUP BY 1) SELECT *,NTILE(5) OVER(ORDER BY recency DESC) r_score,NTILE(5) OVER(ORDER BY frequency) f_score FROM rfm;

-- 47. Top 10% customers | deciles | SQLite
WITH x AS (SELECT customer_id,SUM(net_revenue) revenue FROM v_order_financials GROUP BY 1),r AS (SELECT *,NTILE(10) OVER(ORDER BY revenue DESC) d FROM x) SELECT * FROM r WHERE d=1;

-- 48. Channel customer economics | unit economics | SQLite
SELECT c.acquisition_channel,COUNT(DISTINCT c.customer_id) customers,SUM(f.net_revenue) revenue,SUM(f.net_revenue)/COUNT(DISTINCT c.customer_id) revenue_per_customer FROM dim_customer c JOIN fact_order o USING(customer_id) JOIN v_order_financials f USING(order_id) GROUP BY 1;

-- 49. Recursive date spine | recursive CTE | PostgreSQL pattern
WITH RECURSIVE dates AS (SELECT DATE '2025-01-01' d UNION ALL SELECT d+1 FROM dates WHERE d<DATE '2025-12-31') SELECT * FROM dates;

-- 50. Sessionization | sessionization | PostgreSQL pattern
SELECT *,SUM(new_session) OVER(PARTITION BY customer_id ORDER BY event_ts) session_id FROM (...) x;

-- 51. Percentile_cont median | ordered-set aggregate | PostgreSQL pattern
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY net_revenue) FROM order_financials;

-- 52. Lateral top-N | LATERAL | PostgreSQL pattern
SELECT c.customer_id,x.* FROM customers c CROSS JOIN LATERAL (SELECT * FROM orders o WHERE o.customer_id=c.customer_id ORDER BY order_date DESC LIMIT 3) x;

-- 53. Distinct on latest row | DISTINCT ON | PostgreSQL pattern
SELECT DISTINCT ON (customer_id) * FROM orders ORDER BY customer_id,order_date DESC;

-- 54. Generate-series calendar | date spine | PostgreSQL pattern
SELECT d::date FROM generate_series('2025-01-01'::date,'2025-12-31'::date,'1 day') d;

-- 55. FILTER aggregates | FILTER | PostgreSQL pattern
SELECT COUNT(*) FILTER (WHERE returned=1),COUNT(*) FILTER (WHERE returned=0) FROM orders;

-- 56. JSONB extraction | JSONB | PostgreSQL pattern
SELECT payload->>'campaign' campaign,COUNT(*) FROM events GROUP BY 1;

-- 57. Explain analyze | optimization | PostgreSQL pattern
EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM orders WHERE customer_id=42 ORDER BY order_date DESC;

-- 58. Concurrent materialized refresh | warehouse ops | PostgreSQL pattern
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_ltv;
