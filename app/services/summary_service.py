from app.ai.summarizer import summarize_text


async def generate_summary(transcript_text: str, mode: str = "short") -> str:
    return await summarize_text(transcript_text, mode=mode)
