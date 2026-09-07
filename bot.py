import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import telebot
from telebot import types


# =========================
# إعدادات
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))

ACCESS_CODE = "1230"

TIMEZONE = ZoneInfo("Africa/Algiers")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود")


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


# =========================
# 365Scores
# =========================

MATCHES_URL = (
    "https://www.365scores.com/football/league/"
    "premier-league-7/matches"
)


# =========================
# أسماء الفرق
# =========================

TEAM_AR = {
    "Arsenal": "أرسنال",
    "Arsenal FC": "أرسنال",

    "Aston Villa": "أستون فيلا",
    "Aston Villa FC": "أستون فيلا",

    "Bournemouth": "بورنموث",
    "AFC Bournemouth": "بورنموث",

    "Brentford": "برينتفورد",
    "Brentford FC": "برينتفورد",

    "Brighton": "برايتون",
    "Brighton & Hove Albion": "برايتون",
    "Brighton & Hove Albion FC": "برايتون",

    "Burnley": "بيرنلي",
    "Burnley FC": "بيرنلي",

    "Chelsea": "تشيلسي",
    "Chelsea FC": "تشيلسي",

    "Crystal Palace": "كريستال بالاس",
    "Crystal Palace FC": "كريستال بالاس",

    "Everton": "إيفرتون",
    "Everton FC": "إيفرتون",

    "Fulham": "فولهام",
    "Fulham FC": "فولهام",

    "Leeds United": "ليدز يونايتد",
    "Leeds United FC": "ليدز يونايتد",

    "Liverpool": "ليفربول",
    "Liverpool FC": "ليفربول",

    "Manchester City": "مانشستر سيتي",
    "Manchester City FC": "مانشستر سيتي",

    "Manchester United": "مانشستر يونايتد",
    "Manchester United FC": "مانشستر يونايتد",

    "Newcastle United": "نيوكاسل",
    "Newcastle United FC": "نيوكاسل",

    "Nottingham Forest": "نوتنغهام فورست",
    "Nottingham Forest FC": "نوتنغهام فورست",

    "Sunderland": "سندرلاند",
    "Sunderland AFC": "سندرلاند",

    "Tottenham Hotspur": "توتنهام",
    "Tottenham Hotspur FC": "توتنهام",

    "West Ham United": "وست هام",
    "West Ham United FC": "وست هام",

    "Wolverhampton Wanderers": "وولفرهامبتون",
    "Wolverhampton Wanderers FC": "وولفرهامبتون",
}


# =========================
# المستخدمون
# =========================

authorized_users = set()


# =========================
# أدوات
# =========================

def clean(text):
    if not text:
        return ""

    return " ".join(
        str(text)
        .replace("\xa0", " ")
        .split()
    )


def arabic_team(name):
    name = clean(name)

    if name in TEAM_AR:
        return TEAM_AR[name]

    return name


def known_team(name):
    name = clean(name).lower()

    for team in TEAM_AR:
        if team.lower() == name:
            return True

    return False


def today():
    return datetime.now(TIMEZONE).date()


# =========================
# تحميل الصفحة
# =========================

def get_page():

    try:

        response = session.get(
            MATCHES_URL,
            timeout=20
        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        print("365Scores error:", e)

        return ""


# =========================
# استخراج مباريات اليوم
# =========================

def get_today_matches():

    html = get_page()

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # إزالة الأشياء غير المهمة
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg"
    ]):
        tag.decompose()

    text = soup.get_text(
        "\n",
        strip=True
    )

    lines = [
        clean(line)
        for line in text.splitlines()
        if clean(line)
    ]

    matches = []

    today_date = today()

    # تواريخ محتملة في الصفحة
    today_strings = {
        today_date.strftime("%d/%m/%Y"),
        today_date.strftime("%d/%m/%y"),
        today_date.strftime("%-d/%-m/%Y"),
        today_date.strftime("%-d/%-m/%y"),
    }

    found_today = False

    for line in lines:

        # معرفة بداية مباريات اليوم
        if any(
            date_string in line
            for date_string in today_strings
        ):
            found_today = True
            continue

        if not found_today:
            continue

        # إذا وصلنا إلى تاريخ آخر نتوقف
        if "/" in line:

            possible_date = False

            for part in line.split():
                if "/" in part:
                    possible_date = True
                    break

            if possible_date:
                continue

        # -------------------------
        # مباراة بوقت
        # -------------------------

        parts = line.split()

        for i, part in enumerate(parts):

            if ":" not in part:
                continue

            # نبحث عن وقت مثل 15:00
            time_part = part

            try:

                hour, minute = time_part.split(":")

                if not (
                    hour.isdigit()
                    and minute.isdigit()
                ):
                    continue

                if not (
                    0 <= int(hour) <= 23
                    and 0 <= int(minute) <= 59
                ):
                    continue

            except Exception:
                continue

            left = clean(
                " ".join(parts[:i])
            )

            right = clean(
                " ".join(parts[i + 1:])
            )

            if not left or not right:
                continue

            # محاولة العثور على فريق معروف
            home = None
            away = None

            for team in TEAM_AR:

                if team.lower() in left.lower():
                    home = team

                if team.lower() in right.lower():
                    away = team

            if home and away:

                item = {
                    "home": home,
                    "away": away,
                    "time": time_part
                }

                duplicate = any(
                    m["home"] == home
                    and m["away"] == away
                    and m["time"] == time_part
                    for m in matches
                )

                if not duplicate:
                    matches.append(item)

                break

    return matches


# =========================
# لوحة التحكم
# =========================

keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True
)

keyboard.add(
    types.KeyboardButton(
        "🏴 مباريات اليوم"
    )
)


# =========================
# START
# =========================

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
        "🏴 <b>Premier League Bot</b>\n\n"
        "📅 يعرض مباريات الدوري الإنجليزي "
        "المقررة اليوم.\n\n"
        "🔐 أدخل رمز الدخول:",

        parse_mode="HTML"
    )


# =========================
# كود الدخول
# =========================

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
        "اضغط على الزر لعرض مباريات اليوم:",

        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# مباريات اليوم
# =========================

@bot.message_handler(
    func=lambda message:
    message.chat.id in authorized_users
    and message.text == "🏴 مباريات اليوم"
)
def matches_today(message):

    bot.send_message(
        message.chat.id,
        "⏳ جاري جلب مباريات اليوم..."
    )

    matches = get_today_matches()

    if not matches:

        bot.send_message(
            message.chat.id,

            "📅 <b>مباريات الدوري الإنجليزي اليوم</b>\n\n"
            "لا توجد مباريات اليوم "
            "أو تعذر قراءة بيانات 365Scores حاليًا.",

            reply_markup=keyboard,
            parse_mode="HTML"
        )

        return

    text = (
        "🏴 <b>الدوري الإنجليزي</b>\n"
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
            f"⚽ <b>{home}</b>\n"
            f"🕐 {match['time']}\n"
            f"🆚 <b>{away}</b>\n\n"
        )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# الصفحة الرئيسية
# =========================

@app.route("/")
def home():

    return "Premier League Bot is running", 200


# =========================
# Health
# =========================

@app.route("/health")
def health():

    return "OK", 200


# =========================
# Telegram Webhook
# =========================

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


# =========================
# تشغيل
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )
