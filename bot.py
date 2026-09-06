import os
import re
import math
import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import telebot
from telebot import types


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ACCESS_CODE = "1230"

PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

app = Flask(__name__)

TIMEZONE = ZoneInfo("Africa/Algiers")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =========================================================
# 365SCORES LEAGUES
# =========================================================

LEAGUES = {

    "dz": {
        "name": "🇩🇿 الدوري الجزائري",
        "short": "الجزائري",
        "matches": (
            "https://www.365scores.com/"
            "football/league/ligue-1-560/matches"
        ),
        "standings": (
            "https://www.365scores.com/"
            "football/league/ligue-1-560/standings"
        ),
    },

    "eng": {
        "name": "🏴 الدوري الإنجليزي",
        "short": "الإنجليزي",
        "matches": (
            "https://www.365scores.com/"
            "football/league/premier-league-7/matches"
        ),
        "standings": (
            "https://www.365scores.com/"
            "football/league/premier-league-7/standings"
        ),
    },

    "fr": {
        "name": "🇫🇷 الدوري الفرنسي",
        "short": "الفرنسي",
        "matches": (
            "https://www.365scores.com/"
            "football/league/ligue-1-35/matches"
        ),
        "standings": (
            "https://www.365scores.com/"
            "football/league/ligue-1-35/standings"
        ),
    },
}


# =========================================================
# TEAM TRANSLATIONS
# =========================================================

TEAM_AR = {

    # -------------------------
    # ALGERIA
    # -------------------------

    "MC Alger": "مولودية الجزائر",
    "Mouloudia Club d'Alger": "مولودية الجزائر",

    "USM Alger": "اتحاد العاصمة",
    "Union Sportive de la Médina d'Alger": "اتحاد العاصمة",

    "CR Belouizdad": "شباب بلوزداد",

    "JS Kabylie": "شبيبة القبائل",

    "CS Constantine": "شباب قسنطينة",

    "ES Setif": "وفاق سطيف",
    "ES Sétif": "وفاق سطيف",

    "JS Saoura": "شبيبة الساورة",

    "MC Oran": "مولودية وهران",

    "ASO Chlef": "جمعية الشلف",

    "US Biskra": "اتحاد بسكرة",

    "USM Khenchela": "اتحاد خنشلة",

    "Olympique Akbou": "أولمبيك أقبو",

    "ES Ben Aknoun": "نجم بن عكنون",

    "MB Rouissat": "مولودية الرويسات",

    # -------------------------
    # ENGLAND
    # -------------------------

    "Arsenal": "أرسنال",
    "Chelsea": "تشيلسي",
    "Liverpool": "ليفربول",

    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",

    "Tottenham": "توتنهام",
    "Newcastle United": "نيوكاسل",
    "Newcastle": "نيوكاسل",

    "Aston Villa": "أستون فيلا",
    "Everton": "إيفرتون",
    "West Ham United": "وست هام",
    "West Ham": "وست هام",

    "Brighton": "برايتون",
    "Brighton & Hove Albion": "برايتون",

    "Fulham": "فولهام",
    "Crystal Palace": "كريستال بالاس",
    "Brentford": "برينتفورد",
    "Bournemouth": "بورنموث",

    "Wolverhampton Wanderers": "وولفرهامبتون",
    "Wolverhampton": "وولفرهامبتون",
    "Wolves": "وولفرهامبتون",

    "Nottingham Forest": "نوتنغهام فورست",
    "Leeds United": "ليدز يونايتد",
    "Sunderland": "سندرلاند",
    "Burnley": "بيرنلي",

    # -------------------------
    # FRANCE
    # -------------------------

    "Paris Saint-Germain": "باريس سان جيرمان",
    "Paris Saint Germain": "باريس سان جيرمان",
    "PSG": "باريس سان جيرمان",

    "Paris FC": "باريس إف سي",

    "AS Monaco": "موناكو",
    "Monaco": "موناكو",

    "Olympique Marseille": "مارسيليا",
    "Olympique de Marseille": "مارسيليا",
    "Marseille": "مارسيليا",

    "Olympique Lyonnais": "ليون",
    "Lyon": "ليون",

    "LOSC Lille": "ليل",
    "Lille": "ليل",

    "RC Lens": "لانس",
    "Lens": "لانس",

    "Stade Rennais": "رين",
    "Rennes": "رين",

    "Toulouse FC": "تولوز",
    "Toulouse": "تولوز",

    "Stade Brestois": "بريست",
    "Brest": "بريست",

    "Le Havre AC": "لوهافر",
    "Le Havre": "لوهافر",

    "Angers SCO": "أنجيه",
    "Angers": "أنجيه",

    "AJ Auxerre": "أوكسير",
    "Auxerre": "أوكسير",

    "RC Strasbourg": "ستراسبورغ",
    "Strasbourg": "ستراسبورغ",

    "FC Lorient": "لوريان",
    "Lorient": "لوريان",

    "OGC Nice": "نيس",
    "Nice": "نيس",

    "AS Saint-Etienne": "سانت إيتيان",
    "Saint-Etienne": "سانت إيتيان",
}


