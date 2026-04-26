import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

API_KEY = "dev-api-key-change-me"
HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture
def mock_redis():
    with patch("api.routers.tasks.redis_client") as mock:
        yield mock


@pytest.fixture
def mock_celery_app():
    with patch("api.routers.tasks.celery_app") as mock:
        yield mock


class TestCreateTask:
    @patch("api.routers.tasks.process_video")
    @patch("api.routers.tasks._init_task_meta")
    @patch("api.routers.tasks._build_task_info")
    def test_create_task_success(self, mock_build, mock_init, mock_process):
        mock_build.return_value = {
            "id": "test-uuid",
            "status": "pending",
            "url": "https://www.facebook.com/watch?v=123",
            "language": "auto",
            "output_format": "json",
            "use_local": True,
            "model_size": "small",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
        }

        response = client.post(
            "/tasks",
            json={
                "url": "https://www.facebook.com/watch?v=123",
                "language": "auto",
                "output_format": "json",
                "use_local": True,
            },
            headers=HEADERS,
        )

        assert response.status_code == 202
        mock_init.assert_called_once()
        mock_process.apply_async.assert_called_once()

    def test_create_task_missing_api_key(self):
        response = client.post(
            "/tasks",
            json={"url": "https://www.facebook.com/watch?v=123"},
        )
        assert response.status_code == 401

    def test_create_task_invalid_api_key(self):
        response = client.post(
            "/tasks",
            json={"url": "https://www.facebook.com/watch?v=123"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_create_task_invalid_url_type(self):
        response = client.post(
            "/tasks",
            json={"url": 123},
            headers=HEADERS,
        )
        assert response.status_code == 422

    def test_create_task_missing_url(self):
        response = client.post(
            "/tasks",
            json={},
            headers=HEADERS,
        )
        assert response.status_code == 422


def _make_task_info(task_id: str, status: str = "pending") -> dict:
    now = datetime.now().isoformat()
    return {
        "id": task_id,
        "status": status,
        "url": "https://www.facebook.com/watch?v=123",
        "language": "auto",
        "output_format": "json",
        "use_local": True,
        "model_size": "small",
        "created_at": now,
        "progress": 0,
    }


class TestListTasks:
    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_success(self, mock_build, mock_redis):
        mock_redis.keys.return_value = ["task_meta:task-1", "task_meta:task-2"]
        mock_build.side_effect = [
            _make_task_info("task-1", "completed"),
            _make_task_info("task-2", "pending"),
        ]

        response = client.get("/tasks", headers=HEADERS)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "task-1"

    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_with_pagination(self, mock_build, mock_redis):
        mock_redis.keys.return_value = [
            "task_meta:task-1",
            "task_meta:task-2",
            "task_meta:task-3",
        ]
        mock_build.side_effect = [
            _make_task_info("task-1"),
            _make_task_info("task-2"),
        ]

        response = client.get("/tasks?skip=0&limit=2", headers=HEADERS)

        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_skip_broken_meta(self, mock_build, mock_redis):
        mock_redis.keys.return_value = ["task_meta:task-1", "task_meta:broken"]
        from fastapi import HTTPException

        def side_effect(task_id):
            if task_id == "broken":
                raise HTTPException(status_code=404)
            return _make_task_info(task_id)

        mock_build.side_effect = side_effect

        response = client.get("/tasks", headers=HEADERS)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_tasks_missing_api_key(self):
        response = client.get("/tasks")
        assert response.status_code == 401


class TestGetTask:
    @patch("api.routers.tasks._build_task_info")
    def test_get_task_success(self, mock_build):
        mock_build.return_value = {
            "id": "task-123",
            "status": "completed",
            "url": "https://example.com",
            "language": "en",
            "output_format": "json",
            "use_local": True,
            "model_size": "small",
            "created_at": datetime.now().isoformat(),
            "progress": 100,
        }

        response = client.get("/tasks/task-123", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["id"] == "task-123"

    @patch("api.routers.tasks._build_task_info")
    def test_get_task_not_found(self, mock_build):
        from fastapi import HTTPException

        mock_build.side_effect = HTTPException(status_code=404, detail="任务不存在")

        response = client.get("/tasks/nonexistent", headers=HEADERS)
        assert response.status_code == 404


class TestDownloadResult:
    @patch("api.routers.tasks._get_task_meta")
    def test_download_completed_task(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text('{"test": true}')

            response = client.get("/tasks/task-123/download", headers=HEADERS)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    @patch("api.routers.tasks._get_task_meta")
    def test_download_task_not_completed(self, mock_get_meta):
        mock_get_meta.return_value = {
            "status": "pending",
            "output_format": "json",
        }

        response = client.get("/tasks/task-123/download", headers=HEADERS)
        assert response.status_code == 400

    @patch("api.routers.tasks._get_task_meta")
    def test_download_file_not_found(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            response = client.get("/tasks/task-123/download", headers=HEADERS)
            assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_download_task_not_exists(self, mock_get_meta):
        mock_get_meta.return_value = {}

        response = client.get("/tasks/task-123/download", headers=HEADERS)
        assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_download_txt_format(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "txt",
            }

            output_file = tmp_path / "task-123.txt"
            output_file.write_text("Hello world")

            response = client.get("/tasks/task-123/download", headers=HEADERS)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestGetTaskResult:
    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_completed_json(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "completed",
                "language": "en",
                "duration": "10.5",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text(
                json.dumps(
                    {
                        "segments": [{"id": 1, "text": "Hello"}],
                        "full_text": "Hello world",
                    }
                )
            )

            response = client.get("/tasks/task-123/result", headers=HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["segments"] == [{"id": 1, "text": "Hello"}]
            assert data["full_text"] == "Hello world"

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_pending(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "pending",
                "output_format": "json",
            }

            response = client.get("/tasks/task-123/result", headers=HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["segments"] is None
            assert data["full_text"] is None

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_task_not_exists(self, mock_get_meta):
        mock_get_meta.return_value = {}

        response = client.get("/tasks/task-123/result", headers=HEADERS)
        assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_corrupted_json(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_settings.api_key = API_KEY
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text("not valid json")

            response = client.get("/tasks/task-123/result", headers=HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data["segments"] is None
