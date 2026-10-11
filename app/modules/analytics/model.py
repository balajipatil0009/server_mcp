import enum
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


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


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=100)
    exam_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unit-test")
    term: Mapped[str] = mapped_column(String(20), nullable=False, default="Term1")
    exam_date: Mapped[date_type] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student = relationship("Student", back_populates="marks")


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.present
    )

    student = relationship("Student", back_populates="attendance_records")

    __table_args__ = ({"mysql_engine": "InnoDB"},)


class Behaviour(Base):
    __tablename__ = "behaviour"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-10
    remark: Mapped[str] = mapped_column(Text, nullable=True)
    observed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student = relationship("Student", back_populates="behaviour_records")


class CurriculumActivity(Base):
    __tablename__ = "curriculum_activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[ActivityCategory] = mapped_column(
        Enum(ActivityCategory), nullable=False, default=ActivityCategory.other
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    achievement: Mapped[str] = mapped_column(String(150), nullable=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=True)

    student = relationship("Student", back_populates="activities")
