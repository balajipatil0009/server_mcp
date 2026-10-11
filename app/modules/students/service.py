from typing import List, Optional

import pymysql

from app.modules.students import schemas
from app.modules.students.repository import StudentRepository


class DuplicatePhoneError(ValueError):
    pass


class StudentNotFoundError(ValueError):
    pass


def _is_duplicate_phone_error(exc: Exception) -> bool:
    """MySQL 1062 = duplicate entry (the unique phone index)."""
    return isinstance(exc, pymysql.err.IntegrityError) and exc.args and exc.args[0] == 1062


class StudentService:
    """Business-logic layer: validation + rules. No HTTP, no SQL text."""

    def __init__(self, conn):
        self.repo = StudentRepository(conn)

    def create_student(self, payload: schemas.StudentCreate) -> dict:
        if self.repo.get_by_phone(payload.phone):
            raise DuplicatePhoneError(f"phone {payload.phone} already registered")
        try:
            return self.repo.create(
                name=payload.name, phone=payload.phone, standard=payload.standard
            )
        except Exception as e:  # noqa: BLE001
            if _is_duplicate_phone_error(e):
                raise DuplicatePhoneError(f"phone {payload.phone} already registered") from e
            raise

    def get_student(self, student_id: int) -> dict:
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

    def list_standards(self) -> List[str]:
        return self.repo.list_standards()

    def update_student(self, student_id: int, payload: schemas.StudentUpdate) -> dict:
        obj = self.get_student(student_id)
        data = payload.model_dump(exclude_unset=True)
        if "phone" in data and data["phone"] != obj["phone"]:
            if self.repo.get_by_phone(data["phone"]):
                raise DuplicatePhoneError(f"phone {data['phone']} already registered")
        try:
            return self.repo.update(student_id, **data)
        except Exception as e:  # noqa: BLE001
            if _is_duplicate_phone_error(e):
                raise DuplicatePhoneError("phone already registered") from e
            raise

    def delete_student(self, student_id: int) -> None:
        self.get_student(student_id)
        self.repo.delete(student_id)