def clean_text(value):
    if not value:
        return ""

    value = re.sub(r"\s+", " ", str(value))

    return value.strip()


def team_name(name):
    name = clean_text(name)

    if name in TEAM_AR:
        return TEAM_AR[name]

    lower_name = name.lower()

    for key, value in TEAM_AR.items():

        if key.lower() == lower_name:
            return value

    return name


# =========================================================
# HTTP
# =========================================================

def download_page(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        print(
            "365Scores:",
            response.status_code,
            url
        )

        if response.status_code != 200:
            return None

        return response.text

    except requests.RequestException as error:

        print(
            "365Scores request error:",
            error
        )

        return None

    except Exception as error:

        print(
            "365Scores unknown error:",
            error
        )

        return None


# =========================================================
# DATE
# =========================================================

def current_date():

    return datetime.now(TIMEZONE)


def today_text():

    now = current_date()

    return now.strftime("%d/%m/%Y")


# =========================================================
# MATCH PARSER
# =========================================================

def extract_possible_matches(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup.find_all(
        ["script", "style", "noscript"]
    ):
        tag.decompose()

    result = []

    elements = soup.find_all(
        ["div", "span", "a", "p", "li"]
    )

    for element in elements:

        text = clean_text(
            element.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            continue

        if len(text) > 180:
            continue

        result.append(text)

    # Remove duplicates
    unique = []

    seen = set()

    for item in result:

        if item in seen:
            continue

        seen.add(item)
        unique.append(item)

    return unique


def parse_match(text):

    text = clean_text(text)

    # ----------------------------------
    # Example:
    # Arsenal 19:30 Chelsea
    # ----------------------------------

    time_match = re.search(
        r"^(.+?)\s+(\d{1,2}:\d{2})\s+(.+)$",
        text
    )

    if time_match:

        home = clean_text(
            time_match.group(1)
        )

        match_time = time_match.group(2)

        away = clean_text(
            time_match.group(3)
        )

        if valid_team_pair(home, away):

            return {
                "home": home,
                "away": away,
                "time": match_time,
                "score": None,
                "status": "scheduled",
            }

    # ----------------------------------
    # Example:
    # Arsenal 2-1 Chelsea
    # ----------------------------------

    score_match = re.search(
        r"^(.+?)\s+(\d+)\s*[-:]\s*(\d+)\s+(.+)$",
        text
    )

    if score_match:

        home = clean_text(
            score_match.group(1)
        )

        home_score = score_match.group(2)
        away_score = score_match.group(3)

        away = clean_text(
            score_match.group(4)
        )

        if valid_team_pair(home, away):

            return {
                "home": home,
                "away": away,
                "time": None,
                "score": (
                    f"{home_score}-{away_score}"
                ),
                "status": "live",
            }

    return None


def valid_team_pair(home, away):

    if not home or not away:
        return False

    if home.lower() == away.lower():
        return False

    if len(home) > 70:
        return False

    if len(away) > 70:
        return False

    forbidden = [
        "standings",
        "fixtures",
        "matches",
        "results",
        "news",
        "statistics",
        "365scores",
        "follow",
        "login",
        "register",
    ]

    combined = (
        home.lower() +
        " " +
        away.lower()
    )

    for word in forbidden:

        if word in combined:
            return False

    return True


def get_matches(league_key):

    league = LEAGUES[league_key]

    html = download_page(
        league["matches"]
    )

    if not html:
        return []

    lines = extract_possible_matches(
        html
    )

    matches = []

    seen = set()

    for line in lines:

        parsed = parse_match(line)

        if not parsed:
            continue

        key = (
            parsed["home"].lower(),
            parsed["away"].lower(),
            parsed.get("time"),
            parsed.get("score"),
        )

        if key in seen:
            continue

        seen.add(key)

        matches.append(parsed)

    return matches[:40]


# =========================================================
# STANDINGS
# =========================================================

def parse_standing(text):

    text = clean_text(text)

    # Try a common structure:
    #
    # 1 Arsenal 10 20 15
    #

    pattern = re.match(
        r"^(\d{1,2})\s+(.+?)\s+"
        r"(\d+)\s+"
        r"(\d+)\s+"
        r"(-?\d+)\s*$",
        text
    )

    if not pattern:
        return None

    return {
        "position": pattern.group(1),
        "team": pattern.group(2),
        "played": pattern.group(3),
        "points": pattern.group(4),
        "goal_difference": pattern.group(5),
    }


def get_standings(league_key):

    league = LEAGUES[league_key]

    html = download_page(
        league["standings"]
    )

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup.find_all(
        ["script", "style", "noscript"]
    ):
        tag.decompose()

    standings = []

    # First attempt: tables
    for row in soup.find_all("tr"):

        text = clean_text(
            row.get_text(
                " ",
                strip=True
            )
        )

        parsed = parse_standing(text)

        if parsed:
            standings.append(parsed)

    # Second attempt: generic elements
    if not standings:

        for element in soup.find_all(
            ["div", "span", "li"]
        ):

            text = clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if len(text) > 150:
                continue

            parsed = parse_standing(text)

            if parsed:
                standings.append(parsed)

    # Remove duplicate teams
    final = []

    seen = set()

    for row in standings:

        team = clean_text(
            row["team"]
        )

        if team.lower() in seen:
            continue

        seen.add(team.lower())

        final.append(row)

    return final[:30]


# =========================================================
# POISSON
# =========================================================

TEAM_STRENGTH = {

    # Algeria
    "مولودية الجزائر": 1.18,
    "اتحاد العاصمة": 1.12,
    "شباب بلوزداد": 1.15,
    "شبيبة القبائل": 1.08,
    "شباب قسنطينة": 1.03,
    "وفاق سطيف": 1.00,
    "شبيبة الساورة": 0.98,
    "مولودية وهران": 0.97,
    "جمعية الشلف": 0.95,

    # England
    "مانشستر سيتي": 1.35,
    "أرسنال": 1.30,
    "ليفربول": 1.28,
    "تشيلسي": 1.12,
    "مانشستر يونايتد": 1.08,
    "نيوكاسل": 1.07,
    "توتنهام": 1.06,
    "أستون فيلا": 1.05,

    # France
    "باريس سان جيرمان": 1.35,
    "موناكو": 1.14,
    "مارسيليا": 1.10,
    "ليل": 1.08,
    "ليون": 1.06,
    "لانس": 1.03,
    "رين": 1.02,
}


def strength(team):

    return TEAM_STRENGTH.get(
        team_name(team),
        1.0
    )


def poisson_probability(
    goals,
    expected
):

    if expected <= 0:
        return 0

    return (
        math.exp(-expected)
        * expected ** goals
        / math.factorial(goals)
    )


def analyze(home, away):

    home_strength = strength(home)
    away_strength = strength(away)

    home_expected = (
        1.35
        * home_strength
        / max(
            0.75,
            away_strength * 0.92
        )
    )

    away_expected = (
        1.05
        * away_strength
        / max(
            0.75,
            home_strength
        )
    )

    home_expected = max(
        0.20,
        min(home_expected, 4.0)
    )

    away_expected = max(
        0.20,
        min(away_expected, 3.5)
    )

    home_win = 0
    draw = 0
    away_win = 0

    score_probabilities = []

    for hg in range(0, 9):

        for ag in range(0, 9):

            probability = (
                poisson_probability(
                    hg,
                    home_expected
                )
                *
                poisson_probability(
                    ag,
                    away_expected
                )
            )

            if hg > ag:
                home_win += probability

            elif hg == ag:
                draw += probability

            else:
                away_win += probability

            score_probabilities.append(
                (
                    probability,
                    hg,
                    ag
                )
            )

    score_probabilities.sort(
        reverse=True
    )

    # BTTS
    home_zero = poisson_probability(
        0,
        home_expected
    )

    away_zero = poisson_probability(
        0,
        away_expected
    )

    btts_yes = (
        1
        - home_zero
        - away_zero
        + home_zero * away_zero
    )

    # Over / Under
    totals = {}

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5,
    ]:

        under = 0

        for hg in range(0, 9):

            for ag in range(0, 9):

                if hg + ag <= line:

                    under += (
                        poisson_probability(
                            hg,
                            home_expected
                        )
                        *
                        poisson_probability(
                            ag,
                            away_expected
                        )
                    )

        totals[line] = {
            "over": max(
                0,
                1 - under
            ),
            "under": max(
                0,
                under
            ),
        }

    return {
        "home_expected": home_expected,
        "away_expected": away_expected,
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "btts_yes": btts_yes,
        "btts_no": 1 - btts_yes,
        "totals": totals,
        "scores": score_probabilities[:5],
    }


def percent(value):

    return f"{value * 100:.1f}%"


# =========================================================
# ANALYSIS MESSAGE
# =========================================================

def analysis_message(home, away):

    result = analyze(
        home,
        away
    )

    home_ar = team_name(home)
    away_ar = team_name(away)

    message = (
        "🧠 <b>تحليل المباراة</b>\n\n"

        f"🏠 <b>{home_ar}</b>\n"
        "🆚\n"
        f"✈️ <b>{away_ar}</b>\n\n"

        "📊 <b>الأهداف المتوقعة</b>\n"
        f"{home_ar}: "
        f"<b>{result['home_expected']:.2f}</b>\n"

        f"{away_ar}: "
        f"<b>{result['away_expected']:.2f}</b>\n\n"

        "🏆 <b>احتمالات النتيجة</b>\n"
        f"فوز {home_ar}: "
        f"<b>{percent(result['home_win'])}</b>\n"

        f"تعادل: "
        f"<b>{percent(result['draw'])}</b>\n"

        f"فوز {away_ar}: "
        f"<b>{percent(result['away_win'])}</b>\n\n"

        "⚽ <b>BTTS</b>\n"
        f"نعم: "
        f"<b>{percent(result['btts_yes'])}</b>\n"

        f"لا: "
        f"<b>{percent(result['btts_no'])}</b>\n\n"

        "📈 <b>Over / Under</b>\n"
    )

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5,
    ]:

        data = result["totals"][line]

        message += (
            f"Over {line}: "
            f"<b>{percent(data['over'])}</b>"
            " | "
            f"Under {line}: "
            f"<b>{percent(data['under'])}</b>\n"
        )

    message += (
        "\n🎯 <b>النتائج الأكثر احتمالاً</b>\n"
    )

    for probability, hg, ag in result["scores"]:

        message += (
            f"{home_ar} "
            f"<b>{hg}-{ag}</b> "
            f"{away_ar} "
            f"({percent(probability)})\n"
        )

    message += (
        "\n⚠️ <i>"
        "التحليل احتمالي وليس ضماناً للنتيجة."
        "</i>"
    )

    return message


# =========================================================
# TELEGRAM USERS
# =========================================================

authorized_users = set()


def authorized(chat_id):

    return chat_id in authorized_users


# =========================================================
# KEYBOARD
# =========================================================

def keyboard():

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        "🇩🇿 مباريات الجزائر",
        "🏴 مباريات إنجلترا"
    )

    kb.row(
        "🇫🇷 مباريات فرنسا",
        "🔴 مباشر"
    )

    kb.row(
        "📊 ترتيب الجزائر",
        "📊 ترتيب إنجلترا"
    )

    kb.row(
        "📊 ترتيب فرنسا",
        "ℹ️ معلومات"
    )

    return kb


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    chat_id = message.chat.id

    authorized_users.discard(
        chat_id
    )

    bot.send_message(
        chat_id,
        "⚽ <b>مرحباً بك</b>\n\n"
        "بوت تحليل مباريات كرة القدم.\n\n"
        "🇩🇿 الدوري الجزائري\n"
        "🏴 الدوري الإنجليزي\n"
        "🇫🇷 الدوري الفرنسي\n\n"
        "🔐 أرسل رمز الدخول:"
    )


