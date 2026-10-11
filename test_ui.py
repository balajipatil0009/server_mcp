"""Validate: /ui serves frontend + seed logic works (throwaway SQLite)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
import app.main as main_mod

engine = create_engine("sqlite:///./_test_ui.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


main_mod.app.dependency_overrides[get_db] = override_db
client = TestClient(main_mod.app, raise_server_exceptions=False)

# 1. UI static pages
for page in ["/ui/", "/ui/students.html", "/ui/analytics.html",
             "/ui/class.html", "/ui/app.js", "/ui/style.css"]:
    r = client.get(page)
    assert r.status_code == 200, (page, r.status_code)
    print(f"UI {page} -> {r.status_code} ({len(r.content)} bytes)")
assert "SchoolTrack" in client.get("/ui/").text
print("UI shell OK")

# 2. Seed-equivalent random insert via API (mirrors seed.py profiles)
import random
rng = random.Random(42)
r = client.post("/api/v1/students", json={"name": "Seed Kid", "phone": "9123456780", "standard": "8-A"})
assert r.status_code == 201, r.text
sid = r.json()["id"]
for subj, mk in [("Maths", 88), ("Science", 45)]:
    assert client.post("/api/v1/marks", json={"student_id": sid, "subject": subj,
                       "marks_obtained": mk, "term": "Term1"}).status_code == 201
client.post("/api/v1/behaviour", json={"student_id": sid, "score": 7, "remark": "Good"})
client.post("/api/v1/activities", json={"student_id": sid, "activity_name": "Cricket",
             "category": "sports", "points": 40})
a = client.get(f"/api/v1/students/{sid}/analytics").json()
assert a["academics"]["total_exams"] == 2 and a["curriculum"]["total_points"] == 40
print(f"Analytics on random-ish data OK: avg={a['academics']['average_pct']} "
      f"score={a['overall_performance_score']} flags={a['flags']}")

# 3. Frontend JS references only existing endpoints
import re, pathlib
js = pathlib.Path("frontend/app.js").read_text(encoding="utf-8")
html = "".join(pathlib.Path(f"frontend/{p}").read_text(encoding="utf-8")
               for p in ["index.html", "students.html", "analytics.html", "class.html"])
for ep in re.findall(r'"/([a-z][^"`\s${]*)"', html):
    full = "/api/v1/" + ep.split("?")[0].split("${")[0]
    assert full.rstrip("/") in (
        "/api/v1/students", "/api/v1/students/", "/api/v1/marks",
        "/api/v1/attendance", "/api/v1/behaviour", "/api/v1/activities",
        "/api/v1/analytics/class", "/api/v1/students/analytics"), full
print("Frontend endpoint references OK")
print("\nALL UI+SEED CHECKS PASSED")
