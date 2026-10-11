"""DB layer only - no validation, no HTTP. Raw parameterized PyMySQL.

Takes an open connection and never commits: the `get_conn()` boundary owns
commit / rollback. All rows are plain dicts (DictCursor).
"""
from typing import List, Optional

# Columns the dynamic UPDATE may touch. The SET clause is built only from
# this whitelist — never from raw user input.
_WRITABLE = ("name", "phone", "standard")


class StudentRepository:
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

    def create(self, *, name: str, phone: str, standard: str) -> dict:
        new_id = self._execute(
            "INSERT INTO students (name, phone, standard) VALUES (%s, %s, %s)",
            (name, phone, standard),
        )
        return self.get_by_id(new_id)

    def get_by_id(self, student_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM students WHERE id = %s", (student_id,))

    def get_by_phone(self, phone: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM students WHERE phone = %s", (phone,))

    def list_standards(self) -> List[str]:
        rows = self._fetchall("SELECT DISTINCT standard FROM students ORDER BY standard")
        return [r["standard"] for r in rows]

    def _where(self, standard: Optional[str], search: Optional[str]):
        clauses, params = [], []
        if standard:
            clauses.append("standard = %s")
            params.append(standard)
        if search:
            clauses.append("name LIKE %s")
            params.append(f"%{search}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, tuple(params)

    def list(self, *, standard: Optional[str] = None, search: Optional[str] = None,
             page: int = 1, size: int = 20):
        where, params = self._where(standard, search)
        total = self._fetchone(f"SELECT COUNT(*) AS n FROM students {where}", params)["n"]
        rows = self._fetchall(
            f"SELECT * FROM students {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            (*params, size, (page - 1) * size),
        )
        return rows, total

    def update(self, student_id: int, **fields) -> dict:
        assignments, params = [], []
        for key in _WRITABLE:
            value = fields.get(key)
            if value is not None:
                assignments.append(f"{key} = %s")
                params.append(value)
        if assignments:
            # updated_at has no ON UPDATE clause in MySQL: set it explicitly.
            assignments.append("updated_at = NOW()")
            params.append(student_id)
            self._execute(
                f"UPDATE students SET {', '.join(assignments)} WHERE id = %s",
                tuple(params),
            )
        return self.get_by_id(student_id)

    def delete(self, student_id: int) -> None:
        # Analytics rows go away via the FK ON DELETE CASCADE clauses.
        self._execute("DELETE FROM students WHERE id = %s", (student_id,))