# =========================================================
# ACCESS
# =========================================================

@bot.message_handler(
    func=lambda message:
    not authorized(message.chat.id)
)
def access_code(message):

    if message.text.strip() == ACCESS_CODE:

        authorized_users.add(
            message.chat.id
        )

        bot.send_message(
            message.chat.id,
            "✅ <b>تم الدخول بنجاح</b>\n\n"
            "اختر الخدمة:",
            reply_markup=keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            "❌ رمز الدخول غير صحيح."
        )


# =========================================================
# MATCHES MESSAGE
# =========================================================

def format_matches(league_key):

    league = LEAGUES[league_key]

    matches = get_matches(
        league_key
    )

    if not matches:

        return (
            f"{league['name']}\n\n"
            "📅 لا توجد مباريات ظاهرة حالياً.\n\n"
            "🔄 اضغط الزر مرة أخرى بعد قليل."
        )

    message = (
        f"{league['name']}\n"
        f"📅 <b>المباريات</b>\n\n"
    )

    for index, match in enumerate(
        matches,
        start=1
    ):

        home = team_name(
            match["home"]
        )

        away = team_name(
            match["away"]
        )

        if match.get("score"):

            status = (
                f"🔴 <b>"
                f"{match['score']}"
                f"</b>"
            )

        else:

            status = (
                f"🕐 "
                f"{match.get('time', '--:--')}"
            )

        message += (
            f"<b>{index}. {home}</b>\n"
            f"   {status}\n"
            f"<b>{away}</b>\n\n"
        )

    return message


