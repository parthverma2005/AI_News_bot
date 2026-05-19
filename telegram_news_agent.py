
from dotenv import load_dotenv
import os
import time
import requests
from datetime import datetime
from groq import Groq
load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")     # from aistudio.google.com
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")  # from @BotFather
TELEGRAM_CHAT_ID = TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")            # from getUpdates URL
MAX_STORIES = 4
REPEAT = False
INTERVAL_HOURS = 6


# Gemini Client
client = Groq(api_key=GROQ_API_KEY)
# ──────────────────────────────────────────────
#  TELEGRAM SENDER
# ──────────────────────────────────────────────
def send_telegram(text: str) -> bool:

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    for chunk in chunks:

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()

            if not data.get("ok"):
                print(f"❌ Telegram error: {data}")
                return False

        except Exception as e:
            print(f"❌ Telegram send failed: {e}")
            return False

        time.sleep(0.5)

    return True


# ──────────────────────────────────────────────
#  GEMINI NEWS FETCHER
# ──────────────────────────────────────────────
def fetch_news_groq() -> str:

    current_date = datetime.now().strftime("%B %d, %Y")

    prompt = f"""
Today is {current_date}.

Give me the {MAX_STORIES} latest breaking AI news stories happening RIGHT NOW.

For each story use this exact format:

---
HEADLINE:
SUMMARY:
WHY IT MATTERS:
WHERE:

Focus ONLY on:
- AI
- OpenAI
- Google Gemini
- Anthropic
- NVIDIA
- Robotics
- AI startups
- Machine learning
- AGI
"""

    print(f"🔍 Fetching AI news via Groq... ({current_date})")

    try:

        response = client.chat.completions.create(
         model="llama-3.3-70b-versatile",
         messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
        temperature=0.7,
        max_tokens=2000
)

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return None

# ──────────────────────────────────────────────
#  FORMAT FOR TELEGRAM
# ──────────────────────────────────────────────
def format_message(raw: str) -> str:

    now = datetime.now().strftime("%A, %B %d %Y — %H:%M")

    header = (
        f"🌍 <b>WORLD NEWS DIGEST</b>\n"
        f"📅 {now}\n"
        f"{'─' * 30}\n\n"
    )

    stories = [s.strip() for s in raw.split("---") if s.strip()]
    formatted = []

    emoji_map = {
        "war": "⚔️",
        "conflict": "⚔️",
        "attack": "💥",
        "strike": "💥",
        "economy": "📈",
        "market": "📊",
        "trade": "💱",
        "inflation": "📉",
        "climate": "🌿",
        "environment": "🌱",
        "flood": "🌊",
        "earthquake": "🌍",
        "tech": "💻",
        "ai": "🤖",
        "space": "🚀",
        "science": "🔬",
        "election": "🗳️",
        "president": "🏛️",
        "government": "🏛️",
        "minister": "🏛️",
        "health": "🏥",
        "virus": "🦠",
        "disease": "🦠",
        "death": "🕊️",
        "killed": "🕊️",
        "disaster": "🚨",
    }

    for i, story in enumerate(stories, 1):

        if not story:
            continue

        lines = story.strip().split("\n")

        headline = ""
        summary = ""
        why = ""
        where = ""

        for line in lines:

            line = line.strip()

            if line.upper().startswith("HEADLINE:"):
                headline = line.split(":", 1)[1].strip()

            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()

            elif line.upper().startswith("WHY IT MATTERS:"):
                why = line.split(":", 1)[1].strip()

            elif line.upper().startswith("WHERE:"):
                where = line.split(":", 1)[1].strip()

        if not headline:
            continue

        emoji = "📰"

        combined = (headline + " " + summary).lower()

        for keyword, e in emoji_map.items():

            if keyword in combined:
                emoji = e
                break

        formatted.append(
            f"{emoji} <b>{i}. {headline}</b>\n"
            f"📍 {where}\n"
            f"{summary}\n"
            f"<i>💡 {why}</i>\n"
        )

    body = "\n".join(formatted) if formatted else raw

    footer = (
        f"\n{'─' * 30}\n"
        f"🤖 <i>Powered by Groq AI</i>"
    )

    return header + body + footer


# ──────────────────────────────────────────────
#  VALIDATE CONFIG
# ──────────────────────────────────────────────
def validate():

    errors = []

    if GROQ_API_KEY == "YOUR_GROQ_API_KEY":
        errors.append("❌ GROQ_API_KEY not set")

    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        errors.append("❌ TELEGRAM_TOKEN not set")

    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID":
        errors.append("❌ TELEGRAM_CHAT_ID not set")

    if errors:

        print("\n🔧 Please fill in your credentials:\n")

        for e in errors:
            print(f"  {e}")

        return False

    return True


# ──────────────────────────────────────────────
#  MAIN JOB
# ──────────────────────────────────────────────
def run_news_job():

    print(f"\n{'='*45}")
    print(f"🚀 Running News Agent — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*45}")

    raw = fetch_news_groq()

    if not raw:

        send_telegram(
            "⚠️ <b>News Agent Error</b>\nCould not fetch news. Will retry later."
        )

        return

    print("✅ News fetched! Formatting...")

    message = format_message(raw)

    print("📤 Sending to Telegram...")

    if send_telegram(message):
        print("✅ Digest sent to Telegram successfully!")

    else:
        print("❌ Failed to send to Telegram.")


# ──────────────────────────────────────────────
#  RUN
# ──────────────────────────────────────────────
if validate():

    # Send once immediately
    run_news_job()

    # Optional loop
    if REPEAT:

        print(
            f"\n⏳ Next update in {INTERVAL_HOURS} hours. Keep this tab open!"
        )

        while True:

            time.sleep(INTERVAL_HOURS * 60 * 60)

            run_news_job()