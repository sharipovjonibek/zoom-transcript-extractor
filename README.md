# Meeting Assistant Bot

AI-powered Telegram bot for cleaning Zoom meeting transcripts, extracting selected speaker conversations, and generating concise meeting summaries.

The bot helps teams review meetings faster by turning raw Zoom `.txt` transcripts into focused, readable notes with optional Gemini-powered summaries.

## Features

- Upload Zoom `.txt` transcript files through Telegram
- Detect speakers automatically
- Select one or two speakers for extraction
- Filter transcript content by optional start and end time
- Generate a cleaned transcript file
- Create an optional AI summary with Google Gemini
- Fall back to a basic local summary if Gemini is unavailable
- Track bot users in PostgreSQL
- Clean up temporary upload/output files automatically
- Send admin broadcast updates

## Workflow

1. Start the bot with `/start`.
2. Upload a Zoom transcript `.txt` file.
3. Choose the speaker or speakers you want to extract.
4. Optionally provide a start and end time.
5. Receive a cleaned transcript file.
6. Optionally generate an AI summary.

## Tech Stack

- Python 3.12
- aiogram 3
- Google Gemini API
- PostgreSQL with asyncpg
- Async Python architecture

## Project Structure

```text
app/
  ai/          Gemini prompt and summary logic
  handlers/    Telegram command and conversation handlers
  keyboards/   Telegram reply and inline keyboards
  parsers/     Zoom transcript parsing
  services/    File, user, extraction, summary, and broadcast services
  utils/       Time and text cleanup helpers
tests/         Unit tests for parser, extraction, time, and summary behavior
```

## Setup

Clone the repository:

```bash
git clone https://github.com/your-username/meeting-assistant-bot.git
cd meeting-assistant-bot
```

Create and activate a virtual environment:

```bash
python -m venv myenv
source myenv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_postgresql_url

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

ADMIN_ID=your_telegram_user_id

TEMP_DIR=storage/temp
MAX_MESSAGE_CHARS=3900
MAX_SUMMARY_INPUT_CHARS=25000
MAX_UPLOAD_BYTES=10485760
```

## Running

Start the bot:

```bash
python -m app.main
```

Run tests:

```bash
python -m unittest discover
```

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather |
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `GEMINI_API_KEY` | No | Gemini API key for AI summaries |
| `GEMINI_MODEL` | No | Gemini model name, defaults to `gemini-2.5-flash` |
| `ADMIN_ID` | No | Telegram user ID allowed to run admin broadcast |
| `TEMP_DIR` | No | Temporary file directory, defaults to `storage/temp` |
| `MAX_MESSAGE_CHARS` | No | Telegram message chunk size, defaults to `3900` |
| `MAX_SUMMARY_INPUT_CHARS` | No | Maximum transcript characters sent to summary generation |
| `MAX_UPLOAD_BYTES` | No | Maximum accepted upload size in bytes |

## Notes

- The bot uses polling mode.
- PostgreSQL is required because user tracking and broadcasts depend on it.
- Uploaded and generated files are stored temporarily and removed during normal flow cleanup.
- If Gemini is not configured or fails, the bot still returns a basic local summary.
