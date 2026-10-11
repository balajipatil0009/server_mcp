"""E2E validation on throwaway SQLite (no MySQL needed)."""
import os
os.environ["DB_NAME"] = "__unused_for_sqlite_override__"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# Throwaway SQLite for validation only
engine = create_engine("sqlite:///./_test_validate.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app, raise_server_exceptions=False)

# 1. Create student
r = client.post("/api/v1/students", json={"name": "Aarav Sharma", "phone": "9876543210", "standard": "8-A"})
assert r.status_code == 201, r.text
sid = r.json()["id"]
print("1. create student OK:", r.json())

# 2. Duplicate phone -> 409
r = client.post("/api/v1/students", json={"name": "Dup", "phone": "+91 9876543210", "standard": "8-A"})
assert r.status_code == 409, r.text
print("2. duplicate phone 409 OK")

# 3. Invalid phone -> 422
r = client.post("/api/v1/students", json={"name": "X", "phone": "123", "standard": "8-A"})
assert r.status_code == 422, r.text
print("3. invalid phone 422 OK")

# 4. List + filter + search
r = client.get("/api/v1/students", params={"standard": "8-A", "search": "aarav"})
assert r.status_code == 200 and len(r.json()) == 1, r.text
print("4. list/filter OK")

# 5. Update + get
r = client.put(f"/api/v1/students/{sid}", json={"standard": "8-B"})
assert r.status_code == 200 and r.json()["standard"] == "8-B", r.text
print("5. update OK")

# 6. Marks + bulk
r = client.post("/api/v1/marks", json={"student_id": sid, "subject": "Maths",
                "marks_obtained": 85, "total_marks": 100, "term": "Term1"})
assert r.status_code == 201, r.text
r = client.post("/api/v1/marks/bulk", json={"records": [
    {"student_id": sid, "subject": "Science", "marks_obtained": 70, "total_marks": 100, "term": "Term1"},
    {"student_id": sid, "subject": "English", "marks_obtained": 90, "total_marks": 100, "term": "Term1"}]})
assert r.status_code == 201, r.text
print("6. marks OK")

# 7. Attendance + behaviour + activities
from datetime import date, timedelta
for i in range(10):
    d = (date.today() - timedelta(days=i)).isoformat()
    st = "absent" if i == 0 else "present"
    rr = client.post("/api/v1/attendance", json={"student_id": sid, "date": d, "status": st})
    assert rr.status_code == 201, rr.text
client.post("/api/v1/behaviour", json={"student_id": sid, "score": 8, "remark": "Good"})
client.post("/api/v1/activities", json={"student_id": sid, "activity_name": "Cricket",
             "category": "sports", "points": 50})
print("7. attendance/behaviour/activities OK")

# 8. Aggregated analytics
r = client.get(f"/api/v1/students/{sid}/analytics")
assert r.status_code == 200, r.text
a = r.json()
print("8. analytics:", a["academics"]["average_pct"], a["attendance"]["presenty_pct"],
      a["overall_performance_score"], a["flags"])
assert abs(a["academics"]["average_pct"] - 81.67) < 0.01
assert a["attendance"]["presenty_pct"] == 90.0
assert a["overall_performance_score"] > 0

# 9. Class summary + leaderboard
r = client.get("/api/v1/analytics/class/8-B/summary")
assert r.status_code == 200 and r.json()["students"] == 1, r.text
print("9. class summary:", r.json())
r = client.get("/api/v1/analytics/class/8-B/leaderboard")
assert r.status_code == 200 and r.json()[0]["student_id"] == sid, r.text
print("10. leaderboard OK")

# 11. Delete cascades
r = client.delete(f"/api/v1/students/{sid}")
assert r.status_code == 204, r.text
r = client.get(f"/api/v1/students/{sid}")
assert r.status_code == 404, r.text
print("11. delete OK")

print("\nALL VALIDATION TESTS PASSED")
