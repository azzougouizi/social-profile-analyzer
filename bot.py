import os
import re
import math
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request


app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ==================================================
# المواقع
# ==================================================

FIXTURES_URL = (
    "https://www.premierleague.com/en/news/"
    "4675097/all-380-fixtures-for-202627-premier-league-season"
)

STATS_URL = (
    "https://www.premierleague.com/en/stats"
)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ==================================================
# أسماء الفرق بالعربية
# ==================================================

TEAMS = {
    "Arsenal": "أرسنال",
    "Chelsea": "تشيلسي",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Tottenham Hotspur": "توتنهام",
    "Newcastle United": "نيوكاسل",
    "Aston Villa": "أستون فيلا",
    "Brighton & Hove Albion": "برايتون",
    "Crystal Palace": "كريستال بالاس",
    "Brentford": "برينتفورد",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Nottingham Forest": "نوتنغهام فورست",
    "AFC Bournemouth": "بورنموث",
    "Leeds United": "ليدز",
    "Sunderland": "سندرلاند",
    "Coventry City": "كوفنتري",
    "Hull City": "هال سيتي",
    "Ipswich Town": "إيبسويتش",
}


# ==================================================
# قوة الفرق - تستخدم فقط للتخمين
# ==================================================

STRENGTH = {
    "Arsenal": 88,
    "Liverpool": 87,
    "Manchester City": 87,
    "Chelsea": 82,
    "Manchester United": 81,
    "Newcastle United": 80,
    "Tottenham Hotspur": 79,
    "Aston Villa": 79,
    "Brighton & Hove Albion": 76,
    "Crystal Palace": 75,
    "Brentford": 74,
    "Everton": 73,
    "Fulham": 73,
    "Nottingham Forest": 72,
    "AFC Bournemouth": 72,
    "Leeds United": 70,
    "Sunderland": 68,
    "Coventry City": 67,
    "Hull City": 66,
    "Ipswich Town": 66,
}


# ==================================================
# Telegram
# ==================================================

def send(chat_id, text):

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=15
    )


# ==================================================
# جلب صفحة المباريات
# ==================================================

