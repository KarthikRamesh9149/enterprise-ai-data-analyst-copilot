# Demo Script

1. Open dashboard and log in as `analyst@example.com` with `DemoPassword123!`.
2. Upload `demo-data/customer_churn.csv`.
3. Validate, inspect schema, profile, sample rows, and data quality score.
4. Load the dataset to DuckDB.
5. Ask “Which customer segments have the highest churn rate?”.
6. Show generated SQL, safety result, and approval requirement.
7. Log in as reviewer/admin or use approvals page to approve SQL.
8. Execute SQL and show result table/chart.
9. Ask “Which customers are at risk?” and open Modeling.
10. Train churn model; show metrics, feature importance, and risk scores.
11. Upload `demo-data/monthly_revenue.csv` and forecast revenue for 3 months.
12. Generate executive report.
13. Show approval queue, MLflow at `http://localhost:5000`, evaluation dashboard, audit logs, and admin observability.
14. Explain local-first boundaries and future Supabase/deployment plans.
