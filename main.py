import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from datetime import datetime
import subprocess

# Load API keys from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

webhook_url = os.getenv("NOTIFICATION_WEBHOOK_URL")

# Load model
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-pro"))

# Persona
personality = """
You are in a roleplay with the following STRICT rules:
your name is "Sofia"
you are a tech journalist and enthusiast
you answer in the same language as the input
You always mention that all the sources are at the section below
Your answer should have a BIG headline 
Your answer is markdown formatted and may have emojis
Your answer use bold text for the most important parts 
You always output a complete answer within less than 1000 characters 
"""

def notify (message):

    validNotification = evaluate_notification(message)
    # Function to send notifications via webhook

    if webhook_url:
        payload = {
            "text": validNotification,
        }
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"✅Notification sent: {validNotification}")
        except requests.RequestException as e:
            print(f"Failed to send notification: {e}")
    else:
        print("No webhook URL configured for notifications.")

# Function to evaluate text that will be sent to webhook
def evaluate_notification(text):
    try:
        response = model.generate_content(
            f""" Evaluate the text bellow and IF it is greater than 140 characters, summarize it,
              your final answer is ONLY the original text if it is small enought OR a small summary you created. Go ahead, analyze this text:\n\n
            
            {text}\n\n
            
            Remember, you can only answer with a text smaller than 140 characters. NOTHING ELSE.
            \n\nYour final answer is:"""
        )
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        notify(str(e))
        return "Could not evaluate notification text."
    

def evaluate_opinion(opinion):
    try:
        response = model.generate_content(
            f""" Evaluate this opinion and answer 0 if this is not a valid opinion or 1 if this is indeed a valid opinion:\n\n
            
            {opinion}\n\n
            
            
            A valid opinion must talk about tech news.
            An invalid opinion is one asking for more information or complaining about apis missing or errors.
            
            Remember, you can only answer with a single number, either 0 for false or 1 for true. NOTHING ELSE.
            \n\nYour final answer is (0 or 1):"""
        )
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        notify(str(e))
        return str(e)

# Function to interact with the Gemini model
def tailor_opinion(news):
    try:
        response = model.generate_content(
            f"{personality}\nThese are the news you must tailor an intelligent opinion for today:\n{news}\n\nYour opinion:"
        )
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        notify(str(e))
        return str(e)

# Function to fetch technology news from GNews API
def fetch_tech_news():
    print("\n📰 Fetching Latest Tech Headlines... \n" + "-"*30)
    try:
        api_key = os.getenv("GNEWS_API_KEY")
        url = f"https://gnews.io/api/v4/search?q=technology&lang=en&topic=technology&max=5&token={api_key}"
        response = requests.get(url)
        news_data = response.json()

        news_lines = []
        display_lines = []

        for idx, article in enumerate(news_data.get("articles", []), start=1):
            line = f"{idx}. {article['title']} ({article['source']['name']})\n   {article['url']}"
            news_lines.append(line)
            display_lines.append(line)

        return "\n".join(news_lines), "\n".join(display_lines)

    except Exception as e:
        print("Failed to fetch news:", e)
        notify(str(e))
        return "", ""

# Main routine
if __name__ == "__main__":
    news, sources = fetch_tech_news()
    opinion = tailor_opinion(news)
    opinionValidity = evaluate_opinion(opinion)
    today = datetime.now().strftime("%Y-%m-%d")

    if opinionValidity == "0":
        print("\n❌ Invalid opinion generated. Exiting.")
        notify(f"❌ Invalid opinion generated. News not published for {today}.")
        exit(1)
    elif opinionValidity == "1":
        headline = f"What happens in tech today ({today}):"

        support_button = "[![Support my work ❤️](https://img.shields.io/badge/Support%20my%20work%20❤️-orange?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/c/orobocigano)"

        final_news = f"{support_button}\n\n{headline}\n\n{opinion}\n\nSources:\n{sources}"

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(final_news)

        print("\n✅ Output saved to README.md\n")
        # print(final_news)

        # Git commit and push
        try:
            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(["git", "commit", "-m", f"Update tech news for {today}"], check=True)
            subprocess.run(["git", "push", "origin", "--force"], check=True)
            print("✅ Changes committed and pushed to origin.")
            notify("✅ News Published for {today}.")

        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            notify(str(e))
