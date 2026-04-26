import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import redis
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from api.celery_app import celery_app
from api.core.config import get_settings
from api.models.schemas import OutputFormat, TaskCreate, TaskInfo, TaskResult
from api.tasks.worker import _get_task_meta, _init_task_meta, process_video

settings = get_settings()
router = APIRouter(prefix="/tasks", tags=["tasks"])

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not key or key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key",
        )
    return key


def _build_task_info(task_id: str) -> TaskInfo:
    meta = _get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="任务不存在")

    async_result = AsyncResult(task_id, app=celery_app)

    # Celery 状态优先
    celery_state = async_result.state or meta.get("status", "pending")
    status_map = {
        "PENDING": "pending",
        "STARTED": "downloading",
        "DOWNLOADING": "downloading",
        "EXTRACTING_AUDIO": "extracting_audio",
        "TRANSCRIBING": "transcribing",
        "SAVING": "transcribing",
        "SUCCESS": "completed",
        "FAILURE": "failed",
        "RETRY": "pending",
    }
    mapped_status = status_map.get(celery_state, meta.get("status", "pending"))

    created_at = meta.get("created_at")
    updated_at = meta.get("updated_at")
    completed_at = meta.get("completed_at")

    return TaskInfo(
        id=task_id,
        status=mapped_status,
        url=meta.get("url", ""),
        language=meta.get("language", "auto"),
        output_format=OutputFormat(meta.get("output_format", "json")),
        use_local=meta.get("use_local", "True").lower() == "true",
        model_size=meta.get("model_size", "small"),
        created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
        updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
        completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
        error_message=meta.get("error_message") or None,
        result_url=meta.get("result_url") or None,
        progress=int(meta.get("progress", 0)),
    )


ACTIVE_STATUSES = {"pending", "downloading", "extracting_audio", "transcribing"}


@router.post("", response_model=TaskInfo, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    payload: TaskCreate,
    api_key: str = Depends(verify_api_key),
):
    # 防重：检查同一 URL 是否已有正在进行的任务
    for key in redis_client.keys("task_meta:*"):
        meta = redis_client.hgetall(key)
        if meta.get("url") == payload.url and meta.get("status") in ACTIVE_STATUSES:
            existing_task_id = key.replace("task_meta:", "")
            return _build_task_info(existing_task_id)

    task_id = str(uuid4())
    params = {
        "language": payload.language,
        "output_format": payload.output_format.value,
        "use_local": payload.use_local,
        "model_size": payload.model_size.value,
        "device": payload.device.value,
    }

    # 初始化元数据
    _init_task_meta(task_id, payload.url, params)

    # 提交 Celery 任务
    process_video.apply_async(args=[task_id, payload.url, params], task_id=task_id)

    return _build_task_info(task_id)


@router.get("", response_model=list[TaskInfo])
def list_tasks(
    skip: int = 0,
    limit: int = 20,
    api_key: str = Depends(verify_api_key),
):
    keys = redis_client.keys("task_meta:*")

    all_tasks = []
    for key in keys:
        task_id = key.replace("task_meta:", "")
        try:
            info = _build_task_info(task_id)
            all_tasks.append(info)
        except Exception:
            continue

    # 按 completed_at 倒序（最近完成在前），未完成的排最后
    completed = [t for t in all_tasks if t.completed_at is not None]
    pending = [t for t in all_tasks if t.completed_at is None]
    completed.sort(key=lambda x: x.completed_at, reverse=True)
    all_tasks = completed + pending

    return all_tasks[skip : skip + limit]


@router.get("/{task_id}", response_model=TaskInfo)
def get_task(
    task_id: str,
    api_key: str = Depends(verify_api_key),
):
    return _build_task_info(task_id)


@router.get("/{task_id}/download")
def download_result(
    task_id: str,
    api_key: str = Depends(verify_api_key),
):
    meta = _get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="任务不存在")

    if meta.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    output_format = meta.get("output_format", "json")
    output_path = Path(settings.output_dir) / f"{task_id}.{output_format}"

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="结果文件已删除")

    media_type_map = {
        "json": "application/json",
        "txt": "text/plain",
        "srt": "text/plain",
        "vtt": "text/vtt",
    }

    return FileResponse(
        path=str(output_path),
        media_type=media_type_map.get(output_format, "application/octet-stream"),
        filename=f"transcript_{task_id}.{output_format}",
    )


@router.get("/{task_id}/result", response_model=TaskResult)
def get_task_result(
    task_id: str,
    api_key: str = Depends(verify_api_key),
):
    meta = _get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="任务不存在")

    status_val = meta.get("status", "pending")
    output_format = meta.get("output_format", "json")
    output_path = Path(settings.output_dir) / f"{task_id}.{output_format}"

    result_data = {
        "id": task_id,
        "status": status_val,
        "language": meta.get("language") or None,
        "duration": float(meta.get("duration", 0)) or None,
        "segments": None,
        "full_text": None,
        "output_file": str(output_path) if output_path.exists() else None,
        "video_url": meta.get("video_url") or None,
        "error_message": meta.get("error_message") or None,
    }

    if status_val == "completed" and output_path.exists() and output_format == "json":
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
            result_data["segments"] = data.get("segments")
            result_data["full_text"] = data.get("full_text")
        except Exception:
            pass

    return TaskResult(**result_data)


@router.get("/{task_id}/download-video")
def download_video(
    task_id: str,
    api_key: str = Depends(verify_api_key),
):
    meta = _get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="任务不存在")

    if meta.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    video_path = Path(settings.output_dir) / f"{task_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件已删除")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"video_{task_id}.mp4",
    )
