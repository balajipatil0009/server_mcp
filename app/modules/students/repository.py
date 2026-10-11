from typing import Optional

from sqlalchemy.orm import Session

from app.modules.students.model import Student


class StudentRepository:
    """DB layer only - no validation, no HTTP. Pure SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, *, name: str, phone: str, standard: str) -> Student:
        obj = Student(name=name, phone=phone, standard=standard)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return self.db.query(Student).filter(Student.id == student_id).first()

    def get_by_phone(self, phone: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.phone == phone).first()

    def count(self, *, standard: Optional[str] = None, search: Optional[str] = None) -> int:
        q = self.db.query(Student)
        if standard:
            q = q.filter(Student.standard == standard)
        if search:
            q = q.filter(Student.name.ilike(f"%{search}%"))
        return q.count()

    def list(self, *, standard: Optional[str] = None, search: Optional[str] = None,
             page: int = 1, size: int = 20):
        q = self.db.query(Student)
        if standard:
            q = q.filter(Student.standard == standard)
        if search:
            like = f"%{search}%"
            q = q.filter(Student.name.ilike(like))
        total_rows = q.count()
        rows = (q.order_by(Student.id.desc())
                .offset((page - 1) * size).limit(size).all())
        return rows, total_rows

    def update(self, obj: Student, **fields) -> Student:
        for k, v in fields.items():
            if v is not None and hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Student) -> None:
        self.db.delete(obj)
        self.db.commit()
