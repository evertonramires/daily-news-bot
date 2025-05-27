# Daily News Bot

This project is a simple AI agent that fetches daily news from the internet and generates custom opinions using the Google Gemini LLM.

## Prerequisites

- Python
- [uv](https://github.com/astral-sh/uv)
- [Google Gemini API key](https://aistudio.google.com/app/apikey)
- [Gnews API Key](https://gnews.io/)

## Installation

```bash
cp .env.EXAMPLE .env
#then edit .env to add your api keys, save. 
uv venv
source venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

```bash
uv run main.py
```
