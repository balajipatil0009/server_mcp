from typing import Optional

from sqlalchemy.exc import IntegrityError
from app.modules.students.schemas import Page

from sqlalchemy.orm import Session

from app.modules.students import schemas
from app.modules.students.model import Student
from app.modules.students.repository import StudentRepository


class DuplicatePhoneError(ValueError):
    pass


class StudentNotFoundError(ValueError):
    pass


class StudentService:
    """Business-logic layer: validation + rules. No HTTP, no raw SQL."""

    def __init__(self, db: Session):
        self.repo = StudentRepository(db)

    def create_student(self, payload: schemas.StudentCreate) -> Student:
        if self.repo.get_by_phone(payload.phone):
            raise DuplicatePhoneError(f"phone {payload.phone} already registered")
        try:
            return self.repo.create(
                name=payload.name, phone=payload.phone, standard=payload.standard
            )
        except IntegrityError:
            raise DuplicatePhoneError(f"phone {payload.phone} already registered")

    def get_student(self, student_id: int) -> Student:
        obj = self.repo.get_by_id(student_id)
        if not obj:
            raise StudentNotFoundError(f"student {student_id} not found")
        return obj

    def list_students(self, *, standard: Optional[str] = None,
                      search: Optional[str] = None, page: int = 1, size: int = 20):
        rows, total_rows = self.repo.list(
            standard=standard, search=search, page=page, size=size
        )
        return schemas.Page[schemas.StudentResponse].build(rows, total_rows, page, size)

    def update_student(self, student_id: int, payload: schemas.StudentUpdate) -> Student:
        obj = self.get_student(student_id)
        data = payload.model_dump(exclude_unset=True)
        if "phone" in data and data["phone"] != obj.phone:
            if self.repo.get_by_phone(data["phone"]):
                raise DuplicatePhoneError(f"phone {data['phone']} already registered")
        try:
            return self.repo.update(obj, **data)
        except IntegrityError:
            raise DuplicatePhoneError("phone already registered")

    def delete_student(self, student_id: int) -> None:
        obj = self.get_student(student_id)
        self.repo.delete(obj)
