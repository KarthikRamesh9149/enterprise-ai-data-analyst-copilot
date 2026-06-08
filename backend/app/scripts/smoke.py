from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    response = client.get("/health")
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
