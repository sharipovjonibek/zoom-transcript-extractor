# 🤖 Meeting Assistant Bot

AI-powered Telegram bot that extracts speaker conversations from Zoom meeting transcripts and generates clear meeting summaries.

This tool helps teams quickly understand discussions, identify action items, and review meeting outcomes without reading the entire transcript.

---

# Features

- Upload Zoom `.txt` transcript files
- Extract messages from specific speakers
- Filter conversations by time range
- Generate a clean transcript
- Optional AI-powered meeting summary (Gemini)
- Supports selecting up to two speakers
- Simple Telegram-based workflow
- Automatic temporary file cleanup
- User activity tracking with PostgreSQL

---

# Example [Workflow](https://wise-shake-264.notion.site/Zoom-Transcript-Extractor-Bot-32295fdf11748043b3d1dbadd59fcb83?source=copy_link)

1. User uploads a Zoom transcript `.txt` file.
2. Bot detects speakers in the meeting.
3. User selects one or two speakers.
4. Optional time filtering can be applied.
5. Bot generates a clean transcript.
6. User can request an AI-generated summary.

---

# Tech Stack

- **Python 3.12**
- **aiogram** — Telegram bot framework
- **Google Gemini API** — AI summaries
- **PostgreSQL** — user tracking
- **Railway** — deployment platform
- **Async Python architecture**

---

# Installation

```bash
git clone https://github.com/your-username/meeting-assistant-bot.git
cd meeting-assistant-bot
```

Create a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create a .env file:
```bash
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

DATABASE_URL=your_postgresql_url

TEMP_DIR=storage/temp
MAX_MESSAGE_CHARS=3900
MAX_SUMMARY_INPUT_CHARS=25000
```

Start the bot:
```bash
python -m app.main
```



