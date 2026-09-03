import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request

# OpenAI اختياري
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# إعداد التطبيق
# =========================================================

app = Flask(__name__)


# =========================================================
# Environment Variables - Render
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")


# =========================================================
# الروابط
# =========================================================

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else None
)

FOOTBALL_DATA_URL = "https://api.football-data.org/v4"


# =========================================================
# OpenAI
# =========================================================

client = None

if OPENAI_API_KEY and OpenAI:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI جاهز")
    except Exception as error:
        print("⚠️ OpenAI Error:", error)

else:
    print("⚠️ OPENAI_API_KEY غير موجود - التحليل الذكي غير مفعل")


# =========================================================
# الدوريات
# =========================================================

LEAGUES = {
    "PL": "🏴 الدوري الإنجليزي",
    "PD": "🇪🇸 الدوري الإسباني",
    "SA": "🇮🇹 الدوري الإيطالي",
    "BL1": "🇩🇪 الدوري الألماني",
    "FL1": "🇫🇷 الدوري الفرنسي",
    "CL": "🏆 دوري أبطال أوروبا"
}


# =========================================================
# Telegram Functions
# =========================================================

def telegram(method, data=None):

    if not TELEGRAM_API:
        print("❌ BOT_TOKEN غير موجود")
        return None

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data or {},
            timeout=30
        )

        result = response.json()

        if not result.get("ok"):
            print("Telegram Error:", result)

        return result

    except Exception as error:

        print("Telegram Error:", error)

        return None


def send_message(chat_id, text, keyboard=None):

    # Telegram يسمح تقريبًا بـ 4096 حرف
    parts = [
        text[i:i + 4000]
        for i in range(0, len(text), 4000)
    ]

    for index, part in enumerate(parts):

        data = {
            "chat_id": chat_id,
            "text": part
        }

        # نضع الكيبورد فقط في آخر رسالة
        if keyboard and index == len(parts) - 1:
            data["reply_markup"] = keyboard

        telegram("sendMessage", data)


def answer_callback(callback_id):

    telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# حماية البوت
# =========================================================

def is_owner(chat_id):

    # إذا لم تضع OWNER_CHAT_ID يسمح للجميع
    if not OWNER_CHAT_ID:
        return True

    return str(chat_id) == str(OWNER_CHAT_ID)


# =========================================================
# القائمة الرئيسية
# =========================================================

def main_keyboard():

    return {

        "keyboard": [

            ["⚽ مباريات اليوم"],

            ["📅 مباريات الغد"],

            ["🏆 اختيار الدوري"],

            ["📊 تحليل مباراة"],

            ["ℹ️ المساعدة"]

        ],

        "resize_keyboard": True
    }


# =========================================================
# Football Data API
# =========================================================

def football_get(endpoint, params=None):

    if not FOOTBALL_DATA_API_KEY:

        print("❌ FOOTBALL_DATA_API_KEY غير موجود")

        return None

    try:

        headers = {
            "X-Auth-Token": FOOTBALL_DATA_API_KEY
        }

        response = requests.get(
            f"{FOOTBALL_DATA_URL}/{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )

        # طباعة الخطأ للمساعدة
        if response.status_code != 200:

            print(
                "Football API Error:",
                response.status_code,
                response.text
            )

            return None

        return response.json()

    except Exception as error:

        print("Football Request Error:", error)

        return None


# =========================================================
# مباريات اليوم
# =========================================================

def get_matches_by_date(date):

    data = football_get(
        "matches",
        {
            "dateFrom": date,
            "dateTo": date
        }
    )

    if not data:
        return []

    return data.get("matches", [])


def get_today_matches():

    today = datetime.now().strftime("%Y-%m-%d")

    return get_matches_by_date(today)


# =========================================================
# مباريات الغد
# =========================================================

def get_tomorrow_matches():

    tomorrow = (
        datetime.now() + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    return get_matches_by_date(tomorrow)


# =========================================================
# مباريات دوري معين
# =========================================================

def get_league_matches(league_code):

    today = datetime.now().strftime("%Y-%m-%d")

    data = football_get(
        f"competitions/{league_code}/matches",
        {
            "dateFrom": today,
            "dateTo": today
        }
    )

    if not data:
        return []

    return data.get("matches", [])


# =========================================================
# عرض اختيار الدوريات
# =========================================================

def show_leagues(chat_id):

    keyboard = []

    for code, name in LEAGUES.items():

        keyboard.append([
            {
                "text": name,
                "callback_data": f"league_{code}"
            }
        ])

    send_message(

        chat_id,

        "🏆 اختر الدوري:",

        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# حفظ المباريات مؤقتًا
# =========================================================

matches_cache = {}


# =========================================================
# عرض المباريات
# =========================================================

def show_matches(chat_id, matches, title):

    if not matches:

        send_message(
            chat_id,
            "❌ لا توجد مباريات متاحة في هذه الفترة."
        )

        return

    text = f"{title}\n\n"

    keyboard = []

    # Telegram يسمح بعدد محدود من الأزرار
    matches = matches[:40]

    for match in matches:

        match_id = match.get("id")

        home = (
            match.get("homeTeam", {})
            .get("name", "الفريق الأول")
        )

        away = (
            match.get("awayTeam", {})
            .get("name", "الفريق الثاني")
        )

        competition = (
            match.get("competition", {})
            .get("name", "")
        )

        utc_date = match.get("utcDate", "")

        try:

            dt = datetime.fromisoformat(
                utc_date.replace("Z", "+00:00")
            )

            time = dt.strftime("%H:%M")

        except:

            time = "?"

        # حفظ المباراة
        matches_cache[str(match_id)] = match

        text += (
            f"⚽ {home} 🆚 {away}\n"
            f"🏆 {competition}\n"
            f"🕒 {time}\n\n"
        )

        keyboard.append([
            {
                "text": f"📊 {home} × {away}",
                "callback_data": f"match_{match_id}"
            }
        ])

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# جلب مباراة واحدة
# =========================================================

def get_match(match_id):

    data = football_get(
        f"matches/{match_id}"
    )

    return data


# =========================================================
# إنشاء تحليل بدون AI
# =========================================================

def basic_analysis(match):

    home = (
        match.get("homeTeam", {})
        .get("name", "الفريق صاحب الأرض")
    )

    away = (
        match.get("awayTeam", {})
        .get("name", "الفريق الضيف")
    )

    competition = (
        match.get("competition", {})
        .get("name", "غير معروف")
    )

    status = match.get("status", "")

    return f"""
━━━━━━━━━━━━━━━━━━
⚽ تحليل المباراة
━━━━━━━━━━━━━━━━━━

🏆 البطولة:
{competition}

🏠 صاحب الأرض:
{home}

✈️ الفريق الضيف:
{away}

📌 حالة المباراة:
{status}

🧠 تحليل أولي:

• المباراة تحتاج إلى دراسة مستوى الفريقين.
• عامل الأرض قد يكون مؤثرًا لصالح صاحب الأرض.
• يجب متابعة التشكيلة والغيابات قبل بداية المباراة.
• النتائج السابقة لا تضمن نتيجة المباراة القادمة.

⚠️ كرة القدم غير مضمونة والنتيجة النهائية قد تختلف عن أي توقع.
"""


# =========================================================
# تحليل بالذكاء الاصطناعي
# =========================================================

def ai_analysis(match):

    if not client:
        return None

    home = (
        match.get("homeTeam", {})
        .get("name", "")
    )

    away = (
        match.get("awayTeam", {})
        .get("name", "")
    )

    competition = (
        match.get("competition", {})
        .get("name", "")
    )

    date = match.get("utcDate", "")

    prompt = f"""
أنت محلل رياضي محترف.

حلل المباراة التالية باللغة العربية:

البطولة: {competition}
الفريق صاحب الأرض: {home}
الفريق الضيف: {away}
موعد المباراة: {date}

أعطني تحليلًا منظمًا:

⚽ نظرة عامة
📊 مقارنة الفريقين
🏠 تأثير اللعب على الأرض
🔥 أهم العوامل المؤثرة
🧠 السيناريوهات المحتملة
📌 ما المعلومات التي يجب متابعتها قبل المباراة

قواعد مهمة:
- لا تخترع إحصائيات غير موجودة.
- لا تقل إن النتيجة مضمونة.
- لا تعد بأي أرباح.
- قدم تحليلًا رياضيًا موضوعيًا فقط.
"""

    try:

        response = client.responses.create(

            model="gpt-5-mini",

            input=prompt
        )

        return response.output_text

    except Exception as error:

        print("AI Error:", error)

        return None


# =========================================================
# عرض التحليل
# =========================================================

def show_match_analysis(chat_id, match_id):

    send_message(
        chat_id,
        "🤖 جاري تحليل المباراة..."
    )

    match = get_match(match_id)

    if not match:

        match = matches_cache.get(str(match_id))

    if not match:

        send_message(
            chat_id,
            "❌ لم أتمكن من الحصول على بيانات المباراة."
        )

        return

    # تحليل أساسي
    analysis = basic_analysis(match)

    send_message(
        chat_id,
        analysis
    )

    # تحليل AI
    ai_result = ai_analysis(match)

    if ai_result:

        send_message(
            chat_id,
            "🤖 التحليل الذكي:\n\n" +
            ai_result
        )

    else:

        send_message(
            chat_id,
            "ℹ️ التحليل الذكي غير متاح حاليًا. "
            "تأكد من OPENAI_API_KEY."
        )


# =========================================================
# المساعدة
# =========================================================

def help_message(chat_id):

    send_message(
        chat_id,
        """
⚽ Football AI

الأزرار المتاحة:

⚽ مباريات اليوم
📅 مباريات الغد
🏆 اختيار الدوري
📊 تحليل المباريات

🤖 البوت يستخدم بيانات كرة القدم
لإنشاء تحليل رياضي.

⚠️ لا توجد نتائج مضمونة في كرة القدم.
"""
    )


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "⚽ Football AI is running!"


# =========================================================
# Webhook Telegram
# =========================================================

@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    data = request.get_json(
        silent=True
    ) or {}


    # =====================================================
    # Callback
    # =====================================================

    callback = data.get("callback_query")

    if callback:

        chat_id = (
            callback["message"]["chat"]["id"]
        )

        answer_callback(callback["id"])

        if not is_owner(chat_id):

            return "OK"

        callback_data = callback.get("data", "")


        # اختيار الدوري
        if callback_data.startswith("league_"):

            league_code = callback_data.replace(
                "league_",
                ""
            )

            league_name = LEAGUES.get(
                league_code,
                "الدوري"
            )

            send_message(
                chat_id,
                "⏳ جاري جلب مباريات الدوري..."
            )

            matches = get_league_matches(
                league_code
            )

            show_matches(
                chat_id,
                matches,
                f"🏆 {league_name}"
            )


        # تحليل مباراة
        elif callback_data.startswith("match_"):

            match_id = callback_data.replace(
                "match_",
                ""
            )

            show_match_analysis(
                chat_id,
                match_id
            )

        return "OK"


    # =====================================================
    # Message
    # =====================================================

    message = data.get("message", {})

    chat_id = (
        message
        .get("chat", {})
        .get("id")
    )

    text = (
        message
        .get("text", "")
        .strip()
    )

    if not chat_id:

        return "OK"


    # =====================================================
    # حماية البوت
    # =====================================================

    if not is_owner(chat_id):

        send_message(
            chat_id,
            "🔒 هذا البوت خاص."
        )

        return "OK"


    # =====================================================
    # Start
    # =====================================================

    if text == "/start":

        send_message(
            chat_id,

            "⚽ أهلاً بك في Football AI 🤖\n\n"
            "📊 مساعد لتحليل مباريات كرة القدم.\n\n"
            "اختر من القائمة:",

            main_keyboard()
        )

        return "OK"


    # =====================================================
    # مباريات اليوم
    # =====================================================

    if text == "⚽ مباريات اليوم":

        send_message(
            chat_id,
            "⏳ جاري جلب مباريات اليوم..."
        )

        matches = get_today_matches()

        show_matches(
            chat_id,
            matches,
            "⚽ مباريات اليوم"
        )

        return "OK"


    # =====================================================
    # مباريات الغد
    # =====================================================

    if text == "📅 مباريات الغد":

        send_message(
            chat_id,
            "⏳ جاري جلب مباريات الغد..."
        )

        matches = get_tomorrow_matches()

        show_matches(
            chat_id,
            matches,
            "📅 مباريات الغد"
        )

        return "OK"


    # =====================================================
    # اختيار الدوري
    # =====================================================

    if text == "🏆 اختيار الدوري":

        show_leagues(chat_id)

        return "OK"


    # =====================================================
    # تحليل مباراة
    # =====================================================

    if text == "📊 تحليل مباراة":

        send_message(
            chat_id,
            "⚽ اختر أولًا «مباريات اليوم» أو «اختيار الدوري»، ثم اضغط على المباراة التي تريد تحليلها."
        )

        return "OK"


    # =====================================================
    # المساعدة
    # =====================================================

    if text == "ℹ️ المساعدة":

        help_message(chat_id)

        return "OK"


    # =====================================================
    # رسالة افتراضية
    # =====================================================

    send_message(
        chat_id,
        "🤖 استخدم الأزرار أو أرسل /start."
    )

    return "OK"


# =========================================================
# تشغيل التطبيق
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
