"""Seed RANDOM demo data: configurable counts, repeatable via --seed.

Usage:
    python seed.py                       # 25 students, fresh random
    python seed.py --students 40 --days 60 --seed 7
    python seed.py --reset               # wipe analytics+students first
"""
import argparse
import random
from datetime import date, timedelta

from app.core.database import Base, SessionLocal, engine
from app.modules.analytics.model import ActivityCategory, AttendanceStatus
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.students.schemas import StudentCreate
from app.modules.students.service import StudentService

FIRST = ["Aarav", "Diya", "Kabir", "Ananya", "Vivaan", "Ishaan", "Myra",
         "Aditya", "Sara", "Arjun", "Navya", "Krishna", "Riya", "Aadhya",
         "Rohan", "Priya", "Karan", "Sneha", "Yash", "Pooja", "Dev",
         "Meera", "Rahul", "Kavya", "Aryan", "Tanvi", "Nikhil", "Shreya"]
LAST = ["Sharma", "Patel", "Singh", "Gupta", "Mehta", "Reddy", "Iyer",
        "Khan", "Nair", "Das", "Kulkarni", "Joshi", "Verma", "Agarwal"]
STANDARDS = ["6-A", "6-B", "7-A", "7-B", "8-A", "8-B", "9-A", "10-A"]
SUBJECTS = ["Maths", "Science", "English", "Hindi", "Social Science", "Computer"]
EXAMS = ["unit-test", "mid-term", "final"]
TERMS = ["Term1", "Term2"]
GOOD = ["Very disciplined", "Helped juniors", "Excellent participation",
        "Great teamwork", "Very punctual", "Creative thinker"]
BAD = ["Needs focus in class", "Homework pending twice",
       "Talkative in class", "Needs improvement in discipline"]
ACTS = [("Inter-school Cricket", ActivityCategory.sports, 50),
        ("Drawing Competition", ActivityCategory.arts, 30),
        ("Robotics Workshop", ActivityCategory.tech, 40),
        ("Science Exhibition", ActivityCategory.tech, 30),
        ("Football League", ActivityCategory.sports, 40),
        ("Music Fest", ActivityCategory.arts, 25),
        ("Debate Club", ActivityCategory.academics_club, 20),
        ("Tree Plantation Drive", ActivityCategory.social, 15),
        ("Quiz Olympiad", ActivityCategory.academics_club, 35)]


def gen_phone(rng, used):
    while True:
        p = f"{rng.choice('6789')}{rng.randint(100000000, 999999999)}"
        if p not in used:
            used.add(p)
            return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=25)
    ap.add_argument("--per-class", type=str, default=None,
                    help="e.g. '6-A:30,7-A:30,8-A:30,9-A:30' (overrides --students)")
    ap.add_argument("--days", type=int, default=45)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        svc = StudentService(db)
        repo = AnalyticsRepository(db)
        if args.reset:
            from app.modules.analytics.model import (Attendance, Behaviour,
                                                     CurriculumActivity, Mark)
            from app.modules.students.model import Student
            for m in (Mark, Attendance, Behaviour, CurriculumActivity):
                db.query(m).delete()
            db.query(Student).delete()
            db.commit()
            print("Reset: wiped all data")
        used = {s.phone for s in db.query(
            __import__("app.modules.students.model",
                       fromlist=["Student"]).Student).all()}
        today = date.today()
        profiles = ["topper", "average", "struggler", "sporty", "irregular"]

        # Build (standard, count) plan: --per-class wins over --students
        if args.per_class:
            plan = []
            for chunk in args.per_class.split(","):
                std, cnt = chunk.strip().split(":")
                plan.append((std.strip(), int(cnt)))
        else:
            plan = [(None, args.students)]  # None = random standard

        def seed_one(forced_std):
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            profile = rng.choice(profiles)
            sid = svc.create_student(StudentCreate(
                name=name, phone=gen_phone(rng, used),
                standard=forced_std or rng.choice(STANDARDS))).id
            base = {"topper": rng.uniform(82, 97),
                    "struggler": rng.uniform(28, 52),
                    "sporty": rng.uniform(55, 72)}.get(
                        profile, rng.uniform(60, 82))
            for term in TERMS:
                for subj in rng.sample(SUBJECTS, rng.randint(4, 6)):
                    for exam in rng.sample(EXAMS, rng.randint(1, 2)):
                        repo.add_mark(
                            student_id=sid, subject=subj,
                            marks_obtained=round(max(
                                0, min(100, rng.gauss(base, 9))), 1),
                            total_marks=100, exam_type=exam, term=term,
                            exam_date=today - timedelta(
                                days=rng.randint(0, 180)))
            absent = {"topper": 0.03, "average": 0.08,
                      "struggler": 0.22, "sporty": 0.10}.get(profile, 0.30)
            for i in range(args.days):
                d = today - timedelta(days=i)
                if d.weekday() == 6:
                    continue
                r = rng.random()
                st = (AttendanceStatus.absent if r < absent
                      else AttendanceStatus.leave
                      if r < absent + 0.03
                      else AttendanceStatus.present)
                repo.mark_attendance(student_id=sid, date=d, status=st)
            for _ in range(rng.randint(2, 5)):
                bad = profile == "struggler" and rng.random() < 0.4
                repo.add_behaviour(
                    student_id=sid,
                    score=rng.randint(3, 5) if bad else rng.randint(6, 10),
                    remark=rng.choice(BAD) if bad else rng.choice(GOOD),
                    observed_by=rng.choice(
                        ["Class Teacher", "Sports Sir", "Principal"]),
                    date=today - timedelta(days=rng.randint(0, 90)))
            na = (rng.randint(2, 5) if profile == "sporty"
                  else rng.randint(0, 4))
            for nm, cat, pts in rng.sample(ACTS, min(na, len(ACTS))):
                repo.add_activity(
                    student_id=sid, activity_name=nm, category=cat,
                    points=pts + rng.randint(-5, 15),
                    achievement=rng.choice(
                        [None, "Participant", "Winner", "Runner-up"]),
                    date=today - timedelta(days=rng.randint(0, 180)))
            return sid

        n = 0
        for forced_std, cnt in plan:
            for _ in range(cnt):
                seed_one(forced_std)
                n += 1
        print(f"Seeded {n} random students (seed={args.seed}). "
              "Open http://127.0.0.1:8000/ui/ to browse.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

