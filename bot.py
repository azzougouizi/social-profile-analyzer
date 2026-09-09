import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

# -----------------------------------------
# أسماء الفرق بالعربية
# -----------------------------------------

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

# -----------------------------------------
# إرسال رسالة
# -----------------------------------------

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=15
        )
    except Exception:
        pass


# -----------------------------------------
# القائمة
# -----------------------------------------

def main_menu(chat_id):

    keyboard = {
        "keyboard": [
            ["⚽ مباريات اليوم"],
            ["🥇 ترتيب الهدافين"],
            ["🏆 أفضل لاعب"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"{TELEGRAM}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "اختر الخدمة:",
                "reply_markup": keyboard
            },
            timeout=15
        )
    except Exception:
        pass


# -----------------------------------------
# تحميل صفحة
# -----------------------------------------

def get_page(url):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        return response.text

    except Exception:
        return None


# -----------------------------------------
# تحويل اسم الفريق
# -----------------------------------------

def arabic_team(name):

    name = name.strip()

    return TEAMS.get(name, name)


# -----------------------------------------
# مباريات الدوري الإنجليزي
# -----------------------------------------

def get_fixtures():

    url = (
        "https://www.tntsports.co.uk/football/"
        "premier-league/2026-2027/calendar-results.shtml"
    )

    html = get_page(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    # نبحث عن مباريات تحتوي على أسماء فرق معروفة
    pattern = re.compile(
        r"(Arsenal|AFC Bournemouth|Aston Villa|Brentford|"
        r"Brighton & Hove Albion|Burnley|Chelsea|Crystal Palace|"
        r"Coventry City|Everton|Fulham|Hull City|Ipswich Town|"
        r"Leeds United|Liverpool|Manchester City|Manchester United|"
        r"Newcastle United|Nottingham Forest|Sunderland|"
        r"Tottenham Hotspur)"
        r"\s+"
        r"(?:\d{1,2}:\d{2}|\d+)"
        r"\s+"
        r"(Arsenal|AFC Bournemouth|Aston Villa|Brentford|"
        r"Brighton & Hove Albion|Burnley|Chelsea|Crystal Palace|"
        r"Coventry City|Everton|Fulham|Hull City|Ipswich Town|"
        r"Leeds United|Liverpool|Manchester City|Manchester United|"
        r"Newcastle United|Nottingham Forest|Sunderland|"
        r"Tottenham Hotspur)",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    return matches


# -----------------------------------------
# مباريات اليوم
# -----------------------------------------

def show_matches():

    today = datetime.now(
        ZoneInfo("Europe/London")
    ).strftime("%d/%m/%Y")

    url = (
        "https://www.tntsports.co.uk/football/"
        "premier-league/2026-2027/calendar-results.shtml"
    )

    html = get_page(url)

    if not html:
        return (
            "❌ لم أستطع الوصول إلى موقع المباريات الآن.\n"
            "حاول مرة أخرى بعد قليل."
        )

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n", strip=True)

    # البحث عن تاريخ اليوم
    date_variants = [
        datetime.now(
            ZoneInfo("Europe/London")
        ).strftime("%d/%m/%Y"),

        datetime.now(
            ZoneInfo("Europe/London")
        ).strftime("%-d/%m/%Y"),
    ]

    found_date = None

    for d in date_variants:
        if d in text:
            found_date = d
            break

    if not found_date:

        return (
            "⚽ مباريات الدوري الإنجليزي اليوم\n\n"
            "لا توجد مباريات Premier League اليوم."
        )

    # تقسيم الصفحة حول تاريخ اليوم
    part = text.split(found_date, 1)[1]

    # إذا كان هناك تاريخ اليوم التالي نوقف عنده
    date_match = re.search(
        r"\d{2}/\d{2}/\d{4}",
        part
    )

    if date_match:
        part = part[:date_match.start()]

    teams = list(TEAMS.keys())

    games = []

    lines = [
        x.strip()
        for x in part.splitlines()
        if x.strip()
    ]

    for i in range(len(lines) - 2):

        home = lines[i]
        middle = lines[i + 1]
        away = lines[i + 2]

        if home in teams and away in teams:

            if (
                re.match(r"^\d{1,2}:\d{2}$", middle)
                or re.match(r"^\d+$", middle)
                or middle == "Finished"
            ):

                games.append(
                    (
                        arabic_team(home),
                        middle,
                        arabic_team(away)
                    )
                )

    # إزالة التكرار
    unique_games = []

    for game in games:
        if game not in unique_games:
            unique_games.append(game)

    if not unique_games:

        return (
            "⚽ مباريات الدوري الإنجليزي اليوم\n\n"
            "لا توجد مباريات اليوم."
        )

    result = "⚽ مباريات الدوري الإنجليزي اليوم\n\n"

    for home, time, away in unique_games:

        result += (
            f"🏟 {home}\n"
            f"🆚 {away}\n"
            f"⏰ {time}\n\n"
        )

    return result


# -----------------------------------------
# الهدافون
# -----------------------------------------

def get_top_scorers():

    url = (
        "https://www.premierleague.com/en/"
        "stats/top/players/goals/2026-27"
    )

    html = get_page(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    players = []

    # أسماء معروفة + عدد الأهداف
    known_players = [
        "Erling Haaland",
        "Bruno Fernandes",
        "Alexander Isak",
        "Kai Havertz",
        "Cole Palmer",
        "Rayan Cherki",
        "João Pedro",
        "Anthony Elanga",
        "Jack Hinshelwood",
        "Morgan Rogers",
        "Martin Ødegaard",
        "Bukayo Saka",
        "Bryan Mbeumo",
    ]

    for player in known_players:

        position = text.find(player)

        if position == -1:
            continue

        nearby = text[position:position + 100]

        numbers = re.findall(
            r"\b[1-9]\b",
            nearby
        )

        if numbers:

            goals = int(numbers[-1])

            players.append(
                (player, goals)
            )

    players.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return players


# -----------------------------------------
# مصدر بديل للهدافين
# -----------------------------------------

def get_top_scorers_backup():

    url = (
        "https://www.tntsports.co.uk/football/"
        "premier-league/2026-2027/"
    )

    html = get_page(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    names = [
        "Bruno Fernandes",
        "Erling Haaland",
        "Alexander Isak",
        "Josh Sargent",
        "Kai Havertz",
        "Cole Palmer",
        "Rayan Cherki",
        "João Pedro",
        "Anthony Elanga",
        "Jack Hinshelwood"
    ]

    result = []

    for name in names:

        if name in text:
            result.append(name)

    return result


# -----------------------------------------
# عرض الهدافين
# -----------------------------------------

def show_top_scorers():

    players = get_top_scorers()

    if not players:

        # مصدر احتياطي
        backup = get_top_scorers_backup()

        if backup:

            message = (
                "🥇 ترتيب الهدافين\n\n"
                "البيانات الحالية من موقع كرة القدم:\n\n"
            )

            for i, name in enumerate(
                backup[:10],
                1
            ):
                message += (
                    f"{i}. {name}\n"
                )

            return message

        return (
            "❌ تعذر جلب بيانات الهدافين الآن.\n\n"
            "حاول مرة أخرى بعد قليل."
        )

    message = (
        "🥇 هدافو الدوري الإنجليزي 2026/27\n\n"
    )

    for i, (player, goals) in enumerate(
        players[:10],
        1
    ):

        message += (
            f"{i}. {player} — {goals} أهداف\n"
        )

    return message


# -----------------------------------------
# أفضل لاعب
# -----------------------------------------

def show_best_player():

    players = get_top_scorers()

    if not players:

        return (
            "❌ لا أستطيع جلب بيانات اللاعبين الآن.\n\n"
            "حاول مرة أخرى بعد قليل."
        )

    # في النسخة البسيطة:
    # اللاعب صاحب أكبر عدد من الأهداف
    # يعتبر أفضل لاعب هجومي إحصائياً.

    best_player, goals = players[0]

    return (
        "🏆 أفضل لاعب حاليًا\n\n"
        f"⭐ {best_player}\n"
        f"⚽ الأهداف: {goals}\n\n"
        "📊 الاختيار مبني على أفضل سجل تهديفي "
        "حالي في الدوري."
    )


# -----------------------------------------
# Webhook
# -----------------------------------------

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
            "🔐 أرسل رمز الدخول 1230."
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

    send_message(
        chat_id,
        "اختر خدمة من القائمة الموجودة أسفل الشاشة."
    )

    return "OK"


# -----------------------------------------
# Health check
# -----------------------------------------

@app.route("/")
def home():

    return "Premier League Bot is running"


# -----------------------------------------
# تشغيل Flask
# -----------------------------------------

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
