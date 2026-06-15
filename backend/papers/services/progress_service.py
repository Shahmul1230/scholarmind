from datetime import datetime
from threading import Lock


_PROGRESS_STORE = {}
_PROGRESS_LOCK = Lock()


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def init_progress(upload_id):
    if not upload_id:
        return

    with _PROGRESS_LOCK:
        _PROGRESS_STORE[upload_id] = {
            "upload_id": upload_id,
            "status": "processing",
            "stage": "Starting",
            "percent": 1,
            "details": "Upload request received.",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }


def update_progress(upload_id, stage=None, percent=None, details=None, status="processing"):
    if not upload_id:
        return

    with _PROGRESS_LOCK:
        current = _PROGRESS_STORE.get(upload_id, {
            "upload_id": upload_id,
            "status": "processing",
            "stage": "Starting",
            "percent": 1,
            "details": "Processing started.",
            "created_at": now_iso(),
        })

        if stage is not None:
            current["stage"] = stage

        if percent is not None:
            current["percent"] = max(0, min(100, int(percent)))

        if details is not None:
            current["details"] = details

        current["status"] = status
        current["updated_at"] = now_iso()

        _PROGRESS_STORE[upload_id] = current


def complete_progress(upload_id, details="Document is ready."):
    update_progress(
        upload_id=upload_id,
        stage="Completed",
        percent=100,
        details=details,
        status="completed",
    )


def fail_progress(upload_id, details="Processing failed."):
    update_progress(
        upload_id=upload_id,
        stage="Failed",
        percent=100,
        details=details,
        status="failed",
    )


def get_progress(upload_id):
    if not upload_id:
        return {
            "upload_id": upload_id,
            "status": "unknown",
            "stage": "Unknown",
            "percent": 0,
            "details": "No upload id provided.",
        }

    with _PROGRESS_LOCK:
        progress = _PROGRESS_STORE.get(upload_id)

        if not progress:
            return {
                "upload_id": upload_id,
                "status": "unknown",
                "stage": "Waiting",
                "percent": 0,
                "details": "Progress has not started yet.",
            }

        return progress