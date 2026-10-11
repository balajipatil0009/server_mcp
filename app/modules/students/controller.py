from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.students import schemas
from app.modules.students.service import (
    DuplicatePhoneError,
    StudentNotFoundError,
    StudentService,
)

router = APIRouter(prefix="/students", tags=["Students"])


def get_service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db)


@router.post("", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(payload: schemas.StudentCreate, service: StudentService = Depends(get_service)):
    try:
        return service.create_student(payload)
    except DuplicatePhoneError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=schemas.Page[schemas.StudentResponse])
def list_students(
    standard: Optional[str] = Query(default=None, description="Filter e.g. 8-A"),
    search: Optional[str] = Query(default=None, description="Search by name"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    service: StudentService = Depends(get_service),
):
    return service.list_students(standard=standard, search=search, page=page, size=size)


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, service: StudentService = Depends(get_service)):
    try:
        return service.get_student(student_id)
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    student_id: int, payload: schemas.StudentUpdate,
    service: StudentService = Depends(get_service),
):
    try:
        return service.update_student(student_id, payload)
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicatePhoneError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, service: StudentService = Depends(get_service)):
    try:
        service.delete_student(student_id)
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
