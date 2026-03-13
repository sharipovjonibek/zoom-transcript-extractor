from app.ai.summarizer import summarize_text
from app.config import settings


async def generate_summary(transcript_text: str, mode: str = "short") -> str:
    return await summarize_text(transcript_text, mode=mode)