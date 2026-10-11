from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.analytics import schemas
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsService
from app.modules.students.schemas import Page
from app.modules.students.service import StudentNotFoundError

router = APIRouter(tags=["Analytics"])


def get_repo(db: Session = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(db)


def get_analytics(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


# ---------- Marks CRUD ----------
@router.post("/marks", response_model=schemas.MarkResponse, status_code=201)
def add_mark(payload: schemas.MarkCreate, repo: AnalyticsRepository = Depends(get_repo)):
    if payload.marks_obtained > payload.total_marks:
        raise HTTPException(status_code=422, detail="marks_obtained cannot exceed total_marks")
    return repo.add_mark(**payload.model_dump())


@router.post("/marks/bulk", status_code=201)
def add_marks_bulk(payload: schemas.MarkBulkCreate, repo: AnalyticsRepository = Depends(get_repo)):
    for r in payload.records:
        if r.marks_obtained > r.total_marks:
            raise HTTPException(status_code=422, detail=f"marks exceed total for {r.subject}")
    return repo.add_marks_bulk([r.model_dump() for r in payload.records])


@router.get("/marks", response_model=schemas.Page[schemas.MarkResponse])
def list_marks(student_id: int, term: Optional[str] = None,
               page: int = Query(default=1, ge=1), size: int = Query(default=50, ge=1, le=200),
               repo: AnalyticsRepository = Depends(get_repo)):
    rows, total_rows = repo.list_marks_paged(student_id, term, page, size)
    return schemas.Page[schemas.MarkResponse].build(rows, total_rows, page, size)


@router.put("/marks/{mark_id}", response_model=schemas.MarkResponse)
def update_mark(mark_id: int, payload: schemas.MarkUpdate,
                repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_mark(mark_id)
    if not obj:
        raise HTTPException(status_code=404, detail="mark not found")
    return repo.update_mark(obj, **payload.model_dump(exclude_unset=True))


# ---------- Attendance CRUD ----------
@router.post("/attendance", response_model=schemas.AttendanceResponse, status_code=201)
def mark_attendance(payload: schemas.AttendanceCreate,
                    repo: AnalyticsRepository = Depends(get_repo)):
    return repo.mark_attendance(**payload.model_dump())


@router.post("/attendance/bulk", status_code=201)
def bulk_attendance(payload: schemas.AttendanceBulkCreate,
                    repo: AnalyticsRepository = Depends(get_repo)):
    return repo.add_attendance_bulk([r.model_dump() for r in payload.records])


@router.get("/attendance", response_model=schemas.Page[schemas.AttendanceResponse])
def list_attendance(student_id: int,
                    page: int = Query(default=1, ge=1), size: int = Query(default=50, ge=1, le=200),
                    repo: AnalyticsRepository = Depends(get_repo)):
    rows, total_rows = repo.list_attendance_paged(student_id, page, size)
    return schemas.Page[schemas.AttendanceResponse].build(rows, total_rows, page, size)


@router.put("/attendance/{record_id}", response_model=schemas.AttendanceResponse)
def update_attendance(record_id: int, payload: schemas.AttendanceUpdate,
                      repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_attendance(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="attendance record not found")
    return repo.update_attendance(obj, **payload.model_dump(exclude_unset=True))


@router.delete("/attendance/{record_id}", status_code=204)
def delete_attendance(record_id: int, repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_attendance(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="attendance record not found")
    repo.delete_attendance(obj)
    return None


# ---------- Behaviour CRUD ----------
@router.post("/behaviour", response_model=schemas.BehaviourResponse, status_code=201)
def add_behaviour(payload: schemas.BehaviourCreate,
                  repo: AnalyticsRepository = Depends(get_repo)):
    return repo.add_behaviour(**payload.model_dump())


@router.get("/behaviour", response_model=schemas.Page[schemas.BehaviourResponse])
def list_behaviour(student_id: int,
                   page: int = Query(default=1, ge=1), size: int = Query(default=50, ge=1, le=200),
                   repo: AnalyticsRepository = Depends(get_repo)):
    rows, total_rows = repo.list_behaviour_paged(student_id, page, size)
    return schemas.Page[schemas.BehaviourResponse].build(rows, total_rows, page, size)


@router.put("/behaviour/{record_id}", response_model=schemas.BehaviourResponse)
def update_behaviour(record_id: int, payload: schemas.BehaviourUpdate,
                     repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_behaviour(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="behaviour record not found")
    return repo.update_behaviour(obj, **payload.model_dump(exclude_unset=True))


@router.delete("/behaviour/{record_id}", status_code=204)
def delete_behaviour(record_id: int, repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_behaviour(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="behaviour record not found")
    repo.delete_behaviour(obj)
    return None


# ---------- Curriculum activities CRUD ----------
@router.post("/activities", response_model=schemas.ActivityResponse, status_code=201)
def add_activity(payload: schemas.ActivityCreate,
                 repo: AnalyticsRepository = Depends(get_repo)):
    return repo.add_activity(**payload.model_dump())


@router.get("/activities", response_model=schemas.Page[schemas.ActivityResponse])
def list_activities(student_id: int,
                    page: int = Query(default=1, ge=1), size: int = Query(default=50, ge=1, le=200),
                    repo: AnalyticsRepository = Depends(get_repo)):
    rows, total_rows = repo.list_activities_paged(student_id, page, size)
    return schemas.Page[schemas.ActivityResponse].build(rows, total_rows, page, size)


@router.put("/activities/{record_id}", response_model=schemas.ActivityResponse)
def update_activity(record_id: int, payload: schemas.ActivityUpdate,
                    repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_activity(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="activity not found")
    return repo.update_activity(obj, **payload.model_dump(exclude_unset=True))


@router.delete("/activities/{record_id}", status_code=204)
def delete_activity(record_id: int, repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_activity(record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="activity not found")
    repo.delete_activity(obj)
    return None


# ---------- Aggregated analytics reads ----------
@router.get("/students/{student_id}/analytics",
            response_model=schemas.StudentAnalyticsResponse)
def student_analytics(student_id: int, term: Optional[str] = None,
                      svc: AnalyticsService = Depends(get_analytics)):
    try:
        return svc.get_student_analytics(student_id, term)
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analytics/class/{standard}/summary",
            response_model=schemas.ClassSummaryResponse)
def class_summary(standard: str, svc: AnalyticsService = Depends(get_analytics)):
    return svc.get_class_summary(standard)


@router.get("/analytics/class/{standard}/leaderboard")
def class_leaderboard(standard: str, limit: int = Query(default=10, ge=1, le=100),
                      svc: AnalyticsService = Depends(get_analytics)):
    return svc.get_leaderboard(standard, limit)


@router.delete("/marks/{mark_id}", status_code=204)
def delete_mark(mark_id: int, repo: AnalyticsRepository = Depends(get_repo)):
    obj = repo.get_mark(mark_id)
    if not obj:
        raise HTTPException(status_code=404, detail="mark not found")
    repo.delete_mark(obj)
    return None
