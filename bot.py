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
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ACCESS_CODE = "1230"

PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

TZ = ZoneInfo("Africa/Algiers")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ar;q=0.7",
}

# 365Scores league IDs
LEAGUES = {
    "dz": {
        "name": "🇩🇿 الدوري الجزائري",
        "short": "الجزائر",
        "id": "560",
        "matches": "https://www.365scores.com/football/league/ligue-1-560/matches",
        "standings": "https://www.365scores.com/football/league/ligue-1-560/standings",
    },
    "eng": {
        "name": "🏴 الدوري الإنجليزي",
        "short": "إنجلترا",
        "id": "7",
        "matches": "https://www.365scores.com/football/league/premier-league-7/matches",
        "standings": "https://www.365scores.com/football/league/premier-league-7/standings",
    },
    "fr": {
        "name": "🇫🇷 الدوري الفرنسي",
        "short": "فرنسا",
        "id": "35",
        "matches": "https://www.365scores.com/football/league/ligue-1-35/matches",
        "standings": "https://www.365scores.com/football/league/ligue-1-35/standings",
    },
}


# =========================================================
# TEAM NAMES
# =========================================================

TEAM_AR = {
    # Algeria
    "MC Alger": "مولودية الجزائر",
    "MC Alger ": "مولودية الجزائر",
    "USM Alger": "اتحاد العاصمة",
    "CR Belouizdad": "شباب بلوزداد",
    "JS Kabylie": "شبيبة القبائل",
    "CS Constantine": "شباب قسنطينة",
    "ES Setif": "وفاق سطيف",
    "ES Sétif": "وفاق سطيف",
    "JS Saoura": "شبيبة الساورة",
    "Saoura": "شبيبة الساورة",
    "MC Oran": "مولودية وهران",
    "ASO Chlef": "جمعية الشلف",
    "US Biskra": "اتحاد بسكرة",
    "MB Rouisset": "مولودية الرويسات",
    "Olympique Akbou": "أولمبيك أقبو",
    "USM Khenchela": "اتحاد خنشلة",
    "ES Ben Aknoun": "نجم بن عكنون",
    "CR Temouchent": "شباب تموشنت",
    "JS El Biar": "شبيبة الأبيار",

    # England
    "Arsenal": "أرسنال",
    "Chelsea": "تشيلسي",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Tottenham": "توتنهام",
    "Newcastle": "نيوكاسل",
    "Aston Villa": "أستون فيلا",
    "Everton": "إيفرتون",
    "West Ham": "وست هام",
    "Brighton": "برايتون",
    "Fulham": "فولهام",
    "Crystal Palace": "كريستال بالاس",
    "Brentford": "برينتفورد",
    "Bournemouth": "بورنموث",
    "Wolves": "وولفرهامبتون",
    "Wolverhampton": "وولفرهامبتون",
    "Nottingham Forest": "نوتنغهام فورست",
    "Leeds United": "ليدز يونايتد",
    "Sunderland": "سندرلاند",
    "Burnley": "بيرنلي",

    # France
    "Paris Saint-Germain": "باريس سان جيرمان",
    "PSG": "باريس سان جيرمان",
    "Paris FC": "باريس إف سي",
    "AS Monaco": "موناكو",
    "Monaco": "موناكو",
    "Olympique Marseille": "مارسيليا",
    "Marseille": "مارسيليا",
    "Olympique Lyonnais": "ليون",
    "Lyon": "ليون",
    "LOSC Lille": "ليل",
    "Lille": "ليل",
    "RC Lens": "لانس",
    "Lens": "لانس",
    "Rennes": "رين",
    "Stade Rennais": "رين",
    "Toulouse": "تولوز",
    "Brest": "بريست",
    "Le Havre": "لوهافر",
    "Angers": "أنجيه",
    "Auxerre": "أوكسير",
    "Strasbourg": "ستراسبورغ",
    "Lorient": "لوريان",
    "OGC Nice": "نيس",
    "Nice": "نيس",
    "Troyes": "تروا",
    "Le Mans": "لومان",
}


