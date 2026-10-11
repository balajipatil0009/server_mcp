import enum
from datetime import date
from datetime import date as date_cls  # aliased binding: a field literally named "date"
                                     # typed as Optional[date] breaks inside a
                                     # parametrized generic (Page[T]) in pydantic v2.
                                     # Annotating with the alias keeps the field name,
                                     # JSON key, and DB column all as "date".
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator

from app.modules.students.schemas import Page  # re-export for controller use

__all__ = ["Page", "AttendanceStatus", "ActivityCategory"]


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    leave = "leave"


class ActivityCategory(str, enum.Enum):
    sports = "sports"
    arts = "arts"
    tech = "tech"
    academics_club = "academics_club"
    social = "social"
    other = "other"

# ---------- Marks ----------

class MarkCreate(BaseModel):
    student_id: int
    subject: str
    marks_obtained: float
    total_marks: float = 100
    exam_type: str = "unit-test"
    term: str = "Term1"
    exam_date: Optional[date] = None

    @field_validator("marks_obtained", "total_marks")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("marks cannot be negative")
        return v


class MarkUpdate(BaseModel):
    subject: Optional[str] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None
    exam_type: Optional[str] = None
    term: Optional[str] = None
    exam_date: Optional[date] = None


class MarkResponse(MarkCreate):
    id: int


class MarkBulkCreate(BaseModel):
    records: List[MarkCreate]


# ---------- Attendance ----------

class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus = AttendanceStatus.present


class AttendanceUpdate(BaseModel):
    date: Optional[date] = None
    status: Optional[AttendanceStatus] = None


class AttendanceResponse(AttendanceCreate):
    id: int


class AttendanceBulkCreate(BaseModel):
    records: List[AttendanceCreate]


# ---------- Behaviour ----------

class BehaviourCreate(BaseModel):
    student_id: int
    score: int
    remark: Optional[str] = None
    observed_by: Optional[str] = None
    date: Optional[date_cls] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("behaviour score must be 1-10")
        return v


class BehaviourUpdate(BaseModel):
    score: Optional[int] = None
    remark: Optional[str] = None
    observed_by: Optional[str] = None
    date: Optional[date_cls] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 1 <= v <= 10:
            raise ValueError("behaviour score must be 1-10")
        return v


class BehaviourResponse(BehaviourCreate):
    id: int


# ---------- Curriculum ----------

class ActivityCreate(BaseModel):
    student_id: int
    activity_name: str
    category: ActivityCategory = ActivityCategory.other
    points: int = 0
    achievement: Optional[str] = None
    date: Optional[date_cls] = None

    @field_validator("points")
    @classmethod
    def points_ok(cls, v: int) -> int:
        if v < 0:
            raise ValueError("points cannot be negative")
        return v


class ActivityUpdate(BaseModel):
    activity_name: Optional[str] = None
    category: Optional[ActivityCategory] = None
    points: Optional[int] = None
    achievement: Optional[str] = None
    date: Optional[date_cls] = None


class ActivityResponse(ActivityCreate):
    id: int


# ---------- Analytics read models ----------

class SubjectStat(BaseModel):
    subject: str
    average_pct: float
    exams: int


class AcademicsSummary(BaseModel):
    average_pct: float
    grade: str
    total_exams: int
    subject_wise: List[SubjectStat]
    trend_by_term: Dict[str, float]


class AttendanceSummary(BaseModel):
    total: int
    present: int
    absent: int
    leave: int
    presenty_pct: float  # kept your spelling alias for present %


class BehaviourSummary(BaseModel):
    average_score: float
    total_records: int
    latest_remarks: List[str]


class CurriculumSummary(BaseModel):
    total_points: int
    total_activities: int
    by_category: Dict[str, int]


class StudentAnalyticsResponse(BaseModel):
    student_id: int
    student_name: str
    standard: str
    term: Optional[str] = None
    academics: AcademicsSummary
    attendance: AttendanceSummary
    behaviour: BehaviourSummary
    curriculum: CurriculumSummary
    overall_performance_score: float
    flags: List[str]


class ClassSummaryResponse(BaseModel):
    standard: str
    students: int
    class_average_pct: float
    class_attendance_pct: float
    topper: Optional[dict] = None
    at_risk: List[dict]
