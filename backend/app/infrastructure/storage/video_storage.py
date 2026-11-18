"""Local video storage service (filesystem). MinIO can replace this adapter later."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".mpeg", ".mpg", ".m4v", ".ts"}
ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/mpeg",
    "video/x-m4v",
    "video/mp2t",
    "application/octet-stream",
}


class VideoStorageError(Exception):
    pass


class LocalVideoStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or Path(settings.video_upload_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "samples").mkdir(parents=True, exist_ok=True)

    def validate(self, filename: str, content_type: str | None, size: int | None) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise VideoStorageError(
                f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            # still allow if extension is valid (some browsers send odd types)
            logger.warning("Unusual content-type for video upload: %s", content_type)
        if size is not None and size > settings.max_upload_bytes:
            mb = settings.max_upload_bytes / (1024 * 1024)
            raise VideoStorageError(f"File too large. Max {mb:.0f} MB")
        return ext

    async def save_upload(self, file: UploadFile) -> dict:
        original = file.filename or "cctv.mp4"
        safe_original = re.sub(r"[^\w.\-]+", "_", original)[:180]
        ext = self.validate(safe_original, file.content_type, None)

        asset_id = uuid.uuid4()
        stored_name = f"{asset_id.hex}{ext}"
        dest = self.root / stored_name

        size = 0
        async with aiofiles.open(dest, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    await out.close()
                    dest.unlink(missing_ok=True)
                    mb = settings.max_upload_bytes / (1024 * 1024)
                    raise VideoStorageError(f"File too large. Max {mb:.0f} MB")
                await out.write(chunk)

        logger.info("Stored CCTV upload %s (%s bytes)", stored_name, size)
        return {
            "id": asset_id,
            "original_filename": safe_original,
            "stored_filename": stored_name,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": size,
            "storage_path": str(dest.resolve()),
        }

    def list_sample_files(self) -> list[dict]:
        samples_dir = self.root / "samples"
        items = []
        for p in sorted(samples_dir.glob("*")):
            if p.suffix.lower() in ALLOWED_EXTENSIONS and p.is_file():
                items.append(
                    {
                        "filename": p.name,
                        "size_bytes": p.stat().st_size,
                        "path": str(p.resolve()),
                    }
                )
        return items
