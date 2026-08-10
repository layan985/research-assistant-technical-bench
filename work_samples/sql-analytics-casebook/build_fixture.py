from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "fixture.db"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE dim_customer(customer_id TEXT PRIMARY KEY, signup_date TEXT, country TEXT, acquisition_channel TEXT, customer_segment TEXT);
CREATE TABLE dim_product(product_id TEXT PRIMARY KEY, product_name TEXT, category TEXT, subcategory TEXT, unit_cost REAL, list_price REAL);
CREATE TABLE fact_order(order_id TEXT PRIMARY KEY, customer_id TEXT, order_date TEXT, device TEXT, payment_method TEXT, discount_pct REAL, shipping_fee REAL, status TEXT, FOREIGN KEY(customer_id) REFERENCES dim_customer(customer_id));
CREATE TABLE fact_order_item(order_id TEXT, product_id TEXT, quantity INTEGER, unit_price REAL, FOREIGN KEY(order_id) REFERENCES fact_order(order_id), FOREIGN KEY(product_id) REFERENCES dim_product(product_id));
CREATE TABLE fact_return(order_id TEXT PRIMARY KEY, returned INTEGER, return_date TEXT, return_reason TEXT, refund_amount REAL, FOREIGN KEY(order_id) REFERENCES fact_order(order_id));
CREATE VIEW v_order_financials AS
WITH item_rollup AS (
  SELECT oi.order_id, SUM(oi.quantity*oi.unit_price) AS gross_revenue, SUM(oi.quantity*p.unit_cost) AS cogs, SUM(oi.quantity) AS units
  FROM fact_order_item oi JOIN dim_product p USING(product_id) GROUP BY oi.order_id
)
SELECT o.order_id,o.customer_id,o.order_date,o.device,o.payment_method,o.discount_pct,o.shipping_fee,o.status,
       COALESCE(i.gross_revenue,0) gross_revenue,COALESCE(i.cogs,0) cogs,COALESCE(i.units,0) units,
       COALESCE(r.returned,0) returned,COALESCE(r.refund_amount,0) refund_amount,
       CASE WHEN o.status='completed' THEN COALESCE(i.gross_revenue,0)+o.shipping_fee-COALESCE(r.refund_amount,0) ELSE 0 END net_revenue,
       CASE WHEN o.status='completed' THEN COALESCE(i.gross_revenue,0)-COALESCE(i.cogs,0)-COALESCE(r.refund_amount,0) ELSE 0 END gross_margin
FROM fact_order o LEFT JOIN item_rollup i USING(order_id) LEFT JOIN fact_return r USING(order_id);
"""

COUNTRIES = ["Jordan", "Egypt", "UAE", "Saudi Arabia"]
CHANNELS = ["organic", "paid_search", "affiliate", "social"]
SEGMENTS = ["consumer", "high_value", "business"]
CATEGORIES = ["Electronics", "Home", "Beauty"]

if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
con.executescript(SCHEMA)

for i in range(1, 21):
    con.execute("INSERT INTO dim_customer VALUES (?,?,?,?,?)", (
        f"C{i:03d}", f"2024-{(i%12)+1:02d}-01", COUNTRIES[i%len(COUNTRIES)], CHANNELS[i%len(CHANNELS)], SEGMENTS[i%len(SEGMENTS)]
    ))
for i in range(1, 7):
    category = CATEGORIES[(i-1)%len(CATEGORIES)]
    con.execute("INSERT INTO dim_product VALUES (?,?,?,?,?,?)", (
        f"P{i:03d}", f"Product {i}", category, f"Sub{i%2+1}", 8.0+i*3, 20.0+i*6
    ))

order_num = 0
for month in range(1, 7):
    for i in range(1, 21):
        if (i + month) % 3 == 0:
            continue
        order_num += 1
        oid = f"O{order_num:04d}"
        day = ((i*3 + month) % 27) + 1
        status = "cancelled" if order_num % 17 == 0 else "completed"
        discount = [0.0, 0.05, 0.10, 0.15, 0.25][order_num % 5]
        con.execute("INSERT INTO fact_order VALUES (?,?,?,?,?,?,?,?)", (
            oid, f"C{i:03d}", f"2025-{month:02d}-{day:02d}", ["web","ios","android"][order_num%3], ["card","wallet"][order_num%2], discount, 4.5, status
        ))
        p1 = f"P{((i+month)%6)+1:03d}"
        p2 = f"P{((i+month+2)%6)+1:03d}"
        con.execute("INSERT INTO fact_order_item VALUES (?,?,?,?)", (oid, p1, 1+(order_num%2), 24.0+(int(p1[1:])*5)))
        if order_num % 4 == 0:
            con.execute("INSERT INTO fact_order_item VALUES (?,?,?,?)", (oid, p2, 1, 24.0+(int(p2[1:])*5)))
        if status == "completed" and order_num % 11 == 0:
            con.execute("INSERT INTO fact_return VALUES (?,?,?,?,?)", (oid, 1, f"2025-{month:02d}-{min(day+3,28):02d}", ["damaged","changed_mind","wrong_item"][order_num%3], 18.0+(order_num%5)*4))

con.commit()
con.close()
print(DB)
