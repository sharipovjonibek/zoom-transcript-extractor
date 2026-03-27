PROMPT_LIBRARY = {
    "meeting": {
        "title": "🧠 Meeting",
        "prompts": [
            {
                "id": "summary_prompt",
                "title": "Detailed Meeting Summary",
                "text": """I have a meeting transcript where a team member explains a project and outlines what needs to be done.

Your task is to review the transcript and provide a clear, action-oriented breakdown so I can quickly understand the discussion and know exactly what to do next.

🔹 1. Project Summary
- Summarize the overall purpose and main objective in 8–10 clear sentences.
- If multiple topics were discussed, split into 3–5 parts.
- Explain each part in 3–4 sentences.

🔹 2. Top 3–5 Topics Discussed
- Identify the most important topics.
- For each topic, provide a 4–5 sentence explanation.
- Explain both what was said and why it matters.

🔹 3. Tasks & Deliverables
- Extract all tasks, deliverables, or expected outputs.
- Present as a clean bullet list or checklist.
- Group logically if needed.

🔹 4. Step-by-Step Action Plan
- Break down what I need to do in the correct order.
- Write in a clear, actionable format (5–10 sentences).

🔹 5. Next Actions (Immediate Focus)
- Summarize what I should do right now to begin execution.
- Keep it specific, practical, and action-oriented (5–10 sentences).

After reading your output, I should be able to start working immediately without confusion."""
            },
            {
                "id": "meeting_helper",
                "title": "Meeting Answer Helper",
                "text": """You are my senior data engineer assistant.

Goal:
Help me answer work questions, explain tasks, or prepare updates in a natural, conversational, and friendly tone.

Context:
- I will provide transcripts, screenshots, task descriptions, code, or errors.
- Always prioritize my provided context.
- If context is unclear, use best practices (Azure, Databricks, Snowflake, SQL, dbt, ADF, CI/CD).
- If unsure, say:
  "This might need deeper research, let’s flag it and come back."

Output:
- Short conversational paragraph (like speaking in a meeting).
- Friendly, clear, non-robotic tone.
- Use natural phrasing like “basically”, “actually”, “I would say…”.
- Keep it simple and easy to explain aloud.
- If multiple options exist, summarize the best 1–2.

Quality:
- Do NOT invent fake details.
- If context is missing, clearly say what is needed."""
            },
        ],
    },

    "communication": {
        "title": "📢 Communication",
        "prompts": [
            {
                "id": "speech_preparation",
                "title": "Speech Preparation",
                "text": """Write a natural, conversational speech for me to present to my team as a Senior Data Engineer.

Context:
- I will explain actual code changes I made.

Requirements:
- Include real technical details (function names, notebook structure, logic changes).
- Explain everything in simple English.
- Avoid complex vocabulary.
- Keep it 100% accurate — do NOT add anything not in the code.

Tone:
- Friendly and natural (not scripted).
- Start like:
  "Hey team, I’ll walk you through the updates I made…"

Structure:
- Explain step-by-step:
  - what changed
  - how it works now
  - why the change was made

Output:
- Plain text only (no code)
- Easy to read aloud in a meeting"""
            },
            {
                "id": "questions_follow_up",
                "title": "Follow-up Questions",
                "text": """Based on what I present, generate 5 realistic questions my teammates or manager might ask.

For each question:
- Provide a clear and concise answer
- Keep answers conversational and natural
- Focus on technical clarity and confidence"""
            },
        ],
    },
}