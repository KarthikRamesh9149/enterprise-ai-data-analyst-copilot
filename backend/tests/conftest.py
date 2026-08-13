from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base  # noqa: E402
from app.db.models import User
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "test-only-jwt-secret-with-at-least-32-characters")
    monkeypatch.setattr("app.core.config.settings.upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.core.config.settings.duckdb_path", str(tmp_path / "analytics.duckdb"))
    monkeypatch.setattr("app.core.config.settings.sql_generator_provider", "mock")
    monkeypatch.setattr("app.core.config.settings.report_generator_provider", "mock")
    return TestClient(app)


def seed_and_login(client: TestClient, db: Session, email: str, role: str) -> str:
    db.add(User(email=email, role=role, hashed_password=hash_password("DemoPassword123!")))
    db.commit()
    response = client.post("/auth/login", json={"email": email, "password": "DemoPassword123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def tokens(client: TestClient, db: Session):
    return {
        "admin": seed_and_login(client, db, "admin@example.com", "admin"),
        "analyst": seed_and_login(client, db, "analyst@example.com", "analyst"),
        "reviewer": seed_and_login(client, db, "reviewer@example.com", "reviewer"),
        "viewer": seed_and_login(client, db, "viewer@example.com", "viewer"),
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def churn_csv() -> bytes:
    return b"""customer_id,signup_date,plan_type,monthly_revenue,total_revenue,contract_type,tenure_months,support_tickets,usage_minutes,feature_usage_score,payment_failures,region,customer_segment,churned,churn_date
CUST-1,2024-01-01,starter,49,588,month-to-month,12,5,120,20,2,NA,smb,1,2025-01-01
CUST-2,2023-01-01,growth,149,3576,annual,24,0,800,88,0,EMEA,mid-market,0,
CUST-3,2022-06-01,enterprise,899,32364,multi-year,36,1,1200,92,0,APAC,enterprise,0,
CUST-4,2024-03-01,starter,49,196,month-to-month,4,6,160,28,3,NA,smb,1,2024-07-01
CUST-5,2023-05-01,growth,149,1937,annual,13,2,640,72,0,LATAM,mid-market,0,
CUST-6,2024-02-01,starter,49,245,month-to-month,5,4,240,37,1,APAC,smb,0,
CUST-7,2021-02-01,enterprise,899,43152,multi-year,48,0,1300,96,0,NA,enterprise,0,
CUST-8,2023-08-01,growth,149,1490,month-to-month,10,3,360,49,1,EMEA,mid-market,1,2024-06-01
CUST-9,2022-01-01,starter,49,1176,annual,24,1,610,70,0,LATAM,smb,0,
CUST-10,2022-09-01,growth,149,2980,annual,20,0,770,80,0,NA,mid-market,0,
CUST-11,2024-04-01,starter,49,147,month-to-month,3,7,100,15,2,EMEA,smb,1,2024-07-01
CUST-12,2023-11-01,enterprise,899,12586,annual,14,1,970,90,0,APAC,enterprise,0,
"""
