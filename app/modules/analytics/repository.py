"""DB layer for all analytics tables + read queries for aggregation.

Raw parameterized PyMySQL. Takes an open connection and never commits:
the `get_conn()` boundary owns commit / rollback. Rows are plain dicts.
"""
from datetime import date
from typing import List, Optional

from app.modules.analytics.schemas import ActivityCategory, AttendanceStatus


def _enum_value(value) -> Optional[str]:
    """Accept an Enum member or its raw string; store the plain string."""
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


_MARK_WRITABLE = ("subject", "marks_obtained", "total_marks", "exam_type", "term", "exam_date")
_ATTENDANCE_WRITABLE = ("date", "status")
_BEHAVIOUR_WRITABLE = ("score", "remark", "observed_by", "date")
_ACTIVITY_WRITABLE = ("activity_name", "category", "points", "achievement", "date")


class AnalyticsRepository:
    def __init__(self, conn):
        self.conn = conn

    def _fetchone(self, sql: str, params=()):
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def _fetchall(self, sql: str, params=()):
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _execute(self, sql: str, params=()):
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid

    def _update(self, table: str, record_id: int, fields: dict, writable) -> Optional[dict]:
        assignments, params = [], []
        for key in writable:
            if key in fields and fields[key] is not None:
                value = fields[key]
                if key in ("status", "category"):
                    value = _enum_value(value)
                assignments.append(f"{key} = %s")
                params.append(value)
        if assignments:
            params.append(record_id)
            self._execute(
                f"UPDATE {table} SET {', '.join(assignments)} WHERE id = %s",
                tuple(params),
            )
        return self._fetchone(f"SELECT * FROM {table} WHERE id = %s", (record_id,))

    # ---- marks ----
    def add_mark(self, **fields) -> dict:
        new_id = self._execute(
            """INSERT INTO marks
               (student_id, subject, marks_obtained, total_marks, exam_type, term, exam_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                fields["student_id"], fields["subject"], fields["marks_obtained"],
                fields.get("total_marks", 100), fields.get("exam_type", "unit-test"),
                fields.get("term", "Term1"), fields.get("exam_date"),
            ),
        )
        return self.get_mark(new_id)

    def add_marks_bulk(self, rows: List[dict]) -> List[dict]:
        return [self.add_mark(**r) for r in rows]

    def get_mark(self, mark_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM marks WHERE id = %s", (mark_id,))

    def list_marks(self, student_id: int, term: Optional[str] = None) -> List[dict]:
        if term:
            return self._fetchall(
                "SELECT * FROM marks WHERE student_id = %s AND term = %s"
                " ORDER BY exam_date DESC, id DESC",
                (student_id, term),
            )
        return self._fetchall(
            "SELECT * FROM marks WHERE student_id = %s ORDER BY exam_date DESC, id DESC",
            (student_id,),
        )

    def list_marks_paged(self, student_id: int, term: Optional[str] = None,
                         page: int = 1, size: int = 50):
        if term:
            where, params = "WHERE student_id = %s AND term = %s", (student_id, term)
        else:
            where, params = "WHERE student_id = %s", (student_id,)
        total_rows = self._fetchone(f"SELECT COUNT(*) AS n FROM marks {where}", params)["n"]
        rows = self._fetchall(
            f"SELECT * FROM marks {where} ORDER BY exam_date DESC, id DESC"
            " LIMIT %s OFFSET %s",
            (*params, size, (page - 1) * size),
        )
        return rows, total_rows

    def update_mark(self, mark_id: int, **fields) -> Optional[dict]:
        return self._update("marks", mark_id, fields, _MARK_WRITABLE)

    def delete_mark(self, mark_id: int) -> None:
        self._execute("DELETE FROM marks WHERE id = %s", (mark_id,))

    # ---- attendance ----
    def mark_attendance(self, *, student_id: int, date: date, status=AttendanceStatus.present) -> dict:
        status = _enum_value(status) or AttendanceStatus.present.value
        existing = self._fetchone(
            "SELECT * FROM attendance WHERE student_id = %s AND `date` = %s",
            (student_id, date),
        )
        if existing:
            self._execute(
                "UPDATE attendance SET status = %s WHERE id = %s",
                (status, existing["id"]),
            )
            return self.get_attendance(existing["id"])
        new_id = self._execute(
            "INSERT INTO attendance (student_id, `date`, status) VALUES (%s, %s, %s)",
            (student_id, date, status),
        )
        return self.get_attendance(new_id)

    def add_attendance_bulk(self, rows: List[dict]) -> List[dict]:
        out = []
        for r in rows:
            out.append(
                self.mark_attendance(
                    student_id=r["student_id"], date=r["date"],
                    status=r.get("status", AttendanceStatus.present),
                )
            )
        return out

    def get_attendance(self, record_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM attendance WHERE id = %s", (record_id,))

    def list_attendance(self, student_id: int) -> List[dict]:
        return self._fetchall(
            "SELECT * FROM attendance WHERE student_id = %s ORDER BY `date` DESC",
            (student_id,),
        )

    def list_attendance_paged(self, student_id: int, page: int = 1, size: int = 50):
        total_rows = self._fetchone(
            "SELECT COUNT(*) AS n FROM attendance WHERE student_id = %s", (student_id,)
        )["n"]
        rows = self._fetchall(
            "SELECT * FROM attendance WHERE student_id = %s ORDER BY `date` DESC"
            " LIMIT %s OFFSET %s",
            (student_id, size, (page - 1) * size),
        )
        return rows, total_rows

    def update_attendance(self, record_id: int, **fields) -> Optional[dict]:
        return self._update("attendance", record_id, fields, _ATTENDANCE_WRITABLE)

    def delete_attendance(self, record_id: int) -> None:
        self._execute("DELETE FROM attendance WHERE id = %s", (record_id,))

    # ---- behaviour ----
    def add_behaviour(self, **fields) -> dict:
        new_id = self._execute(
            "INSERT INTO behaviour (student_id, score, remark, observed_by, `date`)"
            " VALUES (%s, %s, %s, %s, %s)",
            (
                fields["student_id"], fields["score"], fields.get("remark"),
                fields.get("observed_by"), fields.get("date"),
            ),
        )
        return self.get_behaviour(new_id)

    def get_behaviour(self, record_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM behaviour WHERE id = %s", (record_id,))

    def list_behaviour(self, student_id: int) -> List[dict]:
        return self._fetchall(
            "SELECT * FROM behaviour WHERE student_id = %s ORDER BY `date` DESC, id DESC",
            (student_id,),
        )

    def list_behaviour_paged(self, student_id: int, page: int = 1, size: int = 50):
        total_rows = self._fetchone(
            "SELECT COUNT(*) AS n FROM behaviour WHERE student_id = %s", (student_id,)
        )["n"]
        rows = self._fetchall(
            "SELECT * FROM behaviour WHERE student_id = %s ORDER BY `date` DESC, id DESC"
            " LIMIT %s OFFSET %s",
            (student_id, size, (page - 1) * size),
        )
        return rows, total_rows

    def update_behaviour(self, record_id: int, **fields) -> Optional[dict]:
        return self._update("behaviour", record_id, fields, _BEHAVIOUR_WRITABLE)

    def delete_behaviour(self, record_id: int) -> None:
        self._execute("DELETE FROM behaviour WHERE id = %s", (record_id,))

    # ---- activities ----
    def add_activity(self, **fields) -> dict:
        new_id = self._execute(
            """INSERT INTO curriculum_activities
               (student_id, activity_name, category, points, achievement, `date`)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                fields["student_id"], fields["activity_name"],
                _enum_value(fields.get("category", ActivityCategory.other))
                or ActivityCategory.other.value,
                fields.get("points", 0), fields.get("achievement"), fields.get("date"),
            ),
        )
        return self.get_activity(new_id)

    def get_activity(self, record_id: int) -> Optional[dict]:
        return self._fetchone(
            "SELECT * FROM curriculum_activities WHERE id = %s", (record_id,)
        )

    def list_activities(self, student_id: int) -> List[dict]:
        return self._fetchall(
            "SELECT * FROM curriculum_activities WHERE student_id = %s"
            " ORDER BY `date` DESC, id DESC",
            (student_id,),
        )

    def list_activities_paged(self, student_id: int, page: int = 1, size: int = 50):
        total_rows = self._fetchone(
            "SELECT COUNT(*) AS n FROM curriculum_activities WHERE student_id = %s",
            (student_id,),
        )["n"]
        rows = self._fetchall(
            "SELECT * FROM curriculum_activities WHERE student_id = %s"
            " ORDER BY `date` DESC, id DESC LIMIT %s OFFSET %s",
            (student_id, size, (page - 1) * size),
        )
        return rows, total_rows

    def update_activity(self, record_id: int, **fields) -> Optional[dict]:
        return self._update("curriculum_activities", record_id, fields, _ACTIVITY_WRITABLE)

    def delete_activity(self, record_id: int) -> None:
        self._execute("DELETE FROM curriculum_activities WHERE id = %s", (record_id,))
