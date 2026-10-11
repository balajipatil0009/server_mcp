import re
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, field_validator

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Standard paginated response envelope."""
    items: List[T]
    total_rows: int
    total_pages: int
    page: int
    size: int
    has_next: bool
    has_previous: bool

    @staticmethod
    def build(items: List[T], total_rows: int, page: int, size: int) -> "Page[T]":
        total_pages = max(1, (total_rows + size - 1) // size) if size > 0 else 0
        return Page(items=items, total_rows=total_rows, total_pages=total_pages,
                    page=page, size=size,
                    has_next=(page * size) < total_rows,
                    has_previous=page > 1)



def normalize_phone(v: str) -> str:
    """Normalize Indian mobile: optional +91/91 prefix -> 10 digits starting 6-9."""
    v = v.strip().replace(" ", "").replace("-", "")
    if v.startswith("+91") and len(v) == 13:
        v = v[3:]
    elif v.startswith("91") and len(v) == 12:
        v = v[2:]
    if not re.fullmatch(r"[6-9]\d{9}", v):
        raise ValueError(
            "phone must be a valid 10-digit Indian mobile number "
            "(optional +91 prefix allowed)"
        )
    return v


class StudentBase(BaseModel):
    name: str
    phone: str
    standard: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("standard")
    @classmethod
    def validate_standard(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("standard is required (e.g. '8-A')")
        return v


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    standard: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_phone(v)

    @field_validator("standard")
    @classmethod
    def validate_standard(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("standard cannot be empty")
        return v


class StudentResponse(StudentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
