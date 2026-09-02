import os
import requests
from datetime import datetime
from flask import Flask, request
from openai import OpenAI


# =========================================================
# الإعدادات
# =========================================================

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

FOOTBALL_API_URL = "https://v3.football.api-sports.io"

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# الدوريات المهمة
# =========================================================

LEAGUES = {
    "39": "🏴 الدوري الإنجليزي",
    "140": "🇪🇸 الدوري الإسباني",
    "135": "🇮🇹 الدوري الإيطالي",
    "78": "🇩🇪 الدوري الألماني",
    "61": "🇫🇷 الدوري الفرنسي",
    "2": "🏆 دوري أبطال أوروبا"
}


# =========================================================
# Telegram Functions
# =========================================================

def telegram(method, data=None):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=30
        )

        return response.json()

    except Exception as error:

        print("Telegram Error:", error)

        return None


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    # تقسيم الرسائل الطويلة
    if len(text) <= 4000:
        return telegram("sendMessage", data)

    parts = [
        text[i:i + 4000]
        for i in range(0, len(text), 4000)
    ]

    for part in parts:

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": part
            }
        )


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

            ["🏆 اختيار دوري"],

            ["📅 مباريات الغد"],

            ["🔥 المباريات المهمة"],

            ["ℹ️ المساعدة"]

        ],

        "resize_keyboard": True

    }


# =========================================================
# Football API
# =========================================================

def football_get(endpoint, params=None):

    try:

        headers = {
            "x-apisports-key": FOOTBALL_API_KEY
        }

        response = requests.get(
            f"{FOOTBALL_API_URL}/{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )

        data = response.json()

        return data.get("response", [])

    except Exception as error:

        print("Football API Error:", error)

        return []


# =========================================================
# مباريات اليوم
# =========================================================

def get_today_matches():

    today = datetime.now().strftime("%Y-%m-%d")

    return football_get(
        "fixtures",
        {
            "date": today,
            "timezone": "Africa/Algiers"
        }
    )


# =========================================================
# مباريات الغد
# =========================================================

def get_tomorrow_matches():

    from datetime import timedelta

    tomorrow = (
        datetime.now() + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    return football_get(
        "fixtures",
        {
            "date": tomorrow,
            "timezone": "Africa/Algiers"
        }
    )


# =========================================================
# عرض الدوريات
# =========================================================

def show_leagues(chat_id):

    keyboard = []

    for league_id, league_name in LEAGUES.items():

        keyboard.append([
            {
                "text": league_name,
                "callback_data": f"league_{league_id}"
            }
        ])

    send_message(

        chat_id,

        "🏆 اختر الدوري الذي تريد مشاهدة مبارياته:",

        {
            "inline_keyboard": keyboard
        }

    )


# =========================================================
# عرض المباريات
# =========================================================

def show_matches(chat_id, matches, title):

    if not matches:

        send_message(
            chat_id,
            "❌ لا توجد مباريات متاحة."
        )

        return

    keyboard = []

    text = f"{title}\n\n"

    for match in matches:

        fixture_id = match["fixture"]["id"]

        home = match["teams"]["home"]["name"]

        away = match["teams"]["away"]["name"]

        league = match["league"]["name"]

        date = match["fixture"]["date"]

        try:

            time = datetime.fromisoformat(
                date.replace("Z", "+00:00")
            ).strftime("%H:%M")

        except:

            time = "?"

        text += (
            f"⚽ {home} × {away}\n"
            f"🏆 {league}\n"
            f"🕒 {time}\n\n"
        )

        keyboard.append([
            {
                "text": f"{home} 🆚 {away}",
                "callback_data": f"match_{fixture_id}"
            }
        ])

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard[:50]
        }
    )


# =========================================================
# مباريات دوري معين
# =========================================================

def get_league_matches(league_id):

    today = datetime.now().strftime("%Y-%m-%d")

    return football_get(
        "fixtures",
        {
            "league": league_id,
            "date": today,
            "timezone": "Africa/Algiers"
        }
    )


# =========================================================
# جلب بيانات المباراة
# =========================================================

def get_match(fixture_id):

    matches = football_get(
        "fixtures",
        {
            "id": fixture_id
        }
    )

    if matches:

        return matches[0]

    return None


# =========================================================
# تحليل المباراة بالذكاء الاصطناعي
# =========================================================