def team_name(name):
    name = clean_text(name)

    if name in TEAM_AR:
        return TEAM_AR[name]

    # Try partial matching
    for key, value in TEAM_AR.items():
        if key.lower() == name.lower():
            return value

    return name


# =========================================================
# HTTP
# =========================================================

def get_page(url):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=25,
        )

        if r.status_code != 200:
            print("365Scores HTTP:", r.status_code, url)
            return None

        return r.text

    except Exception as e:
        print("365Scores ERROR:", e)
        return None


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================================================
# DATE
# =========================================================

def today_strings():
    now = datetime.now(TZ)

    return {
        "iso": now.strftime("%Y-%m-%d"),
        "day": now.day,
        "month": now.month,
        "year": now.year,
        "full": now.strftime("%d/%m/%Y"),
    }


def date_matches_today(text):
    """
    Detect today's date in several formats.
    """

    now = datetime.now(TZ)

    patterns = [
        now.strftime("%d/%m/%Y"),
        now.strftime("%-d/%-m/%Y") if os.name != "nt" else now.strftime("%d/%m/%Y"),
        now.strftime("%m/%d/%Y"),
        now.strftime("%-m/%-d/%Y") if os.name != "nt" else now.strftime("%m/%d/%Y"),
        now.strftime("%d/%m"),
        now.strftime("%m/%d"),
    ]

    for p in patterns:
        if p in text:
            return True

    months = {
        1: ["January", "Jan", "janvier"],
        2: ["February", "Feb", "février"],
        3: ["March", "Mar", "mars"],
        4: ["April", "Apr", "avril"],
        5: ["May", "mai"],
        6: ["June", "Jun", "juin"],
        7: ["July", "Jul", "juillet"],
        8: ["August", "Aug", "août"],
        9: ["September", "Sep", "septembre"],
        10: ["October", "Oct", "octobre"],
        11: ["November", "Nov", "novembre"],
        12: ["December", "Dec", "décembre"],
    }

    for m in months[now.month]:
        if re.search(rf"\b{m}\b", text, re.I):
            # avoid accidentally accepting old page content
            if str(now.day) in text:
                return True

    return False


# =========================================================
# PARSING MATCHES
# =========================================================

def parse_match_line(line):
    """
    Attempts to extract:

        Home 19:00 Away
        Home Ended 2-1 Away
        Home 2-1 Away
    """

    line = clean_text(line)

    if not line:
        return None

    # Ignore obvious non-match text
    bad = [
        "latest results",
        "fixtures",
        "standings",
        "copyright",
        "365scores",
        "see more",
        "add the",
        "follow",
        "about",
        "round ",
    ]

    low = line.lower()

    if any(x in low for x in bad):
        return None

    # Result:
    m = re.search(
        r"^(.+?)\s+(?:Ended|Final|FT)\s+(\d+)\s*[-:]\s*(\d+)\s+(.+)$",
        line,
        re.I,
    )

    if m:
        return {
            "home": clean_text(m.group(1)),
            "score": f"{m.group(2)}-{m.group(3)}",
            "away": clean_text(m.group(4)),
            "status": "ended",
        }

    # Score without Ended
    m = re.search(
        r"^(.+?)\s+(\d+)\s*[-:]\s*(\d+)\s+(.+)$",
        line,
    )

    if m:
        home = clean_text(m.group(1))
        away = clean_text(m.group(4))

        if len(home) > 1 and len(away) > 1:
            return {
                "home": home,
                "score": f"{m.group(2)}-{m.group(3)}",
                "away": away,
                "status": "live_or_finished",
            }

    # Kickoff:
    m = re.search(
        r"^(.+?)\s+(\d{1,2}:\d{2})\s+(.+)$",
        line,
    )

    if m:
        home = clean_text(m.group(1))
        time_value = m.group(2)
        away = clean_text(m.group(3))

        if (
            len(home) >= 2
            and len(away) >= 2
            and len(home) < 60
            and len(away) < 60
        ):
            return {
                "home": home,
                "score": None,
                "away": away,
                "time": time_value,
                "status": "scheduled",
            }

    return None


