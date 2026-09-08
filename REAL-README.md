# Daily News Bot

This project is a simple AI agent that fetches daily news from the internet and generates custom opinions using an OpenAI-compatible LLM API.

## Prerequisites

- Python
- [uv](https://github.com/astral-sh/uv)
- OpenAI-compatible API key
- [Gnews API Key](https://gnews.io/)

## Installation

```bash
cp .env.EXAMPLE .env
#then edit .env to add your api keys, save. 
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Set your API settings in `.env`:

```env
OPENAI_API_KEY="your_openai_or_compatible_key_here"
OPENAI_MODEL="gpt-4o-mini"
# Optional for compatible providers (OpenRouter, local gateways, etc.)
# OPENAI_BASE_URL="https://api.openai.com/v1"

GNEWS_API_KEY="your_gnews_api_key_here"

# Telegram notifications (token from @BotFather, chat id of the destination chat)
TELEGRAM_BOT_TOKEN="123456:your_bot_token_here"
TELEGRAM_CHAT_ID="your_numeric_chat_id_here"
```

## Usage

```bash
uv run main.py            # fetch, write README.md, commit, push, notify
uv run main.py --dry-run  # same pipeline, but no README write / commit / push
```

Status notifications (success, invalid opinion, any error) are sent to Telegram via the Bot API.
