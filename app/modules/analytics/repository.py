from datetime import date
from typing import List, Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Session

from app.modules.analytics.model import (
    ActivityCategory,
    Attendance,
    AttendanceStatus,
    Behaviour,
    CurriculumActivity,
    Mark,
)


class AnalyticsRepository:
    """DB layer for all analytics tables + read queries for aggregation."""

    def __init__(self, db: Session):
        self.db = db

    # ---- marks ----
    def add_mark(self, **fields) -> Mark:
        obj = Mark(**fields)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add_marks_bulk(self, rows: List[dict]) -> List[Mark]:
        objs = [Mark(**r) for r in rows]
        self.db.add_all(objs)
        self.db.commit()
        for o in objs:
            self.db.refresh(o)
        return objs

    def get_mark(self, mark_id: int) -> Optional[Mark]:
        return self.db.query(Mark).filter(Mark.id == mark_id).first()

    def list_marks(self, student_id: int, term: Optional[str] = None) -> List[Mark]:
        q = self.db.query(Mark).filter(Mark.student_id == student_id)
        if term:
            q = q.filter(Mark.term == term)
        return q.order_by(Mark.exam_date.desc(), Mark.id.desc()).all()

    def list_marks_paged(self, student_id: int, term: Optional[str] = None,
                         page: int = 1, size: int = 50):
        q = self.db.query(Mark).filter(Mark.student_id == student_id)
        if term:
            q = q.filter(Mark.term == term)
        total_rows = q.count()
        rows = (q.order_by(Mark.exam_date.desc(), Mark.id.desc())
                .offset((page - 1) * size).limit(size).all())
        return rows, total_rows

    def update_mark(self, obj: Mark, **fields) -> Mark:
        for k, v in fields.items():
            if v is not None and hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_mark(self, obj: Mark) -> None:
        self.db.delete(obj)
        self.db.commit()

    # ---- attendance ----
    def mark_attendance(self, *, student_id: int, date: date, status: AttendanceStatus) -> Attendance:
        existing = (
            self.db.query(Attendance)
            .filter(Attendance.student_id == student_id, Attendance.date == date)
            .first()
        )
        if existing:
            existing.status = status
            self.db.commit()
            self.db.refresh(existing)
            return existing
        obj = Attendance(student_id=student_id, date=date, status=status)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add_attendance_bulk(self, rows: List[dict]) -> List[Attendance]:
        out = []
        for r in rows:
            out.append(
                self.mark_attendance(
                    student_id=r["student_id"], date=r["date"], status=r.get("status", AttendanceStatus.present)
                )
            )
        return out

    def get_attendance(self, record_id: int) -> Optional[Attendance]:
        return self.db.query(Attendance).filter(Attendance.id == record_id).first()

    def list_attendance(self, student_id: int) -> List[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.student_id == student_id)
            .order_by(Attendance.date.desc())
            .all()
        )

    def list_attendance_paged(self, student_id: int, page: int = 1, size: int = 50):
        q = (self.db.query(Attendance)
             .filter(Attendance.student_id == student_id))
        total_rows = q.count()
        rows = (q.order_by(Attendance.date.desc())
                .offset((page - 1) * size).limit(size).all())
        return rows, total_rows

    def update_attendance(self, obj: Attendance, **fields) -> Attendance:
        for k, v in fields.items():
            if v is not None and hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_attendance(self, obj: Attendance) -> None:
        self.db.delete(obj)
        self.db.commit()

    # ---- behaviour ----
    def add_behaviour(self, **fields) -> Behaviour:
        obj = Behaviour(**fields)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_behaviour(self, record_id: int) -> Optional[Behaviour]:
        return self.db.query(Behaviour).filter(Behaviour.id == record_id).first()

    def list_behaviour(self, student_id: int) -> List[Behaviour]:
        return (
            self.db.query(Behaviour)
            .filter(Behaviour.student_id == student_id)
            .order_by(Behaviour.date.desc(), Behaviour.id.desc())
            .all()
        )

    def list_behaviour_paged(self, student_id: int, page: int = 1, size: int = 50):
        q = (self.db.query(Behaviour)
             .filter(Behaviour.student_id == student_id))
        total_rows = q.count()
        rows = (q.order_by(Behaviour.date.desc(), Behaviour.id.desc())
                .offset((page - 1) * size).limit(size).all())
        return rows, total_rows

    def update_behaviour(self, obj: Behaviour, **fields) -> Behaviour:
        for k, v in fields.items():
            if v is not None and hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_behaviour(self, obj: Behaviour) -> None:
        self.db.delete(obj)
        self.db.commit()

    # ---- activities ----
    def add_activity(self, **fields) -> CurriculumActivity:
        obj = CurriculumActivity(**fields)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_activity(self, record_id: int) -> Optional[CurriculumActivity]:
        return self.db.query(CurriculumActivity).filter(CurriculumActivity.id == record_id).first()

    def list_activities(self, student_id: int) -> List[CurriculumActivity]:
        return (
            self.db.query(CurriculumActivity)
            .filter(CurriculumActivity.student_id == student_id)
            .order_by(CurriculumActivity.date.desc(), CurriculumActivity.id.desc())
            .all()
        )

    def list_activities_paged(self, student_id: int, page: int = 1, size: int = 50):
        q = (self.db.query(CurriculumActivity)
             .filter(CurriculumActivity.student_id == student_id))
        total_rows = q.count()
        rows = (q.order_by(CurriculumActivity.date.desc(), CurriculumActivity.id.desc())
                .offset((page - 1) * size).limit(size).all())
        return rows, total_rows

    def update_activity(self, obj: CurriculumActivity, **fields) -> CurriculumActivity:
        for k, v in fields.items():
            if v is not None and hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_activity(self, obj: CurriculumActivity) -> None:
        self.db.delete(obj)
        self.db.commit()
