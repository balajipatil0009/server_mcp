"""Raw MySQL access via PyMySQL — no ORM.

Single seam: `get_connection()` builds a `DictCursor` connection
(rows come back as plain dicts).

Two lifecycle helpers share one rule — commit on success, rollback on
error, close always:
- `get_conn()` is a plain generator for FastAPI `Depends(get_conn)`.
  (It must stay a bare generator function: FastAPI detects `yield`
  dependencies via introspection, which a `@contextmanager` wrapper hides.)
- `conn_scope()` is the `with`-block twin for MCP tools, seed.py and tests.
"""
from contextlib import contextmanager
from typing import Iterator

import pymysql
import pymysql.cursors

from app.core.config import settings


def get_connection():
    """Open a new raw PyMySQL connection using the current settings."""
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )


def get_conn():
    """FastAPI dependency: yield one transactional connection per request."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def conn_scope() -> Iterator[pymysql.connections.Connection]:
    """`with` block version of `get_conn()` for non-request code
    (MCP tools, seed.py, tests). Same commit / rollback / close rule."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
