from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Student(Base):
    """Lean student table: only name, phone, standard (+ ids/timestamps)."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(15), nullable=False, unique=True, index=True)
    standard: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships (cascade so deleting a student cleans analytics)
    marks = relationship("Mark", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )
    behaviour_records = relationship(
        "Behaviour", back_populates="student", cascade="all, delete-orphan"
    )
    activities = relationship(
        "CurriculumActivity", back_populates="student", cascade="all, delete-orphan"
    )
