import os
import subprocess
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load API keys from .env
# override=True: this script runs as a child of systemd services that export
# their own TELEGRAM_BOT_TOKEN etc. Without it, the inherited value silently
# wins and notifications go out from the wrong bot.
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or os.getenv("GEMINI_MODEL", "gpt-4o-mini")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

_client = None


def get_llm_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("Missing OPENAI_API_KEY (or legacy GEMINI_API_KEY) in your environment.")

        if OPENAI_BASE_URL:
            _client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL.rstrip("/"),
            )
        else:
            _client = OpenAI(api_key=OPENAI_API_KEY)

    return _client


def generate_text(messages, temperature=0.2):
    response = get_llm_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )

    message = response.choices[0].message.content or ""
    return message.strip()

# Persona
personality = """
You are in a roleplay with the following STRICT rules:
your name is "Sofia"
you are a tech journalist and enthusiast
you ALWAYS answer in English, regardless of the language of the input or the headlines
You always mention that all the sources are at the section below
Your answer should have a BIG headline 
Your answer is markdown formatted and may have emojis
Your answer use bold text for the most important parts 
You always output a complete answer within less than 1000 characters 
"""

def notify(message):
    """Send a short status line straight to Telegram via the Bot API."""
    validNotification = evaluate_notification(message)

    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("No Telegram bot token / chat id configured for notifications.")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": validNotification,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        response.raise_for_status()
        print(f"✅Notification sent: {validNotification}")
    except requests.RequestException as e:
        # Never let a failed notification break a successful publish.
        detail = ""
        if getattr(e, "response", None) is not None:
            detail = f" — {e.response.text[:200]}"
        print(f"Failed to send notification: {e}{detail}")

# Function to evaluate text that will be sent to webhook
def evaluate_notification(notificationText):
    try:
        text = generate_text(
            [
                {
                    "role": "user",
                    "content": f""" Evaluate the text bellow and IF it is greater than 140 characters, summarize it.
              Always write your answer in English, regardless of the language of the input.
              your final answer is ONLY the original text if it is small enought OR a small summary you created. Go ahead, analyze this text:\n\n
            
            {notificationText}\n\n""",
                }
            ],
            temperature=0,
        )

        if len(text) > 140:
            text = text[:137].rstrip() + "..."

        print(f"Notification evaluation result: {text}")
        # Keep the caller's status marker (❌ / 🧪) instead of stamping ✅ on errors.
        marker = str(notificationText).lstrip()[:1]
        if marker in ("❌", "🧪", "✅") and not text.startswith(marker):
            text = f"{marker} {text}"
        elif marker not in ("❌", "🧪", "✅"):
            text = f"✅ {text}"
        return text
    except Exception as e:
        print(f"Error: {e}")
        fallback = str(notificationText)
        if len(fallback) > 140:
            fallback = fallback[:137].rstrip() + "..."
        return fallback
    

def evaluate_opinion(opinion):
    try:
        result = generate_text(
            [
                {
                    "role": "user",
                    "content": f""" Evaluate this opinion and answer 0 if this is not a valid opinion or 1 if this is indeed a valid opinion:\n\n
            
            {opinion}\n\n
            
            
            A valid opinion must talk about tech news.
            An invalid opinion is one asking for more information or complaining about apis missing or errors.
            
            Remember, you can only answer with a single number, either 0 for false or 1 for true. NOTHING ELSE.
            \n\nYour final answer is (0 or 1):""",
                }
            ],
            temperature=0,
        )

        opinion_result = "1" if result.startswith("1") else "0"
        return opinion_result
    except Exception as e:
        print(f"Error: {e}")
        notify(str(e))
        return "0"


# Function to interact with the OpenAI-compatible model
def tailor_opinion(news):
    try:
        return generate_text(
            [
                {
                    "role": "system",
                    "content": personality,
                },
                {
                    "role": "user",
                    "content": f"These are the news you must tailor an intelligent opinion for today:\n{news}\n\nYour opinion:",
                },
            ]
        )
    except Exception as e:
        print(f"Error: {e}")
        notify(str(e))
        return str(e)

# Function to fetch technology news from GNews API
def fetch_tech_news():
    print("\n📰 Fetching Latest Tech Headlines... \n")
    try:
        api_key = os.getenv("GNEWS_API_KEY")
        if not api_key:
            raise ValueError("Missing GNEWS_API_KEY in your environment.")
        url = f"https://gnews.io/api/v4/search?q=technology&lang=en&topic=technology&max=5&token={api_key}"
        response = requests.get(url, timeout=20)
        news_data = response.json()
        if response.status_code != 200 or "articles" not in news_data:
            raise RuntimeError(f"GNews HTTP {response.status_code}: {news_data.get('errors', news_data)}")
        if not news_data["articles"]:
            raise RuntimeError("GNews returned no articles.")

        news_lines = []
        display_lines = []

        for idx, article in enumerate(news_data.get("articles", []), start=1):
            line = f"{idx}. {article['title']} ({article['source']['name']})\n   {article['url']}"
            news_lines.append(line)
            display_lines.append(line)

        return "\n".join(news_lines), "\n".join(display_lines)

    except Exception as e:
        print("Failed to fetch news:", e)
        notify(f"❌ Failed to fetch news: {e}")
        return "", ""

# Main routine
if __name__ == "__main__":
    # --dry-run: run the whole pipeline (news, opinion, validation, Telegram
    # notification) but do NOT touch README.md, commit or push.
    dry_run = "--dry-run" in sys.argv[1:]
    try:
        news, sources = fetch_tech_news()
        if not news:
            print("\n❌ No news fetched. Exiting.")
            sys.exit(1)
        opinion = tailor_opinion(news)
        opinionValidity = evaluate_opinion(opinion)
        today = datetime.now().strftime("%Y-%m-%d")

        if opinionValidity == "0":
            print("\n❌ Invalid opinion generated. Exiting.")
            notify(f"❌ Invalid opinion generated. News not published for {today}.")
            sys.exit(1)
        elif opinionValidity == "1":
            headline = f"What happens in tech today ({today}):"

            support_button = "[![Support my work ❤️](https://img.shields.io/badge/Support%20my%20work%20❤️-orange?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/c/evertonics)"

            final_news = f"{support_button}\n\n{headline}\n\n{opinion}\n\nSources:\n{sources}"

            print(f"\n{opinion[:140]}\n")

            if dry_run:
                print("\n🧪 DRY RUN: skipping README.md write, commit and push.\n")
                print(final_news)
                notify(f"🧪 DRY RUN ok for {today}.\n\n{opinion[:140]}")
                sys.exit(0)

            with open("README.md", "w", encoding="utf-8") as f:
                f.write(final_news)

            print("\n✅ Output saved to README.md\n")

            # Git commit and push (plain push: a rejected push is reported via
            # Telegram instead of silently overwriting whatever is on origin).
            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(["git", "commit", "-m", f"Update tech news for {today}"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
            print("✅ Changes committed and pushed to origin.")
            notify(f"✅ News Published for {today}.\n\n{opinion[:140]}")

    except SystemExit:
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        notify(f"❌ Error while publishing news: {str(e)}")
        sys.exit(1)
    except Exception as e:
        # Anything unexpected (disk, network, API) must still reach Telegram.
        print(f"Error: {e}")
        notify(f"❌ daily-news-bot crashed: {type(e).__name__}: {e}")
        sys.exit(1)
