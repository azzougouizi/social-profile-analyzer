import os
import re
import math
import requests

from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request

app = Flask(__name__)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

PREMIER_LEAGUE_URL = (
    "https://www.premierleague.com/en/news/"
    "4675097/all-380-fixtures-for-202627-premier-league-season"
)

# =========================
# TEAM NAMES
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
    "Coventry City": "كوفنتري",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Leeds United": "ليدز",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Newcastle United": "نيوكاسل",
    "Nottingham Forest": "نوتنغهام فورست",
    "Sunderland": "سندرلاند",
    "Tottenham Hotspur": "توتنهام",
    "Hull City": "هال سيتي",
    "Ipswich Town": "إيبسويتش",
}

# =========================
# SIMPLE TEAM STRENGTH
# =========================
# أرقام أساسية للنموذج.
# يمكن تعديلها لاحقاً حسب نتائج الموسم.

TEAM_STRENGTH = {
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

# =========================
# TELEGRAM
# =========================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=15,
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# GET PREMIER LEAGUE PAGE
# =========================

def get_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
    }

    r = requests.get(
        PREMIER_LEAGUE_URL,
        headers=headers,
        timeout=20,
    )

    r.raise_for_status()

    return r.text


# =========================
# EXTRACT FIXTURES
# =========================

def get_today_fixtures():

    html = get_page()

    # إزالة HTML
    text = re.sub(r"<[^>]+>", " ", html)

    text = re.sub(r"\s+", " ", text)

    today_uk = datetime.now(
        ZoneInfo("Europe/London")
    ).date()

    date_pattern = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
        r"\s+(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+(\d{4})"
    )

    month_numbers = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }

    matches = []

    date_matches = list(date_pattern.finditer(text))

    for i, dm in enumerate(date_matches):

        day = int(dm.group(2))
        month = month_numbers[dm.group(3)]
        year = int(dm.group(4))

        current_date = datetime(
            year,
            month,
            day,
            tzinfo=ZoneInfo("Europe/London")
        ).date()

        if current_date != today_uk:
            continue

        start = dm.end()

        if i + 1 < len(date_matches):
            end = date_matches[i + 1].start()
        else:
            end = min(start + 5000, len(text))

        block = text[start:end]

        for team1 in TEAMS:

            pattern = re.escape(team1) + r"\s+v\s+"

            found = re.finditer(pattern, block)

            for f in found:

                remaining = block[f.end():]

                possible_teams = []

                for team2 in TEAMS:

                    if team2 == team1:
                        continue

                    pos = remaining.find(team2)

                    if pos != -1:
                        possible_teams.append(
                            (pos, team2)
                        )

                if not possible_teams:
                    continue

                _, team2 = min(
                    possible_teams,
                    key=lambda x: x[0]
                )

                before = block[
                    max(0, f.start() - 10):
                    f.start()
                ]

                time_match = re.search(
                    r"(\d{1,2}):(\d{2})\s*$",
                    before
                )

                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                else:
                    # الوقت الافتراضي للمباريات التي لا يظهر وقتها
                    hour = 15
                    minute = 0

                fixture = {
                    "home": team1,
                    "away": team2,
                    "hour": hour,
                    "minute": minute,
                    "date": current_date,
                }

                duplicate = False

                for old in matches:
                    if (
                        old["home"] == fixture["home"]
                        and old["away"] == fixture["away"]
                    ):
                        duplicate = True
                        break

                if not duplicate:
                    matches.append(fixture)

    return matches


# =========================
# POISSON
# =========================

def poisson(k, lam):

    if lam <= 0:
        return 0

    return (
        math.exp(-lam)
        * pow(lam, k)
        / math.factorial(k)
    )


