from pathlib import Path
import os
import sys

script_root = Path(__file__).resolve().parent.parent

db_path = script_root / "test_ats_integration.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
sys.path.insert(0, str(script_root / "src"))

from fastapi.testclient import TestClient
from app.main import app

if __name__ == "__main__":
    if db_path.exists():
        db_path.unlink()

    payload = {
        "event": "candidate_created",
        "data": {
            "candidate": {
                "id": "123",
                "name": "Jane Doe",
                "resume_url": "https://example.com/resume.pdf",
            }
        }
    }
    headers = {
        "X-Api-Key": "sk_test_company_123",
        "X-Company-Id": "company_123",
    }

    with TestClient(app) as client:
        response = client.post("/api/webhooks/workable", json=payload, headers=headers)
        print("status_code=", response.status_code)
        print("json=", response.json())
