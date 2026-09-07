import os
import re
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import telebot
from telebot import types


# =========================================================
# إعدادات أساسية
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ACCESS_CODE = "1230"
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود في Environment Variables")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

TIMEZONE = ZoneInfo("Africa/Algiers")

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ar;q=0.7",
})


# =========================================================
# الدوريات - 365Scores
# =========================================================

LEAGUES = {
    "dz": {
        "name": "🇩🇿 الدوري الجزائري",
        "short": "الجزائري",
        "matches": "https://www.365scores.com/football/league/ligue-1-560/matches",
        "standings": "https://www.365scores.com/football/league/ligue-1-560/standings",
    },

    "eng": {
        "name": "🏴 الدوري الإنجليزي",
        "short": "الإنجليزي",
        "matches": "https://www.365scores.com/football/league/premier-league-7/matches",
        "standings": "https://www.365scores.com/football/league/premier-league-7/standings",
    },

    "fr": {
        "name": "🇫🇷 الدوري الفرنسي",
        "short": "الفرنسي",
        "matches": "https://www.365scores.com/football/league/ligue-1-35/matches",
        "standings": "https://www.365scores.com/football/league/ligue-1-35/standings",
    },
}


# =========================================================
# أسماء الفرق بالعربية
# =========================================================

TEAM_AR = {
    # الجزائر
    "MC Alger": "مولودية الجزائر",
    "MCA": "مولودية الجزائر",
    "CR Belouizdad": "شباب بلوزداد",
    "CRB": "شباب بلوزداد",
    "JS Kabylie": "شبيبة القبائل",
    "JSK": "شبيبة القبائل",
    "USM Alger": "اتحاد الجزائر",
    "USMA": "اتحاد الجزائر",
    "ES Sétif": "وفاق سطيف",
    "ES Setif": "وفاق سطيف",
    "ESS": "وفاق سطيف",
    "CS Constantine": "شباب قسنطينة",
    "CSC": "شباب قسنطينة",
    "Paradou AC": "بارادو",
    "PAC": "بارادو",
    "USM Khenchela": "اتحاد خنشلة",
    "USMK": "اتحاد خنشلة",
    "ASO Chlef": "جمعية الشلف",
    "ASO": "جمعية الشلف",
    "MC Oran": "مولودية وهران",
    "MCO": "مولودية وهران",
    "NC Magra": "نجم مقرة",
    "NCM": "نجم مقرة",
    "JS Saoura": "شبيبة الساورة",
    "JSS": "شبيبة الساورة",
    "US Biskra": "اتحاد بسكرة",
    "USB": "اتحاد بسكرة",
    "ES Mostaganem": "ترجي مستغانم",
    "ESM": "ترجي مستغانم",
    "Olympique Akbou": "أولمبيك أقبو",
    "OA": "أولمبيك أقبو",
    "Blida": "اتحاد البليدة",

    # England
    "Arsenal": "أرسنال",
    "Aston Villa": "أستون فيلا",
    "Bournemouth": "بورنموث",
    "Brentford": "برينتفورد",
    "Brighton": "برايتون",
    "Brighton & Hove Albion": "برايتون",
    "Burnley": "بيرنلي",
    "Chelsea": "تشيلسي",
    "Crystal Palace": "كريستال بالاس",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Leeds United": "ليدز يونايتد",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Newcastle United": "نيوكاسل",
    "Nottingham Forest": "نوتنغهام فورست",
    "Sunderland": "سندرلاند",
    "Tottenham Hotspur": "توتنهام",
    "West Ham United": "وست هام",
    "Wolverhampton": "وولفرهامبتون",
    "Wolverhampton Wanderers": "وولفرهامبتون",

    # France
    "Angers": "أنجيه",
    "Auxerre": "أوكسير",
    "Brest": "بريست",
    "Le Havre": "لو هافر",
    "Lens": "لانس",
    "Lille": "ليل",
    "Lorient": "لوريان",
    "Lyon": "ليون",
    "Marseille": "مارسيليا",
    "Metz": "ميتز",
    "Monaco": "موناكو",
    "Nantes": "نانت",
    "Nice": "نيس",
    "Paris Saint-Germain": "باريس سان جيرمان",
    "PSG": "باريس سان جيرمان",
    "Reims": "ريمس",
    "Rennes": "رين",
    "Saint-Etienne": "سانت إيتيان",
    "Strasbourg": "ستراسبورغ",
    "Toulouse": "تولوز",
}


# =========================================================
# قوة الفرق - تستخدم كنقطة بداية للتحليل
# =========================================================

TEAM_STRENGTH = {
    # England
    "Arsenal": 1.35,
    "Chelsea": 1.25,
    "Liverpool": 1.40,
    "Manchester City": 1.45,
    "Manchester United": 1.20,
    "Tottenham Hotspur": 1.15,
    "Newcastle United": 1.18,
    "Aston Villa": 1.15,
    "Brighton": 1.08,
    "Brighton & Hove Albion": 1.08,
    "Crystal Palace": 0.98,
    "West Ham United": 1.00,
    "Everton": 0.90,
    "Fulham": 0.95,
    "Brentford": 0.98,
    "Bournemouth": 0.92,
    "Wolverhampton": 0.90,
    "Wolverhampton Wanderers": 0.90,
    "Nottingham Forest": 0.95,
    "Leeds United": 0.90,
    "Burnley": 0.82,
    "Sunderland": 0.82,

    # France
    "Paris Saint-Germain": 1.45,
    "PSG": 1.45,
    "Marseille": 1.15,
    "Monaco": 1.18,
    "Lyon": 1.08,
    "Lille": 1.10,
    "Nice": 1.05,
    "Lens": 1.05,
    "Rennes": 1.00,
    "Strasbourg": 0.98,
    "Toulouse": 0.95,
    "Nantes": 0.90,
    "Brest": 0.95,
    "Montpellier": 0.88,
    "Auxerre": 0.85,
    "Angers": 0.84,
    "Metz": 0.82,
    "Le Havre": 0.82,
    "Lorient": 0.84,
    "Reims": 0.90,
    "Saint-Etienne": 0.88,

    # Algeria
    "MC Alger": 1.25,
    "MCA": 1.25,
    "CR Belouizdad": 1.18,
    "CRB": 1.18,
    "JS Kabylie": 1.12,
    "JSK": 1.12,
    "USM Alger": 1.12,
    "USMA": 1.12,
    "ES Sétif": 1.02,
    "ES Setif": 1.02,
    "ESS": 1.02,
    "CS Constantine": 1.00,
    "CSC": 1.00,
    "Paradou AC": 0.96,
    "PAC": 0.96,
    "USM Khenchela": 0.90,
    "USMK": 0.90,
    "ASO Chlef": 0.92,
    "ASO": 0.92,
    "MC Oran": 0.92,
    "MCO": 0.92,
    "NC Magra": 0.84,
    "NCM": 0.84,
    "JS Saoura": 0.94,
    "JSS": 0.94,
    "US Biskra": 0.82,
    "USB": 0.82,
    "ES Mostaganem": 0.82,
    "ESM": 0.82,
    "Olympique Akbou": 0.86,
    "OA": 0.86,
}


# =========================================================
# مستخدمون مصرح لهم
# =========================================================

authorized_users = set()


def authorized(chat_id):
    return chat_id in authorized_users


# =========================================================
# أدوات عامة
# =========================================================

def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def team_name(name):
    name = clean_text(name)

    if name in TEAM_AR:
        return TEAM_AR[name]

    # مطابقة مرنة
    low = name.lower()

    for original, arabic in TEAM_AR.items():
        if original.lower() == low:
            return arabic

    return name


def download_page(url):
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print("365Scores error:", e)
        return ""


def today_date():
    return datetime.now(TIMEZONE).date()


def today_formats():
    d = today_date()

    return {
        d.strftime("%d/%m/%Y"),
        d.strftime("%d/%m/%y"),
        d.strftime("%-d/%-m/%Y"),
        d.strftime("%-d/%-m/%y"),
    }


def normalize_date_text(text):
    text = clean_text(text)

    patterns = [
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",
        r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            try:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))

                return datetime(year, month, day).date()
            except Exception:
                pass

    return None


def is_known_team(name):
    name = clean_text(name)

    if name in TEAM_AR:
        return True

    low = name.lower()

    for team in TEAM_AR:
        if team.lower() == low:
            return True

    return False


# =========================================================
# استخراج مباريات 365Scores
# =========================================================

def get_page_lines(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)

    lines = []

    for line in text.splitlines():
        line = clean_text(line)

        if line:
            lines.append(line)

    return lines


def parse_match_line(line):
    line = clean_text(line)

    # مباراة منتهية
    match = re.match(
        r"^(.+?)\s+(?:Ended\s+)?(\d+)\s*[-:]\s*(\d+)\s+(.+?)$",
        line,
        re.IGNORECASE
    )

    if match:
        home = clean_text(match.group(1))
        home_score = int(match.group(2))
        away_score = int(match.group(3))
        away = clean_text(match.group(4))

        if is_known_team(home) or is_known_team(away):
            return {
                "home": home,
                "away": away,
                "time": None,
                "home_score": home_score,
                "away_score": away_score,
                "status": "ended",
            }

    # مباراة بوقت
    match = re.match(
        r"^(.+?)\s+(\d{1,2}:\d{2})\s+(.+?)$",
        line
    )

    if match:
        home = clean_text(match.group(1))
        match_time = match.group(2)
        away = clean_text(match.group(3))

        if is_known_team(home) or is_known_team(away):
            return {
                "home": home,
                "away": away,
                "time": match_time,
                "home_score": None,
                "away_score": None,
                "status": "scheduled",
            }

    return None


def get_matches(league_key):
    league = LEAGUES[league_key]
    html = download_page(league["matches"])

    if not html:
        return []

    lines = get_page_lines(html)

    matches = []
    current_date = None

    today = today_date()

    for line in lines:

        detected_date = normalize_date_text(line)

        if detected_date:
            current_date = detected_date
            continue

        parsed = parse_match_line(line)

        if not parsed:
            continue

        # إذا توفر تاريخ في الصفحة نتحقق من اليوم
        if current_date is not None and current_date != today:
            continue

        parsed["league"] = league_key
        parsed["date"] = today

        # منع التكرار
        duplicate = False

        for old in matches:
            if (
                old["home"] == parsed["home"]
                and old["away"] == parsed["away"]
                and old["time"] == parsed["time"]
            ):
                duplicate = True
                break

        if not duplicate:
            matches.append(parsed)

    return matches[:30]


# =========================================================
# ترتيب الدوري
# =========================================================

def parse_standing_line(line):
    line = clean_text(line)

    # مثال تقريبي:
    # 1 PSG 2 5:1 6 2 0 0 WW

    pattern = re.match(
        r"^(\d{1,2})\s+(.+?)\s+(\d+)\s+"
        r"(\d+):(\d+)\s+"
        r"(-?\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)\s+"
        r"(\d+)\s*"
        r"([WDL]+)?$",
        line,
        re.IGNORECASE
    )

    if not pattern:
        return None

    try:
        position = int(pattern.group(1))
        team = clean_text(pattern.group(2))
        played = int(pattern.group(3))
        gf = int(pattern.group(4))
        ga = int(pattern.group(5))
        gd = int(pattern.group(6))
        points = int(pattern.group(7))
        wins = int(pattern.group(8))
        draws = int(pattern.group(9))
        losses = int(pattern.group(10))
        form = pattern.group(11) or ""

        if not is_known_team(team):
            return None

        return {
            "position": position,
            "team": team,
            "played": played,
            "gf": gf,
            "ga": ga,
            "gd": gd,
            "points": points,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "form": form,
        }

    except Exception:
        return None


def get_standings(league_key):
    league = LEAGUES[league_key]
    html = download_page(league["standings"])

    if not html:
        return []

    lines = get_page_lines(html)

    standings = []

    for line in lines:
        row = parse_standing_line(line)

        if not row:
            continue

        duplicate = any(
            x["position"] == row["position"]
            and x["team"] == row["team"]
            for x in standings
        )

        if not duplicate:
            standings.append(row)

    standings.sort(key=lambda x: x["position"])

    return standings


# =========================================================
# نموذج Poisson
# =========================================================

def strength(team):
    if team in TEAM_STRENGTH:
        return TEAM_STRENGTH[team]

    low = team.lower()

    for name, value in TEAM_STRENGTH.items():
        if name.lower() == low:
            return value

    return 1.0


def poisson_probability(lam, k):
    if lam <= 0:
        return 0.0

    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def analyze(home, away):
    home_strength = strength(home)
    away_strength = strength(away)

    # أفضلية الأرض
    home_lambda = 1.35 * home_strength / max(away_strength, 0.50)
    away_lambda = 1.05 * away_strength / max(home_strength, 0.50)

    # نضع حدًا منطقيًا
    home_lambda = max(0.20, min(home_lambda, 4.00))
    away_lambda = max(0.20, min(away_lambda, 4.00))

    home_win = 0
    draw = 0
    away_win = 0

    score_probs = []

    for h in range(0, 8):
        for a in range(0, 8):

            probability = (
                poisson_probability(home_lambda, h)
                * poisson_probability(away_lambda, a)
            )

            score_probs.append((probability, h, a))

            if h > a:
                home_win += probability
            elif h == a:
                draw += probability
            else:
                away_win += probability

    # مجموع الأهداف
    under = {}
    over = {}

    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:

        under[line] = 0.0
        over[line] = 0.0

        for probability, h, a in score_probs:
            total = h + a

            if total < line:
                under[line] += probability
            else:
                over[line] += probability

    # BTTS
    btts_yes = 0
    btts_no = 0

    for probability, h, a in score_probs:

        if h >= 1 and a >= 1:
            btts_yes += probability
        else:
            btts_no += probability

    score_probs.sort(reverse=True)

    return {
        "home_lambda": home_lambda,
        "away_lambda": away_lambda,
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "under": under,
        "over": over,
        "btts_yes": btts_yes,
        "btts_no": btts_no,
        "scores": score_probs[:5],
    }


def percent(value):
    return round(value * 100, 1)


# =========================================================
# تحليل المباراة
# =========================================================

def analysis_message(match):
    home = match["home"]
    away = match["away"]

    result = analyze(home, away)

    home_ar = team_name(home)
    away_ar = team_name(away)

    text = (
        f"🧠 <b>تحليل المباراة</b>\n\n"
        f"⚽ <b>{home_ar}</b> × <b>{away_ar}</b>\n\n"
        f"📊 <b>احتمالات النتيجة</b>\n"
        f"🏠 فوز {home_ar}: <b>{percent(result['home_win'])}%</b>\n"
        f"🤝 التعادل: <b>{percent(result['draw'])}%</b>\n"
        f"✈️ فوز {away_ar}: <b>{percent(result['away_win'])}%</b>\n\n"
        f"⚽ <b>الأهداف المتوقعة</b>\n"
        f"🏠 {home_ar}: <b>{result['home_lambda']:.2f}</b>\n"
        f"✈️ {away_ar}: <b>{result['away_lambda']:.2f}</b>\n\n"
        f"📈 <b>Over / Under</b>\n"
    )

    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        text += (
            f"• {line}: "
            f"Over <b>{percent(result['over'][line])}%</b> | "
            f"Under <b>{percent(result['under'][line])}%</b>\n"
        )

    text += (
        f"\n🎯 <b>BTTS</b>\n"
        f"✅ نعم: <b>{percent(result['btts_yes'])}%</b>\n"
        f"❌ لا: <b>{percent(result['btts_no'])}%</b>\n\n"
        f"🔢 <b>أكثر النتائج احتمالًا</b>\n"
    )

    for probability, h, a in result["scores"]:
        text += f"• {h} - {a} : <b>{percent(probability)}%</b>\n"

    text += (
        "\n⚠️ <i>التحليل احتمالي باستخدام نموذج Poisson "
        "وليس نتيجة مضمونة.</i>"
    )

    return text


# =========================================================
# لوحة التحكم
# =========================================================

keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True
)

keyboard.row(
    "🇩🇿 مباريات الجزائر",
    "🏴 مباريات إنجلترا"
)

keyboard.row(
    "🇫🇷 مباريات فرنسا",
    "📊 ترتيب الجزائر"
)

keyboard.row(
    "📊 ترتيب إنجلترا",
    "📊 ترتيب فرنسا"
)

keyboard.row(
    "ℹ️ معلومات"
)


# =========================================================
# تنسيق المباريات
# =========================================================

def format_matches(matches, league_key):
    if not matches:
        return (
            f"{LEAGUES[league_key]['name']}\n\n"
            "📅 لا توجد مباريات اليوم حسب البيانات المتاحة من 365Scores."
        )

    text = (
        f"{LEAGUES[league_key]['name']}\n"
        f"📅 مباريات اليوم\n\n"
    )

    for i, match in enumerate(matches):

        home = team_name(match["home"])
        away = team_name(match["away"])

        if match["status"] == "ended":
            score = (
                f"{match['home_score']} - "
                f"{match['away_score']}"
            )

            text += (
                f"⚽ <b>{home}</b>  {score}  <b>{away}</b>\n"
            )

        else:
            text += (
                f"⚽ <b>{home}</b>  "
                f"⏰ {match['time']}  "
                f"<b>{away}</b>\n"
            )

        text += "\n"

    return text


def matches_keyboard(matches, league_key):
    markup = types.InlineKeyboardMarkup()

    for i, match in enumerate(matches):

        home = team_name(match["home"])
        away = team_name(match["away"])

        label = f"🧠 تحليل {home} × {away}"

        # Telegram callback data يجب ألا تكون كبيرة
        callback_data = f"analyze|{league_key}|{i}"

        markup.add(
            types.InlineKeyboardButton(
                label,
                callback_data=callback_data
            )
        )

    return markup


# =========================================================
# تنسيق الترتيب
# =========================================================

def format_standings(standings, league_key):
    if not standings:
        return (
            f"{LEAGUES[league_key]['name']}\n\n"
            "❌ تعذر استخراج جدول الترتيب من 365Scores حاليًا."
        )

    text = (
        f"{LEAGUES[league_key]['name']}\n"
        f"📊 <b>جدول الترتيب</b>\n\n"
    )

    text += (
        "<b># الفريق             لعب  نقاط  +/-</b>\n"
    )

    for row in standings:
        team = team_name(row["team"])

        text += (
            f"{row['position']:>2}. "
            f"{team} "
            f"{row['played']}  "
            f"{row['points']}  "
            f"{row['gd']:+d}\n"
        )

    return text


# =========================================================
# /start
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    authorized_users.discard(message.chat.id)

    bot.send_message(
        message.chat.id,
        "👋 <b>مرحبًا بك</b>\n\n"
        "⚽ بوت تحليل مباريات كرة القدم\n\n"
        "🔐 أدخل رمز الدخول للمتابعة:",
        parse_mode="HTML"
    )


# =========================================================
# كود الدخول
# =========================================================