def match_prediction(home, away):

    home_strength = TEAM_STRENGTH.get(home, 70)
    away_strength = TEAM_STRENGTH.get(away, 70)

    difference = home_strength - away_strength

    # أهداف متوقعة
    home_xg = 1.35 + difference * 0.025
    away_xg = 1.10 - difference * 0.018

    # أفضلية الأرض
    home_xg += 0.12

    home_xg = max(0.25, min(home_xg, 3.5))
    away_xg = max(0.20, min(away_xg, 3.0))

    # احتمالات النتائج
    home_win = 0
    draw = 0
    away_win = 0

    score_probs = []

    for h in range(0, 7):
        for a in range(0, 7):

            p = poisson(h, home_xg) * poisson(a, away_xg)

            score_probs.append(
                (h, a, p)
            )

            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p

    total = home_win + draw + away_win

    home_win /= total
    draw /= total
    away_win /= total

    # النتيجة الأكثر احتمالاً
    best_score = max(
        score_probs,
        key=lambda x: x[2]
    )

    # الفائز
    if home_win >= draw and home_win >= away_win:
        winner = home
    elif away_win >= home_win and away_win >= draw:
        winner = away
    else:
        winner = "تعادل"

    return {
        "home_xg": home_xg,
        "away_xg": away_xg,
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "winner": winner,
        "score": (
            best_score[0],
            best_score[1]
        ),
    }


# =========================
# UNDER GOALS
# =========================

def probability_under(total_xg, line):

    # أقل من 0.5 = مجموع الأهداف 0 فقط
    if line == 0.5:
        return poisson(0, total_xg)

    # أقل من 1.0
    # في الخط الآسيوي:
    # 0 هدف = فوز كامل
    # 1 هدف = استرداد
    # لذلك نعرض احتمال <= 0
    if line == 1.0:
        return poisson(0, total_xg)

    # أقل من 1.5 = 0 أو 1
    if line == 1.5:
        return poisson(0, total_xg) + poisson(1, total_xg)

    # أقل من 2.0
    # 0 أو 1 فوز، و2 استرداد
    if line == 2.0:
        return (
            poisson(0, total_xg)
            + poisson(1, total_xg)
        )

    return 0


# =========================
# PLAYER DATA
# =========================
# بيانات يدوية أولية.
# لا ندعي أنها إصابات أو تشكيلات حية.
# يمكن استبدالها لاحقاً بمصدر إحصائيات رسمي.

TOP_SCORERS = {
    "Arsenal": [
        ("Bukayo Saka", 0.42),
        ("Kai Havertz", 0.36),
        ("Gabriel Martinelli", 0.31),
    ],

    "Liverpool": [
        ("Mohamed Salah", 0.48),
        ("Luis Diaz", 0.34),
        ("Cody Gakpo", 0.32),
    ],

    "Manchester City": [
        ("Erling Haaland", 0.55),
        ("Phil Foden", 0.36),
        ("Jeremy Doku", 0.29),
    ],

    "Chelsea": [
        ("Cole Palmer", 0.45),
        ("Nicolas Jackson", 0.34),
        ("Christopher Nkunku", 0.30),
    ],

    "Manchester United": [
        ("Bruno Fernandes", 0.38),
        ("Rasmus Hojlund", 0.34),
        ("Amad Diallo", 0.29),
    ],

    "Newcastle United": [
        ("Alexander Isak", 0.46),
        ("Anthony Gordon", 0.34),
        ("Harvey Barnes", 0.28),
    ],

    "Tottenham Hotspur": [
        ("Son Heung-min", 0.43),
        ("James Maddison", 0.32),
        ("Richarlison", 0.30),
    ],
}


def get_top_three_scorers(home, away):

    players = []

    for team in [home, away]:

        for player, probability in TOP_SCORERS.get(
            team,
            []
        ):
            players.append(
                (
                    player,
                    probability
                )
            )

    players.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return players[:3]


# =========================
# FORMAT MATCH
# =========================

