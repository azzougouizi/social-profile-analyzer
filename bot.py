import os
import re
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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()

PORT = int(os.getenv("PORT", "10000"))
ACCESS_CODE = "1230"

TIMEZONE = ZoneInfo("Africa/Algiers")

PREMIER_LEAGUE_URL = (
    "https://www.premierleague.com/en/news/"
    "4675097/all-380-fixtures-for-202627-premier-league-season"
)

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY غير موجود")


bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

app = Flask(__name__)

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
})


# =========================================================
# TEAMS
# =========================================================

TEAM_AR = {
    "Arsenal": "أرسنال",
    "Aston Villa": "أستون فيلا",
    "AFC Bournemouth": "بورنموث",
    "Bournemouth": "بورنموث",
    "Brentford": "برينتفورد",
    "Brighton & Hove Albion": "برايتون",
    "Chelsea": "تشيلسي",
    "Crystal Palace": "كريستال بالاس",
    "Coventry City": "كوفنتري سيتي",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Hull City": "هال سيتي",
    "Ipswich Town": "إيبسويتش تاون",
    "Leeds United": "ليدز يونايتد",
    "Liverpool": "ليفربول",
    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Newcastle United": "نيوكاسل يونايتد",
    "Nottingham Forest": "نوتنغهام فورست",
    "Sunderland": "سندرلاند",
    "Tottenham Hotspur": "توتنهام",
}


TEAM_NAMES = sorted(
    TEAM_AR.keys(),
    key=len,
    reverse=True
)


# =========================================================
# USERS
# =========================================================

authorized_users = set()


# =========================================================
# HELPERS
# =========================================================

def clean(text):
    return " ".join(
        str(text).replace("\xa0", " ").split()
    )


def arabic_team(name):
    return TEAM_AR.get(
        name.strip(),
        name.strip()
    )


def current_date():
    return datetime.now(TIMEZONE).date()


def find_team(text):
    text_lower = text.lower()

    for team in TEAM_NAMES:
        if team.lower() in text_lower:
            return team

    return None


# =========================================================
# GET PREMIER LEAGUE FIXTURES
# =========================================================

def get_fixture_page():

    try:

        response = session.get(
            PREMIER_LEAGUE_URL,
            timeout=25
        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        print("Premier League error:", e)

        return ""


def get_today_matches():

    html = get_fixture_page()

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg"
    ]):
        tag.decompose()

    lines = []

    for line in soup.get_text("\n").splitlines():

        line = clean(line)

        if line:
            lines.append(line)

    today = current_date()

    # مثال:
    # Friday 21 August 2026
    # Saturday 22 August
    date_pattern = re.compile(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
        r"\s+(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"(?:\s+(\d{4}))?$",
        re.IGNORECASE
    )

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    active_date = None
    matches = []

    for line in lines:

        date_match = date_pattern.match(line)

        if date_match:

            day = int(date_match.group(2))

            month_name = date_match.group(3).lower()

            month = months[month_name]

            year_text = date_match.group(4)

            if year_text:

                year = int(year_text)

            else:

                # موسم 2026/27
                year = 2026 if month >= 8 else 2027

            try:

                active_date = datetime(
                    year,
                    month,
                    day
                ).date()

            except ValueError:

                active_date = None

            continue

        if active_date != today:
            continue

        # =================================================
        # Match line
        #
        # 14:00 Everton v Manchester United (Sky Sports)
        # Arsenal v Chelsea
        # =================================================

        if " v " not in line:
            continue

        time_match = re.match(
            r"^(\d{1,2}:\d{2})\s+(.+?)\s+v\s+(.+)$",
            line
        )

        if time_match:

            kickoff = time_match.group(1)

            home_text = time_match.group(2)

            away_text = time_match.group(3)

        else:

            kickoff = "15:00"

            parts = line.split(" v ", 1)

            if len(parts) != 2:
                continue

            home_text = parts[0]

            away_text = parts[1]

        # إزالة القناة
        away_text = re.sub(
            r"\s*.*?",
            "",
            away_text
        )

        home = find_team(home_text)
        away = find_team(away_text)

        if not home or not away:
            continue

        match = {
            "home": home,
            "away": away,
            "time": kickoff
        }

        duplicate = any(
            m["home"] == match["home"]
            and m["away"] == match["away"]
            for m in matches
        )

        if not duplicate:
            matches.append(match)

    return matches


# =========================================================
# DEEPSEEK ANALYSIS
# =========================================================

