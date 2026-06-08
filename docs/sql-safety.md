# SQL Safety

Allowed: single `SELECT` or `WITH` query referencing the selected DuckDB dataset table.

Blocked: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `COPY`, `ATTACH`, `INSTALL`, `LOAD`, `PRAGMA`, `read_csv`, `read_parquet`, multiple statements, external file access, unknown tables/columns, and sensitive columns such as email, phone, SSN, passwords, tokens, or credit cards.

Safe example: `SELECT customer_segment, AVG(churned) AS churn_rate FROM ds_customer_churn_x GROUP BY customer_segment LIMIT 25`.

Unsafe example: `DROP TABLE users;`.

Even safe SQL requires reviewer/admin approval before execution.
