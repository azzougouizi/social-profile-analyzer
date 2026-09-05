import os
import re
import requests
from datetime import datetime
from flask import Flask, request
from bs4 import BeautifulSoup

# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ACCESS_CODE = "1230"

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# المستخدمون الذين أدخلوا الكود
authorized_users = set()


# =========================================================
# إرسال رسالة
# =========================================================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=20
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================================================
# القائمة الرئيسية
# =========================================================

def show_menu(chat_id):

    keyboard = {
        "keyboard": [
            ["📅 مباريات اليوم وتحليلها"],
            ["🏆 الفرق"],
            ["ℹ️ معلومات البوت"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🇩🇿⚽ اختر الخدمة:",
                "reply_markup": keyboard
            },
            timeout=20
        )
    except Exception as e:
        print("Keyboard error:", e)


# =========================================================
# المصدر
# =========================================================

SOURCE_URL = "https://www.footmercato.net/algerie/ligue-1/calendrier/"


# =========================================================
# جلب صفحة المباريات
# =========================================================

def get_page():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
    }

    response = requests.get(
        SOURCE_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# =========================================================
# تحويل أسماء الأيام الفرنسية
# =========================================================

DAYS_FR = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche"
}


MONTHS_FR = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre"
}


# =========================================================
# استخراج مباريات اليوم
# =========================================================

def get_today_matches():

    try:

        html = get_page()

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text("\n", strip=True)

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        now = datetime.now()

        today_day = now.day
        today_month = MONTHS_FR[now.month]
        today_year = now.year

        today_date_text = (
            f"{DAYS_FR[now.weekday()]} "
            f"{today_day} "
            f"{today_month} "
            f"{today_year}"
        )

        print("📅 تاريخ اليوم:", today_date_text)

        matches = []

        # -------------------------------------------------
        # نبحث عن عنوان تاريخ اليوم
        # -------------------------------------------------

        date_index = -1

        for i, line in enumerate(lines):

            normalized = line.lower()

            if (
                str(today_day) in normalized
                and today_month.lower() in normalized
                and str(today_year) in normalized
                and (
                    DAYS_FR[now.weekday()] in normalized
                )
            ):
                date_index = i
                break

        # -------------------------------------------------
        # إذا لم نجد التاريخ بالطريقة الأولى
        # -------------------------------------------------

        if date_index == -1:

            possible_dates = []

            for i, line in enumerate(lines):

                if (
                    str(today_day) in line
                    and today_month.lower() in line.lower()
                    and str(today_year) in line
                ):
                    possible_dates.append(i)

            if possible_dates:
                date_index = possible_dates[0]

        # -------------------------------------------------
        # إذا لم نجد تاريخ اليوم
        # -------------------------------------------------

        if date_index == -1:

            print("⚠️ لم يتم العثور على تاريخ اليوم")

            return []

        # -------------------------------------------------
        # أسماء أيام الأسبوع
        # -------------------------------------------------

        day_names = set(DAYS_FR.values())

        # -------------------------------------------------
        # نقرأ الأسطر التي بعد تاريخ اليوم
        # حتى تاريخ المباراة التالي
        # -------------------------------------------------

        block = []

        for line in lines[date_index + 1:]:

            lower = line.lower()

            # توقف عند تاريخ آخر
            if any(
                day in lower
                and str(today_year) in lower
                for day in day_names
            ):
                break

            block.append(line)

        print("📄 عدد الأسطر:", len(block))

        # -------------------------------------------------
        # أسماء الفرق المعروفة في Ligue 1
        # -------------------------------------------------

        team_keywords = [
            "Sétif",
            "Ben Aknoun",
            "Biar",
            "Akbou",
            "Khenchela",
            "USM Alger",
            "Kabylie",
            "Rouisset",
            "Témouchent",
            "Constantine",
            "Chlef",
            "Belouizdad",
            "Biskra",
            "Saoura",
            "MC Alger",
            "MC Oran",
            "Tlemcen",
            "Paradou"
        ]

        # -------------------------------------------------
        # البحث عن سطر المباراة
        # -------------------------------------------------

        i = 0

        while i < len(block):

            line = block[i]

            # وقت المباراة
            time_match = re.search(
                r"\b([01]?\d|2[0-3]):[0-5]\d\b",
                line
            )

            if time_match:

                time = time_match.group(0)

                # الفريق الأول غالبًا السطر السابق
                team1 = ""
                team2 = ""

                previous_lines = block[
                    max(0, i - 4):i
                ]

                candidates = []

                for x in previous_lines:

                    for team in team_keywords:

                        if team.lower() in x.lower():
                            candidates.append(x)

                # نحاول استخدام آخر اسمين
                if len(candidates) >= 2:

                    team1 = candidates[-2]
                    team2 = candidates[-1]

                # أحيانًا الفريقان يكونان في نفس السطر
                if not team1 or not team2:

                    if len(line.split()) >= 3:

                        # محاولة تقسيم بسيطة
                        parts = line.split(time)

                        if len(parts) == 2:

                            left = parts[0].strip()
                            right = parts[1].strip()

                            if left:
                                team1 = left

                            if right:
                                team2 = right

                if team1 and team2:

                    matches.append({
                        "home": clean_team(team1),
                        "away": clean_team(team2),
                        "time": time
                    })

            i += 1

        # -------------------------------------------------
        # إزالة التكرار
        # -------------------------------------------------

        unique = []

        seen = set()

        for match in matches:

            key = (
                match["home"],
                match["away"],
                match["time"]
            )

            if key not in seen:

                seen.add(key)

                unique.append(match)

        return unique

    except Exception as e:

        print("❌ Match scraping error:", e)

        return []


# =========================================================
# تنظيف اسم الفريق
# =========================================================

def clean_team(name):

    name = re.sub(
        r"\b(terminé|reporté|live)\b",
        "",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


# =========================================================
# تحويل أسماء الفرق إلى العربية
# =========================================================

TEAM_AR = {

    "Témouchent": "شباب عين تموشنت",
    "CS Constantine": "النادي الرياضي القسنطيني",
    "Constantine": "النادي الرياضي القسنطيني",

    "ASO Chlef": "أولمبي الشلف",
    "Chlef": "أولمبي الشلف",

    "Belouizdad": "شباب بلوزداد",
    "CR Belouizdad": "شباب بلوزداد",

    "Khenchela": "اتحاد خنشلة",
    "USM Alger": "اتحاد العاصمة",

    "Kabylie": "شبيبة القبائل",
    "Rouisset": "مستقبل الرويسات",

    "ES Sétif": "وفاق سطيف",
    "Sétif": "وفاق سطيف",

    "Ben Aknoun": "نجم بن عكنون",
    "Biar": "شبيبة الأبيار",

    "Akbou": "أولمبي أقبو",
    "Biskra": "اتحاد بسكرة",
    "Saoura": "شبيبة الساورة",

    "MC Alger": "مولودية الجزائر",
    "MC Oran": "مولودية وهران"
}


def arabic_team(name):

    for key, value in TEAM_AR.items():

        if key.lower() in name.lower():
            return value

    return name


# =========================================================
# تحليل المباراة
# =========================================================

def analyze_match(home, away):

    home_ar = arabic_team(home)
    away_ar = arabic_team(away)

    # -----------------------------------------------------
    # تحليل مبدئي
    # لا ندعي أنها إحصائيات رسمية
    # -----------------------------------------------------

    strong_teams = [
        "مولودية الجزائر",
        "شباب بلوزداد",
        "اتحاد العاصمة",
        "شبيبة القبائل"
    ]

    home_score = 33
    away_score = 33
    draw_score = 34

    if home_ar in strong_teams:
        home_score += 7
        away_score -= 3
        draw_score -= 4

    if away_ar in strong_teams:
        away_score += 7
        home_score -= 3
        draw_score -= 4

    # أفضلية الملعب
    home_score += 5
    draw_score -= 2
    away_score -= 3

    # ضبط النسب
    total = home_score + draw_score + away_score

    home_probability = round(
        home_score / total * 100
    )

    draw_probability = round(
        draw_score / total * 100
    )

    away_probability = 100 - home_probability - draw_probability

    if home_probability >= away_probability:
        expected = f"أفضلية {home_ar}"
    else:
        expected = f"أفضلية {away_ar}"

    return (
        f"📊 <b>تحليل المباراة</b>\n\n"
        f"🏠 <b>{home_ar}</b>\n"
        f"🆚\n"
        f"🚩 <b>{away_ar}</b>\n\n"

        f"📈 <b>الاحتمالات التقديرية:</b>\n"
        f"🏠 فوز {home_ar}: {home_probability}%\n"
        f"🤝 التعادل: {draw_probability}%\n"
        f"🚩 فوز {away_ar}: {away_probability}%\n\n"

        f"🎯 <b>الترجيح:</b>\n"
        f"{expected}\n\n"

        f"⚠️ التحليل تقديري وليس ضمانًا للنتيجة."
    )


# =========================================================
# عرض مباريات اليوم
# =========================================================

def show_today_matches(chat_id):

    matches = get_today_matches()

    now = datetime.now()

    date_text = (
        f"{now.day} "
        f"{MONTHS_FR[now.month]} "
        f"{now.year}"
    )

    if not matches:

        send_message(
            chat_id,
            f"📅 <b>مباريات اليوم</b>\n\n"
            f"📆 {date_text}\n\n"
            f"⚽ لا توجد مباريات تمكنت من العثور عليها اليوم.\n\n"
            f"🔄 حاول مرة أخرى بعد قليل."
        )

        return

    message = (
        f"🇩🇿 <b>مباريات الدوري الجزائري اليوم</b>\n"
        f"📆 {date_text}\n\n"
    )

    for index, match in enumerate(matches, 1):

        home = arabic_team(match["home"])
        away = arabic_team(match["away"])
        time = match["time"]

        message += (
            f"━━━━━━━━━━━━━━\n"
            f"⚽ <b>المباراة {index}</b>\n\n"
            f"🏠 {home}\n"
            f"🆚\n"
            f"🚩 {away}\n\n"
            f"🕐 الساعة: <b>{time}</b>\n\n"
        )

        message += analyze_match(
            match["home"],
            match["away"]
        )

        message += "\n\n"

    message += (
        "━━━━━━━━━━━━━━\n"
        "📌 يتم تحديد مباريات اليوم تلقائيًا حسب التاريخ الحالي.\n"
        "⚠️ التحليل تقديري."
    )

    # Telegram لديه حد للرسائل
    if len(message) > 4000:

        parts = []

        current = ""

        for section in message.split(
            "━━━━━━━━━━━━━━"
        ):

            if len(current) + len(section) > 3500:

                parts.append(current)

                current = section

            else:

                current += section

        if current:
            parts.append(current)

        for part in parts:
            send_message(chat_id, part)

    else:

        send_message(chat_id, message)


# =========================================================
# الفرق
# =========================================================

def show_teams(chat_id):

    message = """
🇩🇿 <b>أندية الدوري الجزائري</b>

• مولودية الجزائر
• شباب بلوزداد
• اتحاد العاصمة
• شبيبة القبائل
• وفاق سطيف
• مولودية وهران
• شبيبة الساورة
• النادي الرياضي القسنطيني
• أولمبي الشلف
• اتحاد خنشلة
• اتحاد بسكرة
• أولمبي أقبو
• نجم بن عكنون
• شبيبة الأبيار
• مستقبل الرويسات
• شباب عين تموشنت

"""

    send_message(chat_id, message)


# =========================================================
# معلومات
# =========================================================

def show_info(chat_id):

    message = """
ℹ️ <b>معلومات البوت</b>

🇩🇿 بوت الدوري الجزائري

📅 زر مباريات اليوم:
يعرض مباريات اليوم تلقائيًا حسب التاريخ.

📊 كل مباراة تحصل على تحليل تقديري.

🔐 كود الدخول:
1230

🌐 لا يحتاج إلى Football API Key.

⚠️ التحليلات تقديرية وليست ضمانًا للنتائج.
"""

    send_message(chat_id, message)


# =========================================================
# Webhook
# =========================================================

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    try:

        data = request.get_json(force=True)

        message = data.get("message", {})

        chat = message.get("chat", {})

        chat_id = chat.get("id")

        text = message.get("text", "")

        if not chat_id:
            return "OK", 200

        text = text.strip()

        # -------------------------------------------------
        # التحقق من الكود
        # -------------------------------------------------

        if chat_id not in authorized_users:

            if text == ACCESS_CODE:

                authorized_users.add(chat_id)

                send_message(
                    chat_id,
                    "✅ <b>تم الدخول بنجاح</b>\n\n"
                    "🇩🇿 مرحبًا بك في بوت الدوري الجزائري ⚽"
                )

                show_menu(chat_id)

            else:

                send_message(
                    chat_id,
                    "🔐 <b>أدخل كود الدخول:</b>\n\n"
                    "أرسل الكود للمتابعة."
                )

            return "OK", 200

        # -------------------------------------------------
        # /start
        # -------------------------------------------------

        if text == "/start":

            show_menu(chat_id)

        # -------------------------------------------------
        # مباريات اليوم
        # -------------------------------------------------

        elif text == "📅 مباريات اليوم وتحليلها":

            show_today_matches(chat_id)

        # -------------------------------------------------
        # الفرق
        # -------------------------------------------------

        elif text == "🏆 الفرق":

            show_teams(chat_id)

        # -------------------------------------------------
        # المعلومات
        # -------------------------------------------------

        elif text == "ℹ️ معلومات البوت":

            show_info(chat_id)

        else:

            send_message(
                chat_id,
                "اختر إحدى الخدمات من القائمة 👇"
            )

        return "OK", 200

    except Exception as e:

        print("❌ Webhook error:", e)

        return "OK", 200


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def home():

    return "Algerian Football Bot 🇩🇿⚽"


@app.route("/health")
def health():

    return "OK"


# =========================================================
# تشغيل التطبيق
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