# =========================================================
# STANDINGS MESSAGE
# =========================================================

def format_standings(league_key):

    league = LEAGUES[league_key]

    rows = get_standings(
        league_key
    )

    if not rows:

        return (
            f"{league['name']}\n\n"
            "📊 تعذر استخراج جدول الترتيب الآن.\n"
            "🔄 حاول مرة أخرى."
        )

    message = (
        f"📊 <b>ترتيب {league['short']}</b>\n\n"
    )

    for row in rows:

        position = row["position"]

        team = team_name(
            row["team"]
        )

        played = row["played"]

        points = row["points"]

        gd = row["goal_difference"]

        message += (
            f"<b>{position}.</b> "
            f"{team}\n"
            f"   لعب: {played} | "
            f"نقاط: <b>{points}</b> | "
            f"GD: {gd}\n\n"
        )

    return message


# =========================================================
# LIVE
# =========================================================

def live_matches():

    live = []

    for league_key, league in LEAGUES.items():

        matches = get_matches(
            league_key
        )

        for match in matches:

            if match.get("score"):

                live.append(
                    {
                        "league":
                            league["short"],
                        "home":
                            team_name(
                                match["home"]
                            ),
                        "away":
                            team_name(
                                match["away"]
                            ),
                        "score":
                            match["score"],
                    }
                )

    return live


