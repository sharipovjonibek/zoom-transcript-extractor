from __future__ import annotations

import asyncio
from collections import Counter
import re

from app.ai.prompts import build_detailed_summary_prompt, build_short_summary_prompt
from app.config import settings

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore


STOPWORDS = {
    "about", "after", "again", "all", "also", "and", "are", "been", "before",
    "being", "but", "can", "could", "did", "does", "doing", "for", "from",
    "had", "has", "have", "into", "just", "like", "more", "most", "need",
    "not", "now", "our", "out", "said", "should", "some", "than", "that",
    "the", "their", "them", "there", "they", "this", "those", "through",
    "today", "very", "was", "were", "what", "when", "where", "which", "while",
    "will", "with", "would", "yeah", "okay", "your", "you",
}


async def summarize_text(text: str, mode: str = "short") -> str:
    cleaned = text.strip()
    if not cleaned:
        return "No transcript content was available to summarize."

    if settings.gemini_api_key and genai is not None:
        try:
            return await llm_summary(cleaned, mode=mode)
        except Exception:
            pass

    return heuristic_summary(cleaned, mode=mode)


async def llm_summary(text: str, mode: str = "short") -> str:
    prompt = (
        build_short_summary_prompt(text)
        if mode == "short"
        else build_detailed_summary_prompt(text)
    )
    return await asyncio.to_thread(_sync_gemini_generate, prompt)


def _sync_gemini_generate(prompt: str) -> str:
    if genai is None:
        raise RuntimeError("google-genai is not installed.")

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if text and text.strip():
        return text.strip()

    raise RuntimeError("Gemini returned an empty response.")


def heuristic_summary(text: str, mode: str = "short") -> str:
    speaker_turns = extract_speaker_turns(text)
    candidate_points = extract_candidate_points(text)
    keywords = extract_keywords(text)

    speaker_summary = (
        ", ".join(f"{speaker} ({count})" for speaker, count in speaker_turns.items())
        if speaker_turns
        else "unknown"
    )
    keyword_summary = ", ".join(keywords[:5]) if keywords else "none"

    if mode == "detailed":
        selected_points = candidate_points[:6] or ["No clear discussion points were extracted."]
        points_text = "\n".join(f"- {point}" for point in selected_points)
        return (
            "Detailed summary\n\n"
            f"Speaker activity: {speaker_summary}\n"
            f"Frequent topics: {keyword_summary}\n\n"
            "Main discussion points:\n"
            f"{points_text}"
        )

    selected_points = candidate_points[:3] or ["No clear discussion points were extracted."]
    points_text = "\n".join(f"- {point}" for point in selected_points)

    return (
        "Main points:\n"
        f"{points_text}\n\n"
        f"Important topics: {keyword_summary}\n"
        "Quick takeaway: the discussion mainly focused on the points above."
    )


def extract_speaker_turns(text: str) -> Counter:
    counter: Counter = Counter()

    for block in text.split("\n\n"):
        first_line = block.splitlines()[0] if block.splitlines() else ""
        match = re.search(r"\]\s*(.+?):$", first_line)
        if match:
            speaker = match.group(1).strip()
            counter[speaker] += 1
        elif ":" in first_line:
            speaker = first_line.split(":", 1)[0].strip()
            if speaker:
                counter[speaker] += 1

    return counter


def extract_candidate_points(text: str) -> list[str]:
    points: list[str] = []

    for block in text.split("\n\n"):
        lines = block.splitlines()
        if len(lines) < 2:
            continue

        body = " ".join(line.strip() for line in lines[1:] if line.strip())
        body = re.sub(r"\s+", " ", body).strip()

        if len(body.split()) < 4:
            continue

        if len(body) > 180:
            body = body[:177].rsplit(" ", 1)[0] + "..."

        points.append(body)

    return points


def extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    filtered = [word for word in words if word not in STOPWORDS]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(8)]