from __future__ import annotations

from app.core.security import hash_password
from app.db.base import Base
from app.db.models import User
from app.db.session import SessionLocal, engine

DEMO_USERS = [
    ("admin@example.com", "admin"),
    ("analyst@example.com", "analyst"),
    ("reviewer@example.com", "reviewer"),
    ("viewer@example.com", "viewer"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for email, role in DEMO_USERS:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.role = role
                user.hashed_password = hash_password("DemoPassword123!")
            else:
                db.add(User(email=email, role=role, hashed_password=hash_password("DemoPassword123!")))
        db.commit()
        print("Seeded demo users with password DemoPassword123! (local development only).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