def analyze_match(home, away):

    home_ar = arabic_team(home)
    away_ar = arabic_team(away)

    prompt = f"""
أنت محلل كرة قدم محترف.

حلل مباراة في الدوري الإنجليزي الممتاز:

{home_ar} ضد {away_ar}

أريد تحليلاً مختصرًا وواضحًا باللغة العربية.

أعطني:

1. الفريق الأقرب للفوز
2. النتيجة المتوقعة
3. احتمال فوز صاحب الأرض بالنسبة المئوية
4. احتمال التعادل بالنسبة المئوية
5. احتمال فوز الضيف بالنسبة المئوية
6. Over 1.5
7. Over 2.5
8. Over 3.5
9. BTTS
10. شرح مختصر جدًا للتحليل

مهم جدًا:
- لا تدّعي امتلاك بيانات مباشرة أو نتائج حية إذا لم تكن متاحة.
- لا تخترع إصابات أو إيقافات أو أرقامًا حديثة.
- اعتبر التوقع احتماليًا وليس ضمانًا.
- اجعل الإجابة سهلة للعرض داخل Telegram.
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-v4-flash",

        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت محلل كرة قدم. "
                    "أجب باللغة العربية وبشكل مختصر."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.3,

        "max_tokens": 700
    }

    try:

        response = requests.post(
            DEEPSEEK_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:

        print("DeepSeek error:", e)

        return (
            "❌ تعذر الحصول على تحليل DeepSeek حاليًا.\n"
            "حاول مرة أخرى بعد قليل."
        )


# =========================================================
# KEYBOARDS
# =========================================================

main_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True
)

main_keyboard.add(
    types.KeyboardButton(
        "🏴 مباريات اليوم"
    )
)


def matches_keyboard(matches):

    keyboard = types.InlineKeyboardMarkup()

    for index, match in enumerate(matches):

        home = arabic_team(match["home"])
        away = arabic_team(match["away"])

        keyboard.add(
            types.InlineKeyboardButton(
                text=f"🤖 {home} × {away}",
                callback_data=f"analyze_{index}"
            )
        )

    return keyboard


# =========================================================
# START
# =========================================================

@bot.message_handler(
    commands=["start"]
)
def start(message):

    authorized_users.discard(
        message.chat.id
    )

    bot.send_message(
        message.chat.id,

        "👋 <b>مرحبًا بك</b>\n\n"
        "🏴 <b>Premier League AI Bot</b>\n\n"
        "يعرض مباريات الدوري الإنجليزي اليوم "
        "ويمكنك طلب تحليل المباراة بواسطة DeepSeek.\n\n"
        "🔐 أدخل رمز الدخول:",

        parse_mode="HTML"
    )


# =========================================================
# LOGIN
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text
    and message.text.strip() == ACCESS_CODE
    and message.chat.id not in authorized_users
)
def login(message):

    authorized_users.add(
        message.chat.id
    )

    bot.send_message(
        message.chat.id,

        "✅ <b>تم الدخول بنجاح</b>\n\n"
        "اختر مباريات اليوم:",

        reply_markup=main_keyboard
    )


# =========================================================
# TODAY'S MATCHES
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.chat.id in authorized_users
    and message.text == "🏴 مباريات اليوم"
)
def today_matches(message):

    bot.send_message(
        message.chat.id,
        "⏳ جاري جلب مباريات اليوم..."
    )

    matches = get_today_matches()

    if not matches:

        bot.send_message(
            message.chat.id,

            "📅 <b>مباريات اليوم</b>\n\n"
            "لا توجد مباريات في الدوري الإنجليزي اليوم "
            "أو تعذر قراءة جدول Premier League حاليًا.",

            reply_markup=main_keyboard
        )

        return

    text = (
        "🏴 <b>الدوري الإنجليزي الممتاز</b>\n"
        "📅 <b>مباريات اليوم</b>\n\n"
    )

    for match in matches:

        home = arabic_team(
            match["home"]
        )

        away = arabic_team(
            match["away"]
        )

        text += (
            f"⚽ <b>{home}</b> × <b>{away}</b>\n"
            f"🕐 {match['time']} الجزائر\n\n"
        )

    text += (
        "👇 اختر مباراة للحصول على تحليل DeepSeek:"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=matches_keyboard(matches)
    )


# =========================================================
# ANALYZE BUTTON
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("analyze_")
)
def analyze_button(call):

    try:

        index = int(
            call.data.replace(
                "analyze_",
                ""
            )
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "خطأ"
        )

        return

    matches = get_today_matches()

    if index >= len(matches):

        bot.answer_callback_query(
            call.id,
            "المباراة غير متاحة"
        )

        return

    match = matches[index]

    home = arabic_team(
        match["home"]
    )

    away = arabic_team(
        match["away"]
    )

    bot.answer_callback_query(
        call.id,
        "جاري التحليل..."
    )

    bot.send_message(
        call.message.chat.id,

        f"🤖 <b>DeepSeek AI</b>\n\n"
        f"⚽ <b>{home} × {away}</b>\n\n"
        f"⏳ جاري تحليل المباراة..."
    )

    analysis = analyze_match(
        match["home"],
        match["away"]
    )

    result = (
        f"🤖 <b>تحليل DeepSeek</b>\n\n"
        f"⚽ <b>{home} × {away}</b>\n"
        f"🕐 {match['time']} الجزائر\n\n"
        f"{analysis}\n\n"
        f"⚠️ التوقعات احتمالية وليست ضمانًا."
    )

    bot.send_message(
        call.message.chat.id,
        result,
        reply_markup=main_keyboard
    )


# =========================================================
# FLASK
# =========================================================

@app.route("/")
def home():

    return "Premier League AI Bot is running", 200


@app.route("/health")
def health():

    return "OK", 200


# =========================================================
# TELEGRAM WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST", "GET"]
)
def telegram_webhook():

    if request.method == "GET":
        return "Webhook is active", 200

    try:

        data = request.get_data().decode(
            "utf-8"
        )

        update = telebot.types.Update.de_json(
            data
        )

        bot.process_new_updates(
            [update]
        )

        return "OK", 200

    except Exception as e:

        print(
            "Webhook error:",
            e
        )

        return "ERROR", 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )
