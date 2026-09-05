import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

# =========================================================
# إعدادات
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# كود الدخول الموحد
ACCESS_CODE = "1230"

app = Flask(__name__)

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# المستخدمون الذين أدخلوا الكود
authorized_users = set()


# =========================================================
# Telegram
# =========================================================

def send_message(chat_id, text):
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود")
        return

    try:
        requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=20
        )
    except Exception as e:
        print("Telegram error:", e)


def send_keyboard(chat_id):
    keyboard = {
        "keyboard": [
            ["🇩🇿 الدوري الجزائري"],
            ["📅 مباريات اليوم", "🏆 الفرق"],
            ["📊 تحليل مباراة"],
            ["ℹ️ معلومات البوت"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "اختر الخدمة التي تريدها 👇",
                "reply_markup": keyboard
            },
            timeout=20
        )
    except Exception as e:
        print("Keyboard error:", e)


# =========================================================
# جلب الدوري الجزائري Ligue 1
# =========================================================

LIGUE1_URL = "https://www.footmercato.net/algerie/ligue-1/calendrier/"


def get_ligue1_matches():
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        }

        response = requests.get(
            LIGUE1_URL,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            print("❌ FootMercato:", response.status_code)
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # نحصل على النص الظاهر
        text = soup.get_text("\n", strip=True)

        matches = []

        # أسماء أندية الدوري الجزائري
        teams = [
            "ES Sétif",
            "Ben Aknoun",
            "Biar",
            "Akbou",
            "Khenchela",
            "USM Alger",
            "Kabylie",
            "Rouisset",
            "Témouchent",
            "CS Constantine",
            "ASO Chlef",
            "Belouizdad",
            "US Biskra",
            "Saoura",
            "MC Alger",
            "MC Oran",
            "JS Kabylie",
            "Paradou",
            "MCA",
            "USMA",
            "CR Belouizdad",
            "Chlef"
        ]

        lines = [x.strip() for x in text.split("\n") if x.strip()]

        # نحاول استخراج الأسطر التي تحتوي على فريقين
        for i, line in enumerate(lines):
            found = []

            for team in teams:
                if team.lower() in line.lower():
                    found.append(team)

            if len(found) >= 2:
                matches.append(line)

        # إزالة التكرار
        unique = []
        seen = set()

        for m in matches:
            key = m.lower()
            if key not in seen:
                seen.add(key)
                unique.append(m)

        return unique[:30]

    except Exception as e:
        print("❌ Ligue 1 error:", e)
        return []


# =========================================================
# Ligue 2
# =========================================================

LIGUE2_URL = (
    "https://competition.dz/chrono/"
    "ligue-2-les-calendriers-des-groupes-centre-est-et-centre-ouest-devoiles.html"
)


def get_ligue2_schedule():
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        }

        response = requests.get(
            LIGUE2_URL,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            print("❌ Competition DZ:", response.status_code)
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text("\n", strip=True)

        # نبحث عن بداية المجموعة
        start = text.find("Groupe Centre-Est")

        if start == -1:
            start = text.find("Centre-Est")

        if start == -1:
            return "لم أستطع قراءة جدول Ligue 2 حاليًا."

        content = text[start:]

        # نأخذ جزءًا معقولًا
        return content[:7000]

    except Exception as e:
        print("❌ Ligue 2 error:", e)
        return ""


# =========================================================
# الدوري الجزائري
# =========================================================

def show_ligue1(chat_id):
    matches = get_ligue1_matches()

    if not matches:
        send_message(
            chat_id,
            "⚠️ لم أتمكن من قراءة مباريات الدوري الجزائري حاليًا.\n"
            "حاول مرة أخرى بعد قليل."
        )
        return

    message = "🇩🇿 <b>الدوري الجزائري - Ligue 1</b>\n\n"

    for match in matches[:15]:
        message += f"⚽ {match}\n"

    message += (
        "\n\n📌 المصدر: Foot Mercato\n"
        "ℹ️ البيانات مأخوذة من صفحة عامة على الويب، "
        "وليست API مدفوعة."
    )

    send_message(chat_id, message)


# =========================================================
# مباريات اليوم
# =========================================================

def show_today(chat_id):
    matches = get_ligue1_matches()

    if not matches:
        send_message(
            chat_id,
            "⚠️ لا أستطيع الحصول على مباريات اليوم حاليًا."
        )
        return

    message = "📅 <b>مباريات الدوري الجزائري</b>\n\n"

    for match in matches[:10]:
        message += f"⚽ {match}\n"

    message += (
        "\n\n🔄 يتم جلب البيانات من صفحة ويب عامة."
    )

    send_message(chat_id, message)


# =========================================================
# الفرق
# =========================================================

def show_teams(chat_id):
    message = """
🇩🇿 <b>أندية الدوري الجزائري</b>

🔴 مولودية الجزائر
🟢 شبيبة القبائل
🔴 اتحاد العاصمة
🔴 شباب بلوزداد
🟢 وفاق سطيف
🟡 شبيبة الساورة
🔴 مولودية وهران
🟢 النادي الرياضي القسنطيني
🔵 اتحاد بسكرة
🟢 أولمبي الشلف
🔴 اتحاد خنشلة
🟢 أكبو
🔵 بن عكنون
🔴 تيموشنت
🟢 البيار
🔵 رويسات

📌 القائمة قد تتغير حسب الموسم.
"""

    send_message(chat_id, message)


# =========================================================
# تحليل مباراة
# =========================================================

def analyze_match(chat_id):
    message = """
📊 <b>تحليل مباراة</b>

أرسل لي المباراة بهذا الشكل:

<code>مولودية الجزائر - مولودية وهران</code>

وسأعطيك تحليلًا مبسطًا يشمل:

⚽ الفريق الأقوى
🏠 أفضلية الأرض
📈 التوقع التقريبي
🥅 الأهداف المتوقعة
📊 احتمال الفوز/التعادل/الخسارة

⚠️ التحليل إحصائي وترفيهي وليس ضمانًا للنتيجة.
"""

    send_message(chat_id, message)


# =========================================================
# معلومات
# =========================================================

def show_info(chat_id):
    message = """
ℹ️ <b>معلومات البوت</b>

🇩🇿 بوت خاص بالكرة الجزائرية

يدعم:
• الدوري الجزائري Ligue 1
• Ligue 2
• المباريات
• الفرق
• تحليل المباريات

🔐 كود الدخول:
1230

🌐 لا يحتاج إلى Football API Key.

📌 يتم جلب بعض البيانات من صفحات ويب عامة.
"""

    send_message(chat_id, message)


# =========================================================
# استقبال رسائل Telegram
# =========================================================

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    try:
        data = request.get_json(force=True)

        message = data.get("message", {})

        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if not chat_id:
            return "OK", 200

        text = message.get("text", "")
        text = text.strip()

        # ---------------------------------------------
        # إدخال كود الدخول
        # ---------------------------------------------

        if chat_id not in authorized_users:

            if text == ACCESS_CODE:

                authorized_users.add(chat_id)

                send_message(
                    chat_id,
                    "✅ <b>تم قبول الكود!</b>\n\n"
                    "مرحبًا بك في بوت الكرة الجزائرية 🇩🇿⚽"
                )

                send_keyboard(chat_id)

            else:

                send_message(
                    chat_id,
                    "🔐 <b>البوت مغلق.</b>\n\n"
                    "أرسل كود الدخول للمتابعة."
                )

            return "OK", 200

        # ---------------------------------------------
        # الأوامر بعد الدخول
        # ---------------------------------------------

        if text == "/start":

            send_message(
                chat_id,
                "أهلًا بك 🇩🇿⚽\n"
                "اختر الخدمة:"
            )

            send_keyboard(chat_id)

        elif text == "🇩🇿 الدوري الجزائري":

            show_ligue1(chat_id)

        elif text == "📅 مباريات اليوم":

            show_today(chat_id)

        elif text == "🏆 الفرق":

            show_teams(chat_id)

        elif text == "📊 تحليل مباراة":

            analyze_match(chat_id)

        elif text == "ℹ️ معلومات البوت":

            show_info(chat_id)

        elif text == "Ligue 2":

            schedule = get_ligue2_schedule()

            if schedule:

                send_message(
                    chat_id,
                    "🇩🇿 <b>Ligue 2 الجزائر</b>\n\n"
                    + schedule[:5000]
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ تعذر جلب جدول Ligue 2 حاليًا."
                )

        else:

            # إذا أرسل مباراة مباشرة
            if "-" in text:

                send_message(
                    chat_id,
                    "📊 <b>تحليل مبدئي</b>\n\n"
                    f"⚽ المباراة: <b>{text}</b>\n\n"
                    "🏠 أفضلية الأرض: غير محسوبة\n"
                    "📈 القوة: تحتاج بيانات تاريخية\n"
                    "🥅 الأهداف: تحتاج إحصائيات إضافية\n\n"
                    "⚠️ هذا تحليل مبدئي وليس توقعًا مضمونًا."
                )

            else:

                send_message(
                    chat_id,
                    "اختر إحدى الأزرار الموجودة في القائمة 👇"
                )

        return "OK", 200

    except Exception as e:

        print("❌ Webhook error:", e)

        return "OK", 200


# =========================================================
# Route اختبار
# =========================================================

@app.route("/")
def home():
    return "Algerian Football Bot is running 🇩🇿⚽"


@app.route("/health")
def health():
    return "OK"


# =========================================================
# تشغيل Flask
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