def extract_matches_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    lines = []

    # 365Scores renders a lot of content as divs/spans.
    for element in soup.find_all(["div", "span", "a", "p", "li"]):
        text = clean_text(element.get_text(" ", strip=True))

        if text and len(text) <= 150:
            lines.append(text)

    # Remove duplicates but preserve order
    seen = set()
    unique_lines = []

    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    matches = []

    for line in unique_lines:
        parsed = parse_match_line(line)

        if not parsed:
            continue

        # Avoid absurd matches
        if parsed["home"].lower() == parsed["away"].lower():
            continue

        # avoid rows containing too much UI
        if len(parsed["home"]) > 70 or len(parsed["away"]) > 70:
            continue

        matches.append(parsed)

    # Deduplicate
    final = []
    keys = set()

    for m in matches:
        key = (
            m["home"].lower(),
            m["away"].lower(),
            m.get("score"),
            m.get("time"),
        )

        if key not in keys:
            keys.add(key)
            final.append(m)

    return final


def get_today_matches(league_key):
    league = LEAGUES[league_key]

    html = get_page(league["matches"])

    if not html:
        return []

    matches = extract_matches_from_html(html)

    # Since the league page contains several dates,
    # we keep likely upcoming/current rows.
    #
    # If parsing gives too many rows, limit duplicates.
    return matches[:30]


# =========================================================
# STANDINGS
# =========================================================

def parse_standing_row(text):
    text = clean_text(text)

    if not text:
        return None

    # Typical 365Scores visible structure:
    #
    # 11 Angers 2 3:3 0 3 1 0 1 WL
    #
    m = re.match(
        r"^(\d{1,2})\s+(.+?)\s+"
        r"(\d+)\s+"
        r"(\d+):(\d+)\s+"
        r"(-?\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)"
        r"(?:\s+([WDL]+))?$",
        text,
    )

    if not m:
        return None

    return {
        "pos": m.group(1),
        "team": clean_text(m.group(2)),
        "played": m.group(3),
        "gf": m.group(4),
        "ga": m.group(5),
        "gd": m.group(6),
        "points": m.group(7),
        "wins": m.group(8),
        "draws": m.group(9),
        "losses": m.group(10),
        "form": m.group(11) or "",
    }


def get_standings(league_key):
    league = LEAGUES[league_key]

    html = get_page(league["standings"])

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    rows = []

    # First try actual table rows
    for tr in soup.find_all("tr"):
        text = clean_text(tr.get_text(" ", strip=True))

        row = parse_standing_row(text)

        if row:
            rows.append(row)

    # Fallback: inspect div/span/li
    if not rows:
        for element in soup.find_all(["div", "span", "li"]):
            text = clean_text(element.get_text(" ", strip=True))

            if len(text) <= 150:
                row = parse_standing_row(text)

                if row:
                    rows.append(row)

    # Deduplicate
    final = []
    seen = set()

    for row in rows:
        if row["team"] not in seen:
            seen.add(row["team"])
            final.append(row)

    return final[:30]


# =========================================================
# POISSON
# =========================================================

def poisson(k, lam):
    if lam <= 0:
        return 0.0

    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_distribution(lam, max_goals=8):
    return {
        i: poisson(i, lam)
        for i in range(max_goals + 1)
    }


def probability_over(home_lambda, away_lambda, line):
    ph = poisson_distribution(home_lambda)
    pa = poisson_distribution(away_lambda)

    under = 0.0

    for h, hp in ph.items():
        for a, ap in pa.items():
            if h + a <= line:
                under += hp * ap

    return max(0, 1 - under)


def probability_btts(home_lambda, away_lambda):
    home_no = poisson(0, home_lambda)
    away_no = poisson(0, away_lambda)

    yes = 1 - home_no - away_no + (home_no * away_no)

    return yes


# Base strengths are only a fallback.
# The probabilities themselves are calculated mathematically.
BASE_STRENGTH = {
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
    "موناكو": 1.14,
    "لانس": 1.03,
    "رين": 1.02,
}


def team_strength(name):
    name = team_name(name)

    return BASE_STRENGTH.get(name, 1.0)


def analyze_match(home, away):
    h = team_strength(home)
    a = team_strength(away)

    # Dynamic Poisson lambdas based on relative strength.
    home_lambda = 1.35 * h / max(0.75, a * 0.92)
    away_lambda = 1.05 * a / max(0.75, h)

    # Prevent unrealistic numbers
    home_lambda = max(0.25, min(home_lambda, 3.8))
    away_lambda = max(0.20, min(away_lambda, 3.3))

    ph = poisson_distribution(home_lambda)
    pa = poisson_distribution(away_lambda)

    home_win = 0
    draw = 0
    away_win = 0

    scores = []

    for hg, hp in ph.items():
        for ag, ap in pa.items():
            p = hp * ap

            if hg > ag:
                home_win += p
            elif hg == ag:
                draw += p
            else:
                away_win += p

            scores.append((p, hg, ag))

    scores.sort(reverse=True)

    btts_yes = probability_btts(home_lambda, away_lambda)

    over = {}

    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        over[line] = probability_over(
            home_lambda,
            away_lambda,
            line,
        )

    return {
        "home_lambda": home_lambda,
        "away_lambda": away_lambda,
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "btts_yes": btts_yes,
        "btts_no": 1 - btts_yes,
        "over": over,
        "scores": scores[:5],
    }


# =========================================================
# FORMAT ANALYSIS
# =========================================================

def pct(x):
    return f"{x * 100:.1f}%"


def analysis_text(home, away):
    data = analyze_match(home, away)

    h = team_name(home)
    a = team_name(away)

    text = (
        f"🧠 <b>تحليل المباراة</b>\n\n"
        f"🏠 <b>{h}</b>\n"
        f"🆚\n"
        f"✈️ <b>{a}</b>\n\n"
        f"📊 <b>Poisson</b>\n"
        f"أهداف متوقعة {h}: <b>{data['home_lambda']:.2f}</b>\n"
        f"أهداف متوقعة {a}: <b>{data['away_lambda']:.2f}</b>\n\n"
        f"🏆 فوز {h}: <b>{pct(data['home_win'])}</b>\n"
        f"🤝 التعادل: <b>{pct(data['draw'])}</b>\n"
        f"🏆 فوز {a}: <b>{pct(data['away_win'])}</b>\n\n"
        f"⚽ <b>BTTS</b>\n"
        f"نعم: <b>{pct(data['btts_yes'])}</b>\n"
        f"لا: <b>{pct(data['btts_no'])}</b>\n\n"
        f"📈 <b>Over / Under</b>\n"
    )

    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        op = data["over"][line]

        text += (
            f"Over {line}: <b>{pct(op)}</b> | "
            f"Under {line}: <b>{pct(1-op)}</b>\n"
        )

    text += "\n🎯 <b>النتائج الأكثر احتمالاً</b>\n"

    for p, hg, ag in data["scores"]:
        text += f"{h} {hg} - {ag} {a} → <b>{pct(p)}</b>\n"

    text += (
        "\n⚠️ <i>هذه احتمالات رياضية وليست ضماناً للنتيجة.</i>"
    )

    return text


# =========================================================
# TELEGRAM USERS
# =========================================================

authorized_users = set()


def is_authorized(chat_id):
    return chat_id in authorized_users


# =========================================================
# KEYBOARD
# =========================================================

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2,
    )

    kb.add(
        "🇩🇿 مباريات الجزائر",
        "🏴 مباريات إنجلترا",
    )

    kb.add(
        "🇫🇷 مباريات فرنسا",
        "🔴 المباريات المباشرة",
    )

    kb.add(
        "📊 ترتيب الجزائر",
        "📊 ترتيب إنجلترا",
    )

    kb.add(
        "📊 ترتيب فرنسا",
        "ℹ️ معلومات",
    )

    return kb


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    authorized_users.discard(chat_id)

    bot.send_message(
        chat_id,
        "⚽ <b>مرحبا بك في بوت تحليل كرة القدم</b>\n\n"
        "البوت يعتمد على بيانات 365Scores.\n\n"
        "🔐 أدخل رمز الدخول:",
    )


