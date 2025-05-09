import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from datetime import datetime

# Load API keys from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load model
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-pro"))

# Persona
personality = """
You are in a roleplay with the following STRICT rules:
your name is "Sofia"
you are a tech journalist and enthusiast
you answer in the same language as the input
You always mention that all the sources are at the section below
You always output a complete answer within less than 1000 characters 
"""

# Function to interact with the Gemini model
def tailor_opinion(news):
    try:
        response = model.generate_content(
            f"{personality}\nThese are the news you must tailor an intelligent opinion for today:\n{news}\n\nYour opinion:"
        )
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return str(e)

# Function to fetch technology news from GNews API
def fetch_tech_news():
    print("\n📰 Latest Tech Headlines:\n" + "-"*30)
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
        return "", ""

# Main routine
if __name__ == "__main__":
    news, sources = fetch_tech_news()
    opinion = tailor_opinion(news)
    today = datetime.now().strftime("%Y-%m-%d")
    headline = f"What happens in tech today ({today}):"

    final_news = f"{headline}\n\n{opinion}\n\nSources:\n{sources}"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(final_news)

    print("\n✅ Output saved to README.md\n")
    print(final_news)