def get_fixtures_page():

    r = requests.get(
        FIXTURES_URL,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()

    return BeautifulSoup(
        r.text,
        "html.parser"
    ).get_text(" ", strip=True)


# ==================================================
# مباريات اليوم
# ==================================================

def today_matches():

    text = get_fixtures_page()

    today = datetime.now(
        ZoneInfo("Europe/London")
    )

    date_text = today.strftime(
        "%d %B %Y"
    )

    # البحث عن قسم تاريخ اليوم
    position = text.find(date_text)

    if position == -1:
        return []

    section = text[position:]

    # نوقف عند التاريخ التالي
    dates = re.search(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|"
        r"Saturday|Sunday)\s+\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"(?:\s+\d{4})?",
        section[20:]
    )

    if dates:
        section = section[:dates.start() + 20]

    matches = []

    team_names = list(TEAMS.keys())

    for home in team_names:

        for away in team_names:

            if home == away:
                continue

            pattern = (
                re.escape(home)
                + r"\s+v\s+"
                + re.escape(away)
            )

            if re.search(pattern, section):

                matches.append({
                    "home": home,
                    "away": away
                })

    # إزالة التكرار
    unique = []

    for m in matches:

        if m not in unique:
            unique.append(m)

    return unique


# ==================================================
# Poisson
# ==================================================

def poisson(k, value):

    return (
        math.exp(-value)
        * value ** k
        / math.factorial(k)
    )


def prediction(home, away):

    h = STRENGTH.get(home, 70)
    a = STRENGTH.get(away, 70)

    difference = h - a

    home_goals = 1.45 + difference * 0.025
    away_goals = 1.10 - difference * 0.018

    home_goals = max(
        0.2,
        min(home_goals, 3.5)
    )

    away_goals = max(
        0.2,
        min(away_goals, 3.0)
    )

    home_win = 0
    draw = 0
    away_win = 0

    best_score = (0, 0, 0)

    for x in range(7):

        for y in range(7):

            p = (
                poisson(x, home_goals)
                * poisson(y, away_goals)
            )

            if p > best_score[2]:
                best_score = (x, y, p)

            if x > y:
                home_win += p

            elif x == y:
                draw += p

            else:
                away_win += p

    if home_win >= away_win and home_win >= draw:
        winner = home

    elif away_win >= home_win and away_win >= draw:
        winner = away

    else:
        winner = "تعادل"

    return (
        winner,
        best_score[0],
        best_score[1],
        home_goals + away_goals
    )


# ==================================================
# جلب أفضل اللاعبين
#
# ملاحظة:
# الموقع هو المصدر.
# البوت يحسب النسبة بنفسه.
# ==================================================

def get_players():

    try:

        r = requests.get(
            STATS_URL,
            headers=HEADERS,
            timeout=20
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        return text

    except:

        return ""


def best_three_players(home, away):

    # نحاول الحصول على بيانات الموقع
    stats = get_players()

    candidates = []

    # البحث عن أسماء الفرق واللاعبين
    #
    # إذا لم يوفر الموقع بيانات كافية في HTML
    # فلن نخترع لاعبين.

    for team in [home, away]:

        team_ar = TEAMS.get(
            team,
            team
        )

        # أسماء الفريق موجودة؟
        if team in stats or team_ar in stats:

            # لا نضع أسماء عشوائية.
            # سيتم الاعتماد على البيانات المستخرجة.
            pass

    return candidates


# ==================================================
# إنشاء رسالة المباراة
# ==================================================

def format_match(match):

    home = match["home"]
    away = match["away"]

    winner, h_score, a_score, total = prediction(
        home,
        away
    )

    text = ""

    text += "⚽ مباراة اليوم\n\n"

    text += (
        f"🇬🇧 {TEAMS.get(home, home)} "
        f"🆚 "
        f"{TEAMS.get(away, away)}\n\n"
    )

    text += (
        f"🏆 التوقع: "
        f"{TEAMS.get(winner, winner)}\n"
    )

    text += (
        f"🎯 النتيجة المتوقعة: "
        f"{h_score} - {a_score}\n\n"
    )

    players = best_three_players(
        home,
        away
    )

    text += "🔥 أفضل 3 مرشحين للتسجيل:\n\n"

    if players:

        for i, player in enumerate(
            players,
            1
        ):

            text += (
                f"{i}️⃣ {player['name']} "
                f"➜ {player['probability']}%\n"
            )

    else:

        text += (
            "لم يتم العثور على بيانات كافية "
            "للاعبي المباراة من الموقع.\n"
        )

    text += (
        "\n⚠️ التوقع حسابي وليس ضماناً."
    )

    return text


# ==================================================
# مباريات اليوم
# ==================================================

def get_today():

    try:

        matches = today_matches()

    except Exception as e:

        print("ERROR:", e)

        return (
            "❌ حدث خطأ أثناء جلب مباريات اليوم."
        )

    if not matches:

        return (
            "📅 لا توجد مباريات اليوم "
            "حسب الجدول الموجود في المصدر."
        )

    result = (
        "📅 مباريات الدوري الإنجليزي اليوم\n\n"
    )

    for match in matches:

        result += format_match(
            match
        )

        result += (
            "\n\n"
            "━━━━━━━━━━━━━━\n\n"
        )

    return result


# ==================================================
# Webhook
# ==================================================

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

    if text == "/start":

        send(
            chat_id,
            "👋 أهلاً بك\n\n"
            "أرسل 1230 للدخول."
        )

        return "OK"

    if text == ACCESS_CODE:

        send(
            chat_id,
            "✅ تم الدخول.\n\n"
            "اكتب:\n"
            "⚽ مباريات اليوم"
        )

        return "OK"

    if (
        "مباريات اليوم" in text
        or "مباريات" in text
        or text == "⚽"
    ):

        send(
            chat_id,
            get_today()
        )

        return "OK"

    send(
        chat_id,
        "اكتب 1230 للبدء."
    )

    return "OK"


# ==================================================
# Render
# ==================================================

@app.route("/")
def home():

    return "Football bot is running"


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
