from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    temp_dir: str = os.getenv("TEMP_DIR", "storage/temp")
    max_message_chars: int = int(os.getenv("MAX_MESSAGE_CHARS", "3900"))
    max_summary_input_chars: int = int(os.getenv("MAX_SUMMARY_INPUT_CHARS", "25000"))
    database_url: str = os.getenv("DATABASE_URL", "")


settings = Settings()