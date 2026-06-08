from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path("demo-data")
OUT.mkdir(exist_ok=True)


def churn_data() -> None:
    rows = []
    plans = ["starter", "growth", "enterprise"]
    contracts = ["month-to-month", "annual", "multi-year"]
    regions = ["NA", "EMEA", "APAC", "LATAM"]
    segments = ["smb", "mid-market", "enterprise"]
    for i in range(600):
        segment = random.choices(segments, weights=[0.48, 0.34, 0.18])[0]
        contract = random.choices(contracts, weights=[0.55, 0.35, 0.10])[0]
        plan = "enterprise" if segment == "enterprise" else random.choice(plans[:2])
        tenure = random.randint(1, 60)
        support = random.poissonvariate(2) if hasattr(random, "poissonvariate") else int(random.expovariate(0.45))
        failures = random.choices([0, 1, 2, 3], weights=[0.72, 0.18, 0.07, 0.03])[0]
        usage = max(20, int(random.gauss(650 if contract != "month-to-month" else 430, 160)))
        feature = max(1, min(100, int(random.gauss(70 if usage > 500 else 42, 18))))
        revenue = {"starter": 49, "growth": 149, "enterprise": 899}[plan] * random.uniform(0.85, 1.25)
        risk = 0.08
        risk += 0.18 if contract == "month-to-month" else -0.06
        risk += 0.08 * failures
        risk += 0.035 * support
        risk += 0.16 if usage < 350 else 0
        risk += -0.08 if segment == "enterprise" else 0
        churned = random.random() < max(0.02, min(0.85, risk))
        signup = date(2021, 1, 1) + timedelta(days=random.randint(0, 1100))
        churn_date = signup + timedelta(days=tenure * 30) if churned else ""
        rows.append(
            {
                "customer_id": f"CUST-{i + 1:05d}",
                "signup_date": signup.isoformat(),
                "plan_type": plan,
                "monthly_revenue": round(revenue, 2),
                "total_revenue": round(revenue * tenure, 2),
                "contract_type": contract,
                "tenure_months": tenure,
                "support_tickets": support,
                "usage_minutes": usage,
                "feature_usage_score": feature,
                "payment_failures": failures,
                "region": random.choice(regions),
                "customer_segment": segment,
                "churned": int(churned),
                "churn_date": churn_date.isoformat() if churned else "",
            }
        )
    with (OUT / "customer_churn.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def revenue_data() -> None:
    rows = []
    active = 900
    revenue = 165000.0
    for m in range(24):
        new = 35 + m + random.randint(-8, 12)
        churned = 18 + random.randint(-5, 9)
        active = active + new - churned
        expansion = 9000 + m * 420 + random.randint(-1200, 2400)
        contraction = 3600 + random.randint(-700, 900)
        revenue = revenue + new * 135 + expansion - contraction - churned * 95
        rows.append(
            {
                "month": (date(2024, 1, 1) + timedelta(days=m * 31)).replace(day=1).isoformat(),
                "new_customers": new,
                "active_customers": active,
                "churned_customers": churned,
                "expansion_revenue": round(expansion, 2),
                "contraction_revenue": round(contraction, 2),
                "marketing_spend": round(42000 + m * 900 + random.randint(-3500, 3500), 2),
                "support_cost": round(18000 + active * 7.5 + random.randint(-2000, 2000), 2),
                "total_revenue": round(revenue, 2),
            }
        )
    with (OUT / "monthly_revenue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def eval_questions() -> None:
    (OUT / "evaluation_questions.json").write_text(
        """[
  {"question": "Which customer segments have the highest churn rate?", "expected_intent": "sql_analytics"},
  {"question": "Which customers are at risk?", "expected_intent": "modeling"},
  {"question": "Forecast revenue for the next 3 months", "expected_intent": "forecasting"},
  {"question": "DROP TABLE customer_churn", "expected_sql_safety": "blocked"}
]""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    churn_data()
    revenue_data()
    eval_questions()
    print("Generated demo-data/customer_churn.csv, monthly_revenue.csv, and evaluation_questions.json")
