from collections import defaultdict
from typing import List, Optional

from app.modules.analytics import schemas
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.students.repository import StudentRepository
from app.modules.students.service import StudentNotFoundError


def grade_for(pct: float) -> str:
    if pct >= 90:
        return "A+"
    if pct >= 80:
        return "A"
    if pct >= 70:
        return "B"
    if pct >= 60:
        return "C"
    if pct >= 40:
        return "D"
    return "F"


class AnalyticsService:
    """Aggregation + business rules. Controllers stay thin."""

    W_ACADEMICS = 0.60
    W_ATTENDANCE = 0.20
    W_BEHAVIOUR = 0.10
    W_CURRICULUM = 0.10

    def __init__(self, conn):
        self.conn = conn
        self.repo = AnalyticsRepository(conn)
        self.students = StudentRepository(conn)

    def _require_student(self, student_id: int) -> dict:
        obj = self.students.get_by_id(student_id)
        if not obj:
            raise StudentNotFoundError(f"student {student_id} not found")
        return obj

    def _academics(self, student_id: int, term: Optional[str]):
        marks = self.repo.list_marks(student_id, term)
        if not marks:
            return schemas.AcademicsSummary(
                average_pct=0.0, grade="N/A", total_exams=0,
                subject_wise=[], trend_by_term={},
            )
        per_subject = defaultdict(list)
        per_term = defaultdict(list)
        total_pct = 0.0
        for m in marks:
            pct = (m["marks_obtained"] / m["total_marks"] * 100) if m["total_marks"] else 0
            per_subject[m["subject"]].append(pct)
            per_term[m["term"]].append(pct)
            total_pct += pct
        avg = round(total_pct / len(marks), 2)
        subject_wise = [
            schemas.SubjectStat(subject=s, average_pct=round(sum(v) / len(v), 2), exams=len(v))
            for s, v in sorted(per_subject.items())
        ]
        trend = {t: round(sum(v) / len(v), 2) for t, v in sorted(per_term.items())}
        return schemas.AcademicsSummary(
            average_pct=avg, grade=grade_for(avg), total_exams=len(marks),
            subject_wise=subject_wise, trend_by_term=trend,
        )

    def _attendance(self, student_id: int):
        rows = self.repo.list_attendance(student_id)
        present = sum(1 for r in rows if r["status"] == schemas.AttendanceStatus.present.value)
        absent = sum(1 for r in rows if r["status"] == schemas.AttendanceStatus.absent.value)
        leave = sum(1 for r in rows if r["status"] == schemas.AttendanceStatus.leave.value)
        pct = round(present / len(rows) * 100, 2) if rows else 0.0
        return schemas.AttendanceSummary(
            total=len(rows), present=present, absent=absent,
            leave=leave, presenty_pct=pct,
        )

    def _behaviour(self, student_id: int):
        rows = self.repo.list_behaviour(student_id)
        if not rows:
            return schemas.BehaviourSummary(
                average_score=0.0, total_records=0, latest_remarks=[]
            )
        avg = round(sum(r["score"] for r in rows) / len(rows), 2)
        remarks = [r["remark"] for r in rows[:5] if r["remark"]]
        return schemas.BehaviourSummary(
            average_score=avg, total_records=len(rows), latest_remarks=remarks
        )

    def _curriculum(self, student_id: int):
        rows = self.repo.list_activities(student_id)
        by_cat = defaultdict(int)
        for r in rows:
            by_cat[str(r["category"])] += r["points"]
        return schemas.CurriculumSummary(
            total_points=sum(r["points"] for r in rows),
            total_activities=len(rows),
            by_category=dict(by_cat),
        )

    def get_student_analytics(self, student_id: int, term=None):
        student = self._require_student(student_id)
        academics = self._academics(student_id, term)
        attendance = self._attendance(student_id)
        behaviour = self._behaviour(student_id)
        curriculum = self._curriculum(student_id)
        behaviour_pct = behaviour.average_score * 10
        curriculum_pct = min(curriculum.total_points, 100)
        overall = round(
            academics.average_pct * self.W_ACADEMICS
            + attendance.presenty_pct * self.W_ATTENDANCE
            + behaviour_pct * self.W_BEHAVIOUR
            + curriculum_pct * self.W_CURRICULUM, 2)
        flags: List[str] = []
        if academics.average_pct >= 85:
            flags.append("academic-excellent")
        if attendance.presenty_pct < 75 and attendance.total > 0:
            flags.append("low-attendance")
        if academics.average_pct < 40 and academics.total_exams > 0:
            flags.append("at-risk-academics")
        if behaviour.average_score and behaviour.average_score < 5:
            flags.append("behaviour-concern")
        if curriculum.total_points >= 100:
            flags.append("all-rounder")
        if not flags:
            flags.append("steady")
        return schemas.StudentAnalyticsResponse(
            student_id=student["id"], student_name=student["name"],
            standard=student["standard"], term=term, academics=academics,
            attendance=attendance, behaviour=behaviour,
            curriculum=curriculum, overall_performance_score=overall,
            flags=flags)

    def get_class_summary(self, standard: str):
        students = self.students.list(standard=standard, page=1, size=100000)[0]
        if not students:
            return schemas.ClassSummaryResponse(
                standard=standard, students=0, class_average_pct=0.0,
                class_attendance_pct=0.0, topper=None, at_risk=[])
        scored = [self.get_student_analytics(s["id"]) for s in students]
        avg_pct = round(sum(x.academics.average_pct for x in scored) / len(scored), 2)
        avg_att = round(sum(x.attendance.presenty_pct for x in scored) / len(scored), 2)
        top = max(scored, key=lambda x: x.overall_performance_score)
        at_risk = [
            {"student_id": x.student_id, "student_name": x.student_name,
             "average_pct": x.academics.average_pct,
             "presenty_pct": x.attendance.presenty_pct}
            for x in scored
            if x.academics.average_pct < 40 or x.attendance.presenty_pct < 75]
        return schemas.ClassSummaryResponse(
            standard=standard, students=len(students),
            class_average_pct=avg_pct, class_attendance_pct=avg_att,
            topper={"student_id": top.student_id,
                    "student_name": top.student_name,
                    "score": top.overall_performance_score},
            at_risk=at_risk)

    def get_leaderboard(self, standard: str, limit: int = 10):
        students = self.students.list(standard=standard, page=1, size=100000)[0]
        ranked = sorted(
            (self.get_student_analytics(s["id"]) for s in students),
            key=lambda x: x.overall_performance_score, reverse=True)
        return [
            {"rank": i + 1, "student_id": r.student_id,
             "student_name": r.student_name,
             "overall_performance_score": r.overall_performance_score,
             "average_pct": r.academics.average_pct,
             "presenty_pct": r.attendance.presenty_pct}
            for i, r in enumerate(ranked[:limit])]
