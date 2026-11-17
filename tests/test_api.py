import asyncio
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.cache import cache
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.rate_limit import rate_limiter
from app.main import app


class TaskFlowAPITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp_path = Path(cls._tmp_dir.name)
        cls._db_path = tmp_path / "test_taskflow.db"
        cls._upload_dir = tmp_path / "uploads"
        cls._export_dir = tmp_path / "exports"

        settings = get_settings()
        cls._orig_db_url = settings.database_url
        cls._orig_sqlite_url = settings.sqlite_fallback_url
        cls._orig_upload_dir = settings.upload_dir
        cls._orig_export_dir = settings.export_dir

        settings.database_url = "postgresql+asyncpg://invalid:invalid@127.0.0.1:1/none"
        settings.sqlite_fallback_url = f"sqlite+aiosqlite:///{cls._db_path}"
        settings.upload_dir = str(cls._upload_dir)
        settings.export_dir = str(cls._export_dir)

        asyncio.run(cache.clear())
        cls._client_cm = TestClient(app)
        cls.client = cls._client_cm.__enter__()

        # Register and log in user 1
        cls.user1 = {
            "username": "alice_test",
            "email": "alice@example.com",
            "password": "password123",
        }
        r = cls.client.post("/auth/register", json=cls.user1)
        assert r.status_code == 201, r.text
        cls.user1_id = r.json()["id"]

        r = cls.client.post(
            "/auth/login",
            data={"username": "alice_test", "password": "password123"},
        )
        assert r.status_code == 200, r.text
        cls.token1 = r.json()["access_token"]
        cls.refresh_token1 = r.json()["refresh_token"]
        cls.headers1 = {"Authorization": f"Bearer {cls.token1}"}

        # Register and log in user 2 (for ownership/isolation tests)
        cls.user2 = {
            "username": "bob_test",
            "email": "bob@example.com",
            "password": "password123",
        }
        r = cls.client.post("/auth/register", json=cls.user2)
        assert r.status_code == 201, r.text

        r = cls.client.post(
            "/auth/login",
            data={"username": "bob_test", "password": "password123"},
        )
        assert r.status_code == 200, r.text
        cls.token2 = r.json()["access_token"]
        cls.headers2 = {"Authorization": f"Bearer {cls.token2}"}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_cm.__exit__(None, None, None)
        settings = get_settings()
        settings.database_url = cls._orig_db_url
        settings.sqlite_fallback_url = cls._orig_sqlite_url
        settings.upload_dir = cls._orig_upload_dir
        settings.export_dir = cls._orig_export_dir
        cls._tmp_dir.cleanup()

    def test_01_health_and_resource(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("cache", data)
        self.assertIn("websocket_connections", data)

        r = self.client.get("/resource")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"name": "TaskFlow"})

    def test_02_auth_routes(self) -> None:
        r = self.client.get("/auth/me", headers=self.headers1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["username"], "alice_test")

        # Non-admin should get 403 on /auth/admin-only
        r = self.client.get("/auth/admin-only", headers=self.headers1)
        self.assertEqual(r.status_code, 403)

        # Duplicate registration should return 409
        r = self.client.post("/auth/register", json=self.user1)
        self.assertEqual(r.status_code, 409)

        # Bad login should return 401
        r = self.client.post(
            "/auth/login",
            data={"username": "alice_test", "password": "wrongpassword"},
        )
        self.assertEqual(r.status_code, 401)

        # Refresh token should issue a new access & refresh token pair
        self.assertIsNotNone(self.refresh_token1)
        r_ref = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.refresh_token1},
        )
        self.assertEqual(r_ref.status_code, 200, r_ref.text)
        self.assertIn("access_token", r_ref.json())
        self.assertIn("refresh_token", r_ref.json())

        # Access token cannot be used as a refresh token
        r_bad_ref = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.token1},
        )
        self.assertEqual(r_bad_ref.status_code, 401)

    def test_02b_rate_limiter(self) -> None:
        async def _check_limit():
            await rate_limiter.reset()
            await rate_limiter.check("test:ip", max_requests=2, window_seconds=60)
            await rate_limiter.check("test:ip", max_requests=2, window_seconds=60)
            with self.assertRaises(AppError) as ctx:
                await rate_limiter.check("test:ip", max_requests=2, window_seconds=60)
            self.assertEqual(ctx.exception.status_code, 429)
            self.assertEqual(ctx.exception.code, "RATE_LIMIT_EXCEEDED")
            await rate_limiter.reset()

        asyncio.run(_check_limit())

    def test_03_tasks_pagination_caching_and_ownership(self) -> None:
        # Create 5 tasks for user 1
        past_due = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        future_due = (datetime.now(UTC) + timedelta(days=2)).isoformat()
        created_ids = []
        for i in range(1, 6):
            payload = {
                "title": f"Task {i}",
                "description": f"Description for task {i}",
                "status": "todo" if i % 2 == 1 else "in_progress",
                "due_at": past_due if i == 1 else future_due,
            }
            r = self.client.post("/tasks", json=payload, headers=self.headers1)
            self.assertEqual(r.status_code, 201, r.text)
            created_ids.append(r.json()["id"])

        # Page 1, page_size 2 -> cache MISS then HIT
        r1 = self.client.get(
            "/tasks?page=1&page_size=2&sort_by=title&sort_order=asc",
            headers=self.headers1,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.headers.get("X-Cache"), "MISS")
        body1 = r1.json()
        self.assertEqual(body1["total"], 5)
        self.assertEqual(body1["page"], 1)
        self.assertEqual(body1["page_size"], 2)
        self.assertEqual(body1["total_pages"], 3)
        self.assertTrue(body1["has_next"])
        self.assertFalse(body1["has_prev"])
        self.assertEqual([t["title"] for t in body1["items"]], ["Task 1", "Task 2"])

        r1_cached = self.client.get(
            "/tasks?page=1&page_size=2&sort_by=title&sort_order=asc",
            headers=self.headers1,
        )
        self.assertEqual(r1_cached.status_code, 200)
        self.assertEqual(r1_cached.headers.get("X-Cache"), "HIT")

        # Page 3 -> 1 item, has_next False, has_prev True
        r3 = self.client.get(
            "/tasks?page=3&page_size=2&sort_by=title&sort_order=asc",
            headers=self.headers1,
        )
        self.assertEqual(r3.status_code, 200)
        body3 = r3.json()
        self.assertEqual(len(body3["items"]), 1)
        self.assertFalse(body3["has_next"])
        self.assertTrue(body3["has_prev"])

        # Filter by status and search query
        r_filter = self.client.get(
            "/tasks?status=in_progress&q=Task", headers=self.headers1
        )
        self.assertEqual(r_filter.status_code, 200)
        self.assertEqual(r_filter.json()["total"], 2)

        # Detail endpoint cache MISS then HIT
        tid = created_ids[0]
        rd1 = self.client.get(f"/tasks/{tid}", headers=self.headers1)
        self.assertEqual(rd1.status_code, 200)
        self.assertEqual(rd1.headers.get("X-Cache"), "MISS")

        rd2 = self.client.get(f"/tasks/{tid}", headers=self.headers1)
        self.assertEqual(rd2.status_code, 200)
        self.assertEqual(rd2.headers.get("X-Cache"), "HIT")

        # Update invalidates cache
        ru = self.client.patch(
            f"/tasks/{tid}",
            json={"title": "Task 1 Updated"},
            headers=self.headers1,
        )
        self.assertEqual(ru.status_code, 200)
        self.assertEqual(ru.json()["title"], "Task 1 Updated")

        rd3 = self.client.get(f"/tasks/{tid}", headers=self.headers1)
        self.assertEqual(rd3.status_code, 200)
        self.assertEqual(rd3.headers.get("X-Cache"), "MISS")
        self.assertEqual(rd3.json()["title"], "Task 1 Updated")

        # Ownership enforcement: user 2 cannot get, patch, or delete user 1's task
        self.assertEqual(
            self.client.get(f"/tasks/{tid}", headers=self.headers2).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                f"/tasks/{tid}", json={"title": "Hack"}, headers=self.headers2
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/tasks/{tid}", headers=self.headers2).status_code,
            404,
        )

        # Not found task returns clean AppError JSON
        r_nf = self.client.get("/tasks/999999", headers=self.headers1)
        self.assertEqual(r_nf.status_code, 404)
        self.assertEqual(r_nf.json()["error"]["code"], "TASK_NOT_FOUND")

        # Delete last created task
        r_del = self.client.delete(
            f"/tasks/{created_ids[-1]}", headers=self.headers1
        )
        self.assertEqual(r_del.status_code, 204)

    def test_04_file_uploads_and_attachments(self) -> None:
        r = self.client.post(
            "/tasks", json={"title": "Task with attachment"}, headers=self.headers1
        )
        self.assertEqual(r.status_code, 201)
        task_id = r.json()["id"]

        # Disallowed extension
        r_bad = self.client.post(
            f"/tasks/{task_id}/attachments",
            files={"file": ("malware.exe", b"mz", "application/octet-stream")},
            headers=self.headers1,
        )
        self.assertEqual(r_bad.status_code, 400)
        self.assertEqual(r_bad.json()["error"]["code"], "UNSUPPORTED_FILE_TYPE")

        # Empty file
        r_empty = self.client.post(
            f"/tasks/{task_id}/attachments",
            files={"file": ("empty.txt", b"", "text/plain")},
            headers=self.headers1,
        )
        self.assertEqual(r_empty.status_code, 400)
        self.assertEqual(r_empty.json()["error"]["code"], "EMPTY_FILE")

        # Valid upload
        file_bytes = b"Hello TaskFlow attachment!"
        r_up = self.client.post(
            f"/tasks/{task_id}/attachments",
            files={"file": ("notes.txt", file_bytes, "text/plain")},
            headers=self.headers1,
        )
        self.assertEqual(r_up.status_code, 201, r_up.text)
        att = r_up.json()
        att_id = att["id"]
        self.assertEqual(att["filename"], "notes.txt")
        self.assertEqual(att["size_bytes"], len(file_bytes))

        # List attachments
        r_list = self.client.get(
            f"/tasks/{task_id}/attachments", headers=self.headers1
        )
        self.assertEqual(r_list.status_code, 200)
        self.assertEqual(len(r_list.json()), 1)

        # Download attachment
        r_dl = self.client.get(
            f"/attachments/{att_id}/download", headers=self.headers1
        )
        self.assertEqual(r_dl.status_code, 200)
        self.assertEqual(r_dl.content, file_bytes)

        # Other user cannot download or delete
        self.assertEqual(
            self.client.get(
                f"/attachments/{att_id}/download", headers=self.headers2
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(
                f"/attachments/{att_id}", headers=self.headers2
            ).status_code,
            404,
        )

        # Delete attachment
        r_del = self.client.delete(
            f"/attachments/{att_id}", headers=self.headers1
        )
        self.assertEqual(r_del.status_code, 204)

    def test_05_background_jobs(self) -> None:
        # Export tasks as JSON
        r_exp = self.client.post(
            "/jobs/export-tasks",
            json={"format": "json"},
            headers=self.headers1,
        )
        self.assertEqual(r_exp.status_code, 202, r_exp.text)
        job_id = r_exp.json()["id"]

        # TestClient runs BackgroundTasks before returning, so job should be completed
        r_job = self.client.get(f"/jobs/{job_id}", headers=self.headers1)
        self.assertEqual(r_job.status_code, 200)
        job_data = r_job.json()
        self.assertEqual(job_data["status"], "completed")
        self.assertGreaterEqual(job_data["result"]["task_count"], 1)

        # Download export
        r_dl = self.client.get(
            f"/jobs/{job_id}/download", headers=self.headers1
        )
        self.assertEqual(r_dl.status_code, 200)
        exported = json.loads(r_dl.text)
        self.assertIsInstance(exported, list)
        self.assertGreaterEqual(len(exported), 1)

        # Export tasks as CSV
        r_csv = self.client.post(
            "/jobs/export-tasks",
            json={"format": "csv"},
            headers=self.headers1,
        )
        self.assertEqual(r_csv.status_code, 202)
        csv_job_id = r_csv.json()["id"]
        r_csv_dl = self.client.get(
            f"/jobs/{csv_job_id}/download", headers=self.headers1
        )
        self.assertEqual(r_csv_dl.status_code, 200)
        self.assertIn("id,title,description,status", r_csv_dl.text)

        # Overdue digest job
        r_dig = self.client.post("/jobs/overdue-digest", headers=self.headers1)
        self.assertEqual(r_dig.status_code, 202)
        dig_id = r_dig.json()["id"]
        r_dig_get = self.client.get(f"/jobs/{dig_id}", headers=self.headers1)
        self.assertEqual(r_dig_get.status_code, 200)
        self.assertEqual(r_dig_get.json()["status"], "completed")
        self.assertGreaterEqual(r_dig_get.json()["result"]["overdue_count"], 1)

        # List jobs paginated
        r_jobs = self.client.get("/jobs?page=1&page_size=2", headers=self.headers1)
        self.assertEqual(r_jobs.status_code, 200)
        self.assertEqual(r_jobs.json()["total"], 3)
        self.assertEqual(len(r_jobs.json()["items"]), 2)

        # User 2 cannot access user 1's job
        self.assertEqual(
            self.client.get(f"/jobs/{job_id}", headers=self.headers2).status_code,
            404,
        )

    def test_06_websockets_realtime_events(self) -> None:
        # Unauthenticated WebSocket should fail
        with self.assertRaises(Exception):
            with self.client.websocket_connect("/ws/tasks"):
                pass

        # Authenticated WebSocket receives connected event, ping/pong, and task.created
        with self.client.websocket_connect(
            f"/ws/tasks?token={self.token1}"
        ) as ws:
            hello = ws.receive_json()
            self.assertEqual(hello["event"], "connected")
            self.assertEqual(hello["username"], "alice_test")

            ws.send_text("ping")
            pong = ws.receive_json()
            self.assertEqual(pong["event"], "pong")

            # Creating a task via HTTP triggers WebSocket broadcast to user 1
            r = self.client.post(
                "/tasks",
                json={"title": "Realtime WS Task"},
                headers=self.headers1,
            )
            self.assertEqual(r.status_code, 201)
            new_task_id = r.json()["id"]

            event_msg = ws.receive_json()
            self.assertEqual(event_msg["event"], "task.created")
            self.assertEqual(event_msg["data"]["task_id"], new_task_id)


if __name__ == "__main__":
    unittest.main()