def analyze_match(match):

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]

    league = match["league"]["name"]

    match_date = match["fixture"]["date"]

    prompt = f"""
حلل مباراة كرة القدم التالية تحليلاً رياضيًا موضوعيًا:

الدوري: {league}
الفريق صاحب الأرض: {home}
الفريق الضيف: {away}
موعد المباراة: {match_date}

أعطني تقريرًا منظمًا يتضمن:

1. أهمية المباراة.
2. مقارنة عامة بين الفريقين.
3. نقاط القوة المحتملة.
4. نقاط الضعف المحتملة.
5. العوامل التي قد تؤثر على المباراة.
6. السيناريوهات المحتملة للمباراة.
7. توقع احتمالي بصيغة تحليلية فقط.

مهم جدًا:
- لا تدّعِ وجود معلومات غير موجودة.
- لا تقل إن أي نتيجة مضمونة.
- لا تقدم رهانًا مضمونًا.
- وضح أن كرة القدم غير قابلة للتنبؤ بشكل كامل.
- ركز على التحليل الرياضي والإحصائي.
- أجب باللغة العربية.
"""

    try:

        response = client.responses.create(

            model="gpt-5",

            input=prompt

        )

        return response.output_text

    except Exception as error:

        print("AI Error:", error)

        return (
            "❌ حدث خطأ أثناء إنشاء التحليل."
        )


# =========================================================
# عرض وتحليل المباراة
# =========================================================

def show_match_analysis(chat_id, fixture_id):

    send_message(
        chat_id,
        "🤖 جاري جمع بيانات المباراة وتحليلها..."
    )

    match = get_match(fixture_id)

    if not match:

        send_message(
            chat_id,
            "❌ لم أتمكن من العثور على المباراة."
        )

        return

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]

    league = match["league"]["name"]

    basic_info = (
        "━━━━━━━━━━━━━━━━━━\n"
        "⚽ تحليل المباراة\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 الدوري: {league}\n"
        f"🏠 {home}\n"
        f"✈️ {away}\n\n"
        "🤖 جاري التحليل الذكي...\n"
    )

    send_message(
        chat_id,
        basic_info
    )

    analysis = analyze_match(match)

    send_message(
        chat_id,
        analysis
    )


# =========================================================
# المساعدة
# =========================================================

def help_message(chat_id):

    send_message(

        chat_id,

        "⚽ Football AI\n\n"

        "📅 مباريات اليوم\n"
        "🏆 اختيار دوري\n"
        "📊 تحليل المباريات\n"
        "🤖 تحليل بالذكاء الاصطناعي\n\n"

        "⚠️ التحليل معلوماتي ورياضي فقط، "
        "ولا توجد نتيجة مضمونة في كرة القدم."
    )


# =========================================================
# Flask
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "⚽ Football AI is running!"


@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True) or {}


    # =====================================================
    # CALLBACK
    # =====================================================

    callback = data.get("callback_query")

    if callback:

        chat_id = callback["message"]["chat"]["id"]

        if not is_owner(chat_id):

            answer_callback(callback["id"])

            return "OK"

        callback_data = callback.get("data", "")

        answer_callback(callback["id"])


        # اختيار دوري
        if callback_data.startswith("league_"):

            league_id = callback_data.replace(
                "league_",
                ""
            )

            matches = get_league_matches(
                league_id
            )

            league_name = LEAGUES.get(
                league_id,
                "الدوري"
            )

            show_matches(
                chat_id,
                matches,
                f"🏆 {league_name}"
            )


        # تحليل مباراة
        elif callback_data.startswith("match_"):

            fixture_id = callback_data.replace(
                "match_",
                ""
            )

            show_match_analysis(
                chat_id,
                fixture_id
            )


        return "OK"


    # =====================================================
    # MESSAGE
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
    # حماية
    # =====================================================

    if not is_owner(chat_id):

        send_message(
            chat_id,
            "🔒 هذا البوت خاص."
        )

        return "OK"


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        send_message(

            chat_id,

            "⚽ أهلاً بك في Football AI 🤖\n\n"
            "📊 مساعدك لتحليل مباريات كرة القدم.\n\n"
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
    # الدوريات
    # =====================================================

    if text == "🏆 اختيار دوري":

        show_leagues(chat_id)

        return "OK"


    # =====================================================
    # مباريات مهمة
    # =====================================================

    if text == "🔥 المباريات المهمة":

        send_message(
            chat_id,
            "⚽ استخدم «مباريات اليوم» ثم اختر المباراة التي تريد تحليلها."
        )

        return "OK"


    # =====================================================
    # مساعدة
    # =====================================================

    if text == "ℹ️ المساعدة":

        help_message(chat_id)

        return "OK"


    send_message(
        chat_id,
        "🤖 استخدم الأزرار الموجودة في القائمة."
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
