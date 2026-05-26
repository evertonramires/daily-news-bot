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
source venv/bin/activate
uv pip install -r requirements.txt
```

Set your API settings in `.env`:

```env
OPENAI_API_KEY="your_openai_or_compatible_key_here"
OPENAI_MODEL="gpt-4o-mini"
# Optional for compatible providers (OpenRouter, local gateways, etc.)
# OPENAI_BASE_URL="https://api.openai.com/v1"

GNEWS_API_KEY="your_gnews_api_key_here"
NOTIFICATION_WEBHOOK_URL="https://your-webhook-url"
```

## Usage

```bash
uv run main.py
```
