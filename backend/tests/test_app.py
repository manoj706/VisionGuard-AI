import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from storage.retention import purge_old_data


class VisionGuardAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client_cm = TestClient(app)
        self.client = self.client_cm.__enter__()

    def tearDown(self) -> None:
        self.client_cm.__exit__(None, None, None)

    def test_login_and_health(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "changeme"},
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]

        health = self.client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(health.status_code, 200)
        self.assertIn("privacy_mode", health.json())

    def test_search_and_export(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "changeme"},
        )
        token = response.json()["token"]

        time.sleep(0.5)
        search = self.client.post(
            "/api/search",
            json={"query": "person"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(search.status_code, 200)

        export = self.client.get(
            "/api/search/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(export.status_code, 200)
        self.assertIn("timestamp,camera_name,global_person_id", export.text)

    def test_retention_purge_removes_old_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            thumbs = Path(tmpdir) / "thumbnails"
            clips = Path(tmpdir) / "clips"
            thumbs.mkdir()
            clips.mkdir()
            old_file = thumbs / "old.jpg"
            old_file.write_text("x", encoding="utf-8")
            old_time = time.time() - (31 * 86400)
            Path(old_file).touch()
            import os

            os.utime(old_file, (old_time, old_time))

            self.assertTrue(old_file.exists())
            import asyncio

            asyncio.run(purge_old_data(tmpdir))
            self.assertFalse(old_file.exists())


if __name__ == "__main__":
    unittest.main()
