from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import Document

from app.config import settings


def get_base_temp_dir() -> Path:
    return Path(settings.temp_dir)


def get_upload_dir() -> Path:
    return get_base_temp_dir() / "uploads"


def get_output_dir() -> Path:
    return get_base_temp_dir() / "outputs"


def ensure_storage_dirs() -> None:
    get_upload_dir().mkdir(parents=True, exist_ok=True)
    get_output_dir().mkdir(parents=True, exist_ok=True)


async def download_user_file(bot: Bot, document: Document) -> Path:
    ensure_storage_dirs()

    original_name = document.file_name or "transcript.txt"
    suffix = Path(original_name).suffix or ".txt"
    file_path = get_upload_dir() / f"{uuid4().hex}{suffix}"

    await bot.download(document, destination=file_path)
    return file_path


def read_text_file(file_path: Path) -> str:
    encodings = ["utf-8-sig", "utf-8", "utf-16", "latin-1"]

    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    return file_path.read_text(encoding="utf-8", errors="ignore")


def write_text_file(content: str, prefix: str, suffix: str = ".txt") -> Path:
    ensure_storage_dirs()
    file_path = get_output_dir() / f"{prefix}{uuid4().hex}{suffix}"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def delete_file(file_path: Path | None) -> None:
    if not file_path:
        return

    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass


def cleanup_old_temp_files(max_age_minutes: int = 60) -> None:
    ensure_storage_dirs()
    cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

    for folder in [get_upload_dir(), get_output_dir()]:
        for file_path in folder.iterdir():
            if not file_path.is_file():
                continue

            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if modified_time < cutoff:
                delete_file(file_path)
