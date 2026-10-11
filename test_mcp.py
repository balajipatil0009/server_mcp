"""E2E validation of the MCP tools against a dedicated MySQL test database.

Runs the mounted FastMCP server the same way a remote client would: a
Streamable HTTP client pointed at the in-process ASGI app, so routing,
lifespan and the MCP session manager are all exercised for real.
"""
import asyncio
import os

os.environ["DB_NAME"] = "school_db_test"

import httpx2
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from tests_db import prepare_test_db

prepare_test_db()

from app.main import app  # noqa: E402  (reads DB_NAME at import time)


def http_client_factory(**kwargs):
    return httpx2.AsyncClient(transport=StreamingASGITransport(app), **kwargs)


transport = StreamableHttpTransport(
    url="http://testserver/mcp",
    httpx_client_factory=http_client_factory,
)

EXPECTED_TOOLS = {
    "list_students", "get_student", "list_standards", "create_student",
    "update_student", "delete_student",
    "add_mark", "add_marks_bulk", "list_marks", "update_mark", "delete_mark",
    "mark_attendance", "bulk_attendance", "list_attendance", "update_attendance",
    "delete_attendance",
    "add_behaviour", "list_behaviour", "update_behaviour", "delete_behaviour",
    "add_activity", "list_activities", "update_activity", "delete_activity",
    "get_student_analytics", "get_class_summary", "get_class_leaderboard",
}


async def main():
    async with run_asgi_lifespan(app):
        async with Client(transport) as client:
            # 1. Tool discovery
            tools = await client.list_tools()
            names = {t.name for t in tools}
            print(f"1. {len(names)} tools exposed")
            assert names == EXPECTED_TOOLS, names ^ EXPECTED_TOOLS

            read_only = {t.name for t in tools if t.annotations and t.annotations.read_only_hint}
            assert "get_student_analytics" in read_only and "delete_student" not in read_only
            print("   read-only/destructive hints OK")

            # 2. Create student
            res = await client.call_tool("create_student", {"payload": {
                "name": "Aarav Sharma", "phone": "+91 9876543210", "standard": "8-A"}})
            student = res.data
            assert not res.is_error, res.content
            assert student["standard"] == "8-A" and student["phone"] == "9876543210"
            sid = student["id"]
            print("2. create_student OK:", student["name"], sid)

            # 3. Duplicate phone is reported, not a generic crash
            res = await client.call_tool_mcp("create_student", {"payload": {
                "name": "Dup", "phone": "9876543210", "standard": "8-A"}})
            assert res.is_error and "already registered" in str(res.content), res.content
            print("3. duplicate phone reported OK")

            # 4. list_standards + list_students filters
            res = await client.call_tool("list_standards", {})
            assert res.data == ["8-A"], res.data
            page = (await client.call_tool("list_students", {"standard": "8-A"})).data
            assert page["total_rows"] == 1 and page["items"][0]["id"] == sid, page
            print("4. list_standards / list_students OK")

            # 5. Marks + bulk
            res = await client.call_tool("add_mark", {"payload": {
                "student_id": sid, "subject": "Maths", "marks_obtained": 85,
                "total_marks": 100, "term": "Term1"}})
            assert not res.is_error, res.content
            res = await client.call_tool("add_marks_bulk", {"payload": {"records": [
                {"student_id": sid, "subject": "Science", "marks_obtained": 70,
                 "total_marks": 100, "term": "Term1"},
                {"student_id": sid, "subject": "English", "marks_obtained": 90,
                 "total_marks": 100, "term": "Term1"}]}})
            assert not res.is_error, res.content
            print("5. add_mark / add_marks_bulk OK")

            # 6. Attendance, behaviour, activities
            from datetime import date, timedelta
            res = await client.call_tool("bulk_attendance", {"payload": {"records": [
                {"student_id": sid, "date": (date.today() - timedelta(days=i)).isoformat(),
                 "status": "absent" if i == 0 else "present"} for i in range(10)]}})
            assert not res.is_error, res.content
            res = await client.call_tool("add_behaviour", {"payload": {
                "student_id": sid, "score": 8, "remark": "Good"}})
            assert not res.is_error, res.content
            res = await client.call_tool("add_activity", {"payload": {
                "student_id": sid, "activity_name": "Cricket",
                "category": "sports", "points": 50}})
            assert not res.is_error, res.content
            print("6. bulk_attendance / add_behaviour / add_activity OK")

            # 7. Analytics reads (same numbers the REST validation asserts)
            a = (await client.call_tool("get_student_analytics", {"student_id": sid})).data
            print("7. analytics:", a["academics"]["average_pct"],
                  a["attendance"]["presenty_pct"], a["overall_performance_score"],
                  a["flags"])
            assert abs(a["academics"]["average_pct"] - 81.67) < 0.01
            assert a["attendance"]["presenty_pct"] == 90.0
            assert a["overall_performance_score"] > 0

            # 8. Class summary + leaderboard
            summary = (await client.call_tool("get_class_summary", {"standard": "8-A"})).data
            assert summary["students"] == 1 and summary["topper"]["student_id"] == sid, summary
            board = (await client.call_tool(
                "get_class_leaderboard", {"standard": "8-A"})).data
            assert board[0]["student_id"] == sid and board[0]["rank"] == 1
            print("8. class summary / leaderboard OK")

            # 9. Update + delete a student, confirming the cascade
            upd = (await client.call_tool("update_student", {
                "student_id": sid, "payload": {"standard": "8-B"}})).data
            assert upd["standard"] == "8-B", upd
            res = await client.call_tool("delete_student", {"student_id": sid})
            assert not res.is_error, res.content
            res = await client.call_tool_mcp("get_student", {"student_id": sid})
            assert res.is_error and "not found" in str(res.content), res.content
            print("9. update / delete / cascade OK")

    print("\nALL MCP TESTS PASSED")


asyncio.run(main())