@bot.message_handler(commands=["menu"])
def menu(message):
    if not is_authorized(message.chat.id):
        bot.send_message(
            message.chat.id,
            "🔐 أدخل رمز الدخول أولاً."
        )
        return

    bot.send_message(
        message.chat.id,
        "اختر الخدمة:",
        reply_markup=main_keyboard(),
    )


# =========================================================
# ACCESS CODE
# =========================================================

@bot.message_handler(func=lambda message: not is_authorized(message.chat.id))
def access_handler(message):
    code = message.text.strip()

    if code == ACCESS_CODE:
        authorized_users.add(message.chat.id)

        bot.send_message(
            message.chat.id,
            "✅ تم التحقق بنجاح.\n\n"
            "⚽ اختر الدوري أو الخدمة:",
            reply_markup=main_keyboard(),
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ رمز الدخول غير صحيح."
        )


# =========================================================
# MATCH LIST
# =========================================================

def matches_message(league_key):
    league = LEAGUES[league_key]

    matches = get_today_matches(league_key)

    if not matches:
        return (
            f"{league['name']}\n\n"
            "📅 لا توجد مباريات يمكن استخراجها حالياً.\n\n"
            "🔄 حاول مرة أخرى بعد قليل."
        )

    text = (
        f"{league['name']}\n"
        f"📅 مباريات اليوم\n\n"
    )

    for i, m in enumerate(matches, 1):

        home = team_name(m["home"])
        away = team_name(m["away"])

        if m.get("score"):
            status = f"🔴 {m['score']}"
        else:
            status = f"🕐 {m.get('time', '--:--')}"

        text += (
            f"<b>{i}. {home}</b>\n"
            f"   {status}\n"
            f"   <b>{away}</b>\n\n"
        )

    return text


def send_matches(message, league_key):
    text = matches_message(league_key)

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard(),
    )


# =========================================================
# STANDINGS
# =========================================================

def standings_message(league_key):
    league = LEAGUES[league_key]

    rows = get_standings(league_key)

    if not rows:
        return (
            f"{league['name']}\n\n"
            "📊 لم أستطع استخراج جدول الترتيب حالياً.\n"
            "🔄 حاول مرة أخرى بعد قليل."
        )

    text = (
        f"📊 <b>ترتيب {league['short']}</b>\n\n"
        f"<code>"
        f"#  الفريق                 لعب  نقاط  GD\n"
    )

    for row in rows:
        pos = row["pos"]
        team = team_name(row["team"])

        if len(team) > 20:
            team = team[:20]

        text += (
            f"{pos:>2} "
            f"{team:<20} "
            f"{row['played']:>2} "
            f"{row['points']:>4} "
            f"{row['gd']:>4}\n"
        )

    text += "</code>"

    return text


def send_standings(message, league_key):
    bot.send_message(
        message.chat.id,
        standings_message(league_key),
        reply_markup=main_keyboard(),
    )


# =========================================================
# LIVE
# =========================================================

def live_message():
    all_live = []

    for key, league in LEAGUES.items():
        matches = get_today_matches(key)

        for m in matches:
            if m.get("score") and m["status"] != "ended":
                all_live.append(
                    (
                        league["short"],
                        team_name(m["home"]),
                        m["score"],
                        team_name(m["away"]),
                    )
                )

    if not all_live:
        return (
            "🔴 <b>المباريات المباشرة</b>\n\n"
            "لا توجد مباراة مباشرة ظاهرة حالياً."
        )

    text = "🔴 <b>المباريات المباشرة</b>\n\n"

    for league, home, score, away in all_live:
        text += (
            f"🏆 {league}\n"
            f"⚽ {home} <b>{score}</b> {away}\n\n"
        )

    return text


# =========================================================
# BUTTON HANDLER
# =========================================================

