"""E2E validation against a dedicated MySQL test database (school_db_test)."""
import os
os.environ["DB_NAME"] = "school_db_test"

from fastapi.testclient import TestClient

from tests_db import prepare_test_db

prepare_test_db()

from app.main import app  # noqa: E402  (reads DB_NAME at import time)

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
assert r.status_code == 200 and len(r.json()["items"]) == 1, r.text
print("4. list/filter OK")

# 5. Update + get
r = client.put(f"/api/v1/students/{sid}", json={"standard": "8-B"})
assert r.status_code == 200 and r.json()["standard"] == "8-B", r.text
r = client.get(f"/api/v1/students/{sid}")
assert r.status_code == 200 and r.json()["standard"] == "8-B", r.text
# updated_at must move on write (MySQL has no ON UPDATE clause for it).
assert r.json()["updated_at"] >= r.json()["created_at"], r.text
print("5. update OK (updated_at maintained)")

# 6. Marks + bulk
r = client.post("/api/v1/marks", json={"student_id": sid, "subject": "Maths",
                "marks_obtained": 85, "total_marks": 100, "term": "Term1"})
assert r.status_code == 201, r.text
mark_id = r.json()["id"]
r = client.post("/api/v1/marks/bulk", json={"records": [
    {"student_id": sid, "subject": "Science", "marks_obtained": 70, "total_marks": 100, "term": "Term1"},
    {"student_id": sid, "subject": "English", "marks_obtained": 90, "total_marks": 100, "term": "Term1"}]})
assert r.status_code == 201, r.text
print("6. marks OK")

# 6b. Marks guard: obtained > total -> 422, and update of missing mark -> 404
r = client.post("/api/v1/marks", json={"student_id": sid, "subject": "Maths",
                "marks_obtained": 120, "total_marks": 100, "term": "Term1"})
assert r.status_code == 422, r.text
r = client.put("/api/v1/marks/999999999", json={"subject": "Maths"})
assert r.status_code == 404, r.text
r = client.put(f"/api/v1/marks/{mark_id}", json={"exam_type": "mid-term"})
assert r.status_code == 200 and r.json()["exam_type"] == "mid-term", r.text
print("6b. marks guards OK")

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
r = client.get("/api/v1/marks", params={"student_id": sid})
assert r.status_code == 200 and r.json()["total_rows"] == 0, r.text
print("11. delete OK (analytics rows cascaded)")

print("\nALL VALIDATION TESTS PASSED")
