from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _get_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")

    return value


def _get_optional_int(name: str) -> int | None:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return None

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    temp_dir: str = os.getenv("TEMP_DIR", "storage/temp")
    max_message_chars: int = _get_positive_int("MAX_MESSAGE_CHARS", 3900)
    max_summary_input_chars: int = _get_positive_int("MAX_SUMMARY_INPUT_CHARS", 25000)
    max_upload_bytes: int = _get_positive_int("MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
    database_url: str = os.getenv("DATABASE_URL", "")
    admin_id: int | None = _get_optional_int("ADMIN_ID")


settings = Settings()