def format_live():

    matches = live_matches()

    if not matches:

        return (
            "🔴 <b>المباريات المباشرة</b>\n\n"
            "لا توجد مباريات مباشرة ظاهرة حالياً."
        )

    message = (
        "🔴 <b>المباريات المباشرة</b>\n\n"
    )

    for match in matches:

        message += (
            f"🏆 {match['league']}\n"
            f"⚽ {match['home']} "
            f"<b>{match['score']}</b> "
            f"{match['away']}\n\n"
        )

    return message


# =========================================================
# BUTTONS
# =========================================================

@bot.message_handler(
    func=lambda message:
    authorized(message.chat.id)
)
def handle_buttons(message):

    text = message.text.strip()

    if text == "🇩🇿 مباريات الجزائر":

        bot.send_message(
            message.chat.id,
            format_matches("dz"),
            reply_markup=keyboard()
        )

        return

    if text == "🏴 مباريات إنجلترا":

        bot.send_message(
            message.chat.id,
            format_matches("eng"),
            reply_markup=keyboard()
        )

        return

    if text == "🇫🇷 مباريات فرنسا":

        bot.send_message(
            message.chat.id,
            format_matches("fr"),
            reply_markup=keyboard()
        )

        return

    if text == "📊 ترتيب الجزائر":

        bot.send_message(
            message.chat.id,
            format_standings("dz"),
            reply_markup=keyboard()
        )

        return

    if text == "📊 ترتيب إنجلترا":

        bot.send_message(
            message.chat.id,
            format_standings("eng"),
            reply_markup=keyboard()
        )

        return

    if text == "📊 ترتيب فرنسا":

        bot.send_message(
            message.chat.id,
            format_standings("fr"),
            reply_markup=keyboard()
        )

        return

    if text == "🔴 مباشر":

        bot.send_message(
            message.chat.id,
            format_live(),
            reply_markup=keyboard()
        )

        return

    if text == "ℹ️ معلومات":

        bot.send_message(
            message.chat.id,
            "ℹ️ <b>معلومات البوت</b>\n\n"
            "⚽ تحليل مباريات كرة القدم\n\n"
            "🇩🇿 الدوري الجزائري\n"
            "🏴 الدوري الإنجليزي\n"
            "🇫🇷 الدوري الفرنسي\n\n"
            "📅 مباريات\n"
            "📊 ترتيب\n"
            "🔴 مباشر\n"
            "🧠 Poisson\n"
            "📈 Over / Under\n"
            "⚽ BTTS\n"
            "🎯 النتائج المحتملة\n\n"
            "🔐 كود الدخول: 1230\n\n"
            "المصدر الأساسي: 365Scores",
            reply_markup=keyboard()
        )

        return

    bot.send_message(
        message.chat.id,
        "اختر إحدى الخدمات من القائمة.",
        reply_markup=keyboard()
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route("/", methods=["GET"])
def index():

    return "Football Telegram Bot is running."


@app.route("/health", methods=["GET"])
def health():

    return "OK"


# ---------------------------------------------------------
# IMPORTANT:
# Telegram currently sends to /telegram/webhook
# ---------------------------------------------------------

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    try:

        data = request.get_data(
            as_text=True
        )

        if not data:
            return "EMPTY", 400

        update = telebot.types.Update.de_json(
            data
        )

        bot.process_new_updates(
            [update]
        )

        return "OK", 200

    except Exception as error:

        print(
            "WEBHOOK ERROR:",
            repr(error)
        )

        return "ERROR", 500


# ---------------------------------------------------------
# Backup webhook
# ---------------------------------------------------------

@app.route(
    "/webhook",
    methods=["POST"]
)
def backup_webhook():

    try:

        data = request.get_data(
            as_text=True
        )

        update = telebot.types.Update.de_json(
            data
        )

        bot.process_new_updates(
            [update]
        )

        return "OK", 200

    except Exception as error:

        print(
            "BACKUP WEBHOOK ERROR:",
            repr(error)
        )

        return "ERROR", 500


# =========================================================
# LIVE AUTO UPDATE
# =========================================================

def live_checker():

    while True:

        try:

            print(
                "Checking live matches..."
            )

            matches = live_matches()

            if matches:

                message = (
                    "🔄 <b>تحديث مباشر</b>\n\n"
                )

                for match in matches:

                    message += (
                        f"🏆 {match['league']}\n"
                        f"⚽ {match['home']} "
                        f"<b>{match['score']}</b> "
                        f"{match['away']}\n\n"
                    )

                for chat_id in list(
                    authorized_users
                ):

                    try:

                        bot.send_message(
                            chat_id,
                            message
                        )

                    except Exception as error:

                        print(
                            "Telegram live error:",
                            error
                        )

        except Exception as error:

            print(
                "LIVE CHECK ERROR:",
                error
            )

        # 10 minutes
        time.sleep(600)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "Football Telegram Bot"
    )

    print(
        "Starting..."
    )

    print(
        "Port:",
        PORT
    )

    print(
        "Webhook:",
        "/telegram/webhook"
    )

    print(
        "================================"
    )

    # Start live checker
    checker = threading.Thread(
        target=live_checker,
        daemon=True
    )

    checker.start()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