@bot.message_handler(func=lambda message: is_authorized(message.chat.id))
def buttons(message):

    text = message.text.strip()

    if text == "🇩🇿 مباريات الجزائر":
        send_matches(message, "dz")
        return

    if text == "🏴 مباريات إنجلترا":
        send_matches(message, "eng")
        return

    if text == "🇫🇷 مباريات فرنسا":
        send_matches(message, "fr")
        return

    if text == "📊 ترتيب الجزائر":
        send_standings(message, "dz")
        return

    if text == "📊 ترتيب إنجلترا":
        send_standings(message, "eng")
        return

    if text == "📊 ترتيب فرنسا":
        send_standings(message, "fr")
        return

    if text == "🔴 المباريات المباشرة":
        bot.send_message(
            message.chat.id,
            live_message(),
            reply_markup=main_keyboard(),
        )
        return

    if text == "ℹ️ معلومات":
        bot.send_message(
            message.chat.id,
            "ℹ️ <b>معلومات البوت</b>\n\n"
            "🇩🇿 الدوري الجزائري\n"
            "🏴 الدوري الإنجليزي\n"
            "🇫🇷 الدوري الفرنسي\n\n"
            "📊 ترتيب كل دوري\n"
            "⚽ مباريات اليوم\n"
            "🔴 المباريات المباشرة\n"
            "🧠 تحليل Poisson\n"
            "📈 Over / Under\n"
            "⚽ BTTS\n"
            "🎯 النتائج الأكثر احتمالاً\n\n"
            "مصدر البيانات: 365Scores",
            reply_markup=main_keyboard(),
        )
        return


# =========================================================
# ANALYSIS COMMAND
# =========================================================

@bot.message_handler(commands=["analysis"])
def analysis_command(message):

    if not is_authorized(message.chat.id):
        bot.send_message(
            message.chat.id,
            "🔐 أدخل رمز الدخول أولاً."
        )
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            "مثال:\n"
            "/analysis Arsenal Chelsea"
        )
        return

    teams = parts[2].split()

    if len(teams) < 2:
        bot.send_message(
            message.chat.id,
            "اكتب اسم الفريقين."
        )
        return

    # This command works best with:
    # /analysis Arsenal Chelsea
    #
    # For names with spaces, use:
    # /analysis "Manchester City" "Chelsea"
    #
    # Simplified handling:
    middle = len(teams) // 2

    home = " ".join(teams[:middle])
    away = " ".join(teams[middle:])

    bot.send_message(
        message.chat.id,
        analysis_text(home, away),
        reply_markup=main_keyboard(),
    )


# =========================================================
# ERROR HANDLER
# =========================================================

@bot.message_handler(func=lambda message: True)
def fallback(message):
    if not is_authorized(message.chat.id):
        return

    bot.send_message(
        message.chat.id,
        "اختر أحد الأزرار من القائمة.",
        reply_markup=main_keyboard(),
    )


# =========================================================
# FLASK WEBHOOK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Football bot is running."


@app.route("/health", methods=["GET"])
def health():
    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK"

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "ERROR", 500


# =========================================================
# AUTO LIVE CHECK
# =========================================================

def live_checker():
    """
    Checks live matches every 10 minutes while the Render
    process is awake.

    Note:
    Render Free services can sleep. For guaranteed background
    updates use an always-on service/worker.
    """

    while True:

        try:
            print("Checking live matches...")

            for chat_id in list(authorized_users):

                try:
                    live = live_message()

                    # Only send if a live match exists
                    if "لا توجد مباراة مباشرة" not in live:
                        bot.send_message(
                            chat_id,
                            "🔄 <b>تحديث مباشر</b>\n\n" + live,
                        )

                except Exception as e:
                    print("LIVE USER ERROR:", e)

        except Exception as e:
            print("LIVE CHECK ERROR:", e)

        time.sleep(600)


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    # Background live checker
    thread = threading.Thread(
        target=live_checker,
        daemon=True,
    )

    thread.start()

    print("Football Telegram Bot started.")

    app.run(
        host="0.0.0.0",
        port=PORT,
    )