@bot.message_handler(
    func=lambda message: (
        message.text
        and message.text.strip() == ACCESS_CODE
        and not authorized(message.chat.id)
    )
)
def access(message):
    authorized_users.add(message.chat.id)

    bot.send_message(
        message.chat.id,
        "✅ <b>تم التحقق بنجاح</b>\n\n"
        "اختر الدوري من القائمة 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# الأزرار
# =========================================================

@bot.message_handler(
    func=lambda message: (
        authorized(message.chat.id)
        and message.text
    )
)
def handle_buttons(message):

    text = message.text.strip()

    league_key = None
    action = None

    if text == "🇩🇿 مباريات الجزائر":
        league_key = "dz"
        action = "matches"

    elif text == "🏴 مباريات إنجلترا":
        league_key = "eng"
        action = "matches"

    elif text == "🇫🇷 مباريات فرنسا":
        league_key = "fr"
        action = "matches"

    elif text == "📊 ترتيب الجزائر":
        league_key = "dz"
        action = "standings"

    elif text == "📊 ترتيب إنجلترا":
        league_key = "eng"
        action = "standings"

    elif text == "📊 ترتيب فرنسا":
        league_key = "fr"
        action = "standings"

    elif text == "ℹ️ معلومات":
        bot.send_message(
            message.chat.id,
            "ℹ️ <b>معلومات البوت</b>\n\n"
            "⚽ الدوريات:\n"
            "🇩🇿 الدوري الجزائري\n"
            "🏴 الدوري الإنجليزي\n"
            "🇫🇷 الدوري الفرنسي\n\n"
            "📅 يعرض مباريات اليوم.\n"
            "📊 يعرض جدول الترتيب.\n"
            "🧠 يوفر تحليلًا احتماليًا باستخدام Poisson.\n\n"
            "❌ لا توجد خدمة LIVE في هذه النسخة.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    else:
        return

    bot.send_message(
        message.chat.id,
        "⏳ جاري جلب البيانات من 365Scores...",
        parse_mode="HTML"
    )

    if action == "matches":

        matches = get_matches(league_key)

        bot.send_message(
            message.chat.id,
            format_matches(matches, league_key),
            reply_markup=matches_keyboard(matches, league_key),
            parse_mode="HTML"
        )

    elif action == "standings":

        standings = get_standings(league_key)

        bot.send_message(
            message.chat.id,
            format_standings(standings, league_key),
            parse_mode="HTML"
        )


# =========================================================
# زر تحليل المباراة
# =========================================================

@bot.callback_query_handler(
    func=lambda call: (
        call.data
        and call.data.startswith("analyze|")
    )
)
def callback_analysis(call):

    if not authorized(call.message.chat.id):
        bot.answer_callback_query(
            call.id,
            "❌ يجب إدخال رمز الدخول أولًا."
        )
        return

    try:
        _, league_key, index_text = call.data.split("|")

        index = int(index_text)

        if league_key not in LEAGUES:
            raise ValueError("league")

        matches = get_matches(league_key)

        if index < 0 or index >= len(matches):
            bot.answer_callback_query(
                call.id,
                "❌ المباراة لم تعد متاحة."
            )
            return

        match = matches[index]

        bot.answer_callback_query(
            call.id,
            "🧠 جاري حساب التحليل..."
        )

        bot.send_message(
            call.message.chat.id,
            analysis_message(match),
            parse_mode="HTML"
        )

    except Exception as e:
        print("Analysis error:", e)

        bot.answer_callback_query(
            call.id,
            "❌ حدث خطأ أثناء التحليل."
        )


# =========================================================
# Webhook
# =========================================================

@app.route("/")
def home():
    return "Football Bot is running", 200


@app.route("/health")
def health():
    return "OK", 200


@app.route("/telegram/webhook", methods=["POST", "GET"])
def telegram_webhook():

    if request.method == "GET":
        return "Telegram webhook endpoint is active", 200

    try:
        json_string = request.get_data().decode("utf-8")

        update = telebot.types.Update.de_json(json_string)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:
        print("Webhook error:", e)
        return "ERROR", 500


@app.route("/webhook", methods=["POST", "GET"])
def webhook_alias():

    if request.method == "GET":
        return "Webhook endpoint is active", 200

    try:
        json_string = request.get_data().decode("utf-8")

        update = telebot.types.Update.de_json(json_string)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:
        print("Webhook error:", e)
        return "ERROR", 500


# =========================================================
# تشغيل محلي
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT
    )
