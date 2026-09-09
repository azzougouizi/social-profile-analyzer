import os
import re
import requests

from bs4 import BeautifulSoup
from flask import Flask, request
from datetime import datetime
from zoneinfo import ZoneInfo


app = Flask(__name__)

# =========================
# إعدادات البوت
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"


# =========================
# مواقع المعلومات
# =========================

FIXTURES_URL = (
    "https://www.premierleague.com/en/news/"
    "4675097/all-380-fixtures-for-202627-premier-league-season"
)

STATS_URL = "https://www.premierleague.com/en/stats"


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================
# أسماء الفرق
# =========================

TEAMS = {
    "Arsenal": "أرسنال",
    "AFC Bournemouth": "بورنموث",
    "Aston Villa": "أستون فيلا",
    "Brentford": "برينتفورد",
    "Brighton & Hove Albion": "برايتون",
    "Burnley": "بيرنلي",
    "Chelsea": "تشيلسي",
    "Crystal Palace": "كريستال بالاس",
    "Coventry City": "كوفنتري سيتي",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Hull City": "هال سيتي",
    "Ipswich Town": "إيبسويتش",
    "Leeds United": "ليدز",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Newcastle United": "نيوكاسل",
    "Nottingham Forest": "نوتنغهام فورست",
    "Sunderland": "سندرلاند",
    "Tottenham Hotspur": "توتنهام",
}


# =========================
# Telegram
# =========================

def send_message(chat_id, text):

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=15
    )


# =========================
# القائمة الرئيسية
# =========================

def main_menu(chat_id):

    keyboard = {
        "keyboard": [
            ["⚽ مباريات اليوم"],
            ["🥇 ترتيب الهدافين"],
            ["🏆 أفضل لاعب"]
        ],
        "resize_keyboard": True
    }

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "اختر الخدمة:",
            "reply_markup": keyboard
        },
        timeout=15
    )


# =========================
# جلب صفحة
# =========================

def get_page(url):

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()

    return BeautifulSoup(
        r.text,
        "html.parser"
    ).get_text(" ", strip=True)


# =========================
# مباريات اليوم
# =========================

def get_today_matches():

    text = get_page(FIXTURES_URL)

    now = datetime.now(
        ZoneInfo("Europe/London")
    )

    date_text = now.strftime(
        "%-d %B %Y"
    )

    position = text.find(date_text)

    if position == -1:
        return []

    section = text[position:]

    teams = list(TEAMS.keys())

    matches = []

    for home in teams:

        for away in teams:

            if home == away:
                continue

            pattern = (
                re.escape(home)
                + r"\s+v\s+"
                + re.escape(away)
            )

            if re.search(pattern, section):

                match = {
                    "home": home,
                    "away": away
                }

                if match not in matches:
                    matches.append(match)

    return matches


# =========================
# عرض مباريات اليوم
# =========================

def show_matches():

    try:
        matches = get_today_matches()

    except Exception as e:

        print("Fixture error:", e)

        return (
            "❌ تعذر جلب مباريات اليوم.\n"
            "حاول مرة أخرى."
        )

    if not matches:

        return (
            "⚽ لا توجد مباريات للدوري الإنجليزي "
            "اليوم حسب المصدر."
        )

    text = "⚽ مباريات الدوري الإنجليزي اليوم\n\n"

    for match in matches:

        home = TEAMS.get(
            match["home"],
            match["home"]
        )

        away = TEAMS.get(
            match["away"],
            match["away"]
        )

        text += (
            f"🏟 {home} 🆚 {away}\n\n"
        )

    return text


# =========================
# إحصائيات اللاعبين
# =========================

def get_stats_page():

    try:

        return get_page(STATS_URL)

    except Exception as e:

        print("Stats error:", e)

        return ""


# =========================
# الهدافون
# =========================

def show_top_scorers():

    stats = get_stats_page()

    if not stats:

        return (
            "❌ لم أستطع جلب ترتيب الهدافين."
        )

    return (
        "🥇 ترتيب هدافي الدوري الإنجليزي\n\n"
        "ملاحظة:\n"
        "صفحة الإحصائيات الرسمية تستخدم بيانات "
        "ديناميكية، لذلك إذا لم تظهر الأرقام في "
        "الصفحة العامة فلن يخترع البوت أرقامًا.\n\n"
        "يمكنك فتح إحصائيات Premier League "
        "للاطلاع على الترتيب الحالي."
    )


# =========================
# أفضل لاعب
# =========================

def show_best_player():

    stats = get_stats_page()

    if not stats:

        return (
            "❌ لم أستطع جلب بيانات اللاعبين."
        )

    return (
        "🏆 أفضل لاعب\n\n"
        "يتم تحديد الأفضل من إحصائيات اللاعبين "
        "المتاحة في المصدر الرسمي.\n\n"
        "لن يعرض البوت لاعبًا أو رقمًا غير موجود "
        "في المصدر."
    )


# =========================
# Webhook
# =========================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    message = data.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get("id")

    if not chat_id:
        return "OK"

    text = message.get(
        "text",
        ""
    ).strip()

    # البداية
    if text == "/start":

        send_message(
            chat_id,
            "👋 أهلاً بك في بوت الدوري الإنجليزي.\n\n"
            "أرسل رمز الدخول 1230."
        )

        return "OK"

    # الدخول
    if text == ACCESS_CODE:

        main_menu(chat_id)

        return "OK"

    # المباريات
    if text == "⚽ مباريات اليوم":

        send_message(
            chat_id,
            show_matches()
        )

        return "OK"

    # الهدافون
    if text == "🥇 ترتيب الهدافين":

        send_message(
            chat_id,
            show_top_scorers()
        )

        return "OK"

    # أفضل لاعب
    if text == "🏆 أفضل لاعب":

        send_message(
            chat_id,
            show_best_player()
        )

        return "OK"

    # أي رسالة أخرى
    send_message(
        chat_id,
        "اختر من القائمة الموجودة أسفل الشاشة."
    )

    return "OK"


# =========================
# Render
# =========================

@app.route("/")
def home():

    return "Premier League Bot is running"


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
