"""Shared helper for the MySQL-backed test scripts.

Points the app at a dedicated `school_db_test` database (never the real
`school_db`), creates it if needed, builds the tables via `init_db()` and
wipes all rows so each script starts from a clean slate.

Must be imported AFTER `os.environ["DB_NAME"]` is set and BEFORE `app.main`.
"""
import pymysql

from app.core.config import settings
from app.core.database import conn_scope
from app.core.schema import init_db

TABLES_IN_WIPE_ORDER = (
    "marks", "attendance", "behaviour", "curriculum_activities", "students",
)


def prepare_test_db() -> None:
    # CREATE DATABASE needs a connection without a database selected.
    admin = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with admin.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}`"
                " CHARACTER SET utf8mb4"
            )
        admin.commit()
    finally:
        admin.close()
    init_db()
    with conn_scope() as conn:
        with conn.cursor() as cur:
            for table in TABLES_IN_WIPE_ORDER:
                cur.execute(f"DELETE FROM {table}")