def format_match(match):

    home = match["home"]
    away = match["away"]

    prediction = match_prediction(
        home,
        away
    )

    home_ar = TEAMS.get(
        home,
        home
    )

    away_ar = TEAMS.get(
        away,
        away
    )

    total_xg = (
        prediction["home_xg"]
        + prediction["away_xg"]
    )

    under05 = probability_under(
        total_xg,
        0.5
    )

    under10 = probability_under(
        total_xg,
        1.0
    )

    under15 = probability_under(
        total_xg,
        1.5
    )

    under20 = probability_under(
        total_xg,
        2.0
    )

    top_players = get_top_three_scorers(
        home,
        away
    )

    text = (
        "⚽ مباريات الدوري الإنجليزي\n\n"
        f"🏟 {home_ar} 🆚 {away_ar}\n"
        f"🕐 {match['hour']:02d}:{match['minute']:02d}\n\n"

        f"🏆 الفائز المتوقع: "
        f"{TEAMS.get(prediction['winner'], prediction['winner'])}\n"

        f"🎯 النتيجة المتوقعة: "
        f"{prediction['score'][0]} - "
        f"{prediction['score'][1]}\n\n"

        "📊 توقع مجموع الأهداف\n"
        f"🔹 أقل من 0.5 ➜ {under05 * 100:.1f}%\n"
        f"🔹 أقل من 1.0 ➜ {under10 * 100:.1f}%\n"
        f"🔹 أقل من 1.5 ➜ {under15 * 100:.1f}%\n"
        f"🔹 أقل من 2.0 ➜ {under20 * 100:.1f}%\n\n"

        "🔥 أفضل 3 لاعبين للتسجيل:\n"
    )

    if top_players:

        for i, (player, probability) in enumerate(
            top_players,
            1
        ):
            text += (
                f"{i}️⃣ {player} "
                f"➜ {probability * 100:.0f}%\n"
            )

    else:
        text += (
            "لا توجد بيانات لاعبين كافية لهذه المباراة.\n"
        )

    text += (
        "\n⚠️ هذه توقعات حسابية وليست نتيجة مضمونة."
    )

    return text


# =========================
# TODAY
# =========================

def today_matches_text():

    try:
        matches = get_today_fixtures()

    except Exception as e:

        print("Fixture error:", e)

        return (
            "❌ لم أستطع جلب مباريات اليوم.\n"
            "حاول مرة أخرى بعد قليل."
        )

    if not matches:

        return (
            "⚽ لا توجد مباريات للدوري الإنجليزي "
            "اليوم حسب الجدول المتاح."
        )

    output = (
        "📅 مباريات الدوري الإنجليزي اليوم\n\n"
    )

    for match in matches:

        output += format_match(match)
        output += "\n\n"
        output += "━━━━━━━━━━━━━━\n\n"

    return output


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route(
    "/telegram/webhook",
    methods=["POST", "GET"]
)
def telegram_webhook():

    if request.method == "GET":
        return "Telegram bot is running"

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

    text = (
        message.get("text", "")
        .strip()
    )

    # =====================
    # START
    # =====================

    if text == "/start":

        send_message(
            chat_id,
            "👋 أهلاً بك\n\n"
            "أرسل رمز الدخول للمتابعة."
        )

        return "OK"

    # =====================
    # ACCESS
    # =====================

    if text == ACCESS_CODE:

        send_message(
            chat_id,
            "✅ تم قبول رمز الدخول.\n\n"
            "اختر الخدمة:\n\n"
            "⚽ مباريات اليوم"
        )

        return "OK"

    # =====================
    # TODAY
    # =====================

    if (
        "مباريات" in text
        or "اليوم" in text
        or text == "⚽"
    ):

        result = today_matches_text()

        send_message(
            chat_id,
            result
        )

        return "OK"

    # =====================
    # DEFAULT
    # =====================

    send_message(
        chat_id,
        "اكتب:\n"
        "1230\n\n"
        "ثم اطلب مباريات اليوم."
    )

    return "OK"


# =========================
# HEALTH CHECK
# =========================

@app.route("/")
def home():

    return (
        "Football prediction bot is running."
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
