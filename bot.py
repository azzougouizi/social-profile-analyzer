import os
import json
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, request
from openai import OpenAI


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FOOTBALL_API_URL = "https://api.football-data.org/v4"

# توقيت الجزائر
ALGERIA_TZ = ZoneInfo("Africa/Algiers")


# =========================================================
# OPENAI
# =========================================================

client = None

if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI connected")
    except Exception as e:
        print("❌ OpenAI connection error:", e)
else:
    print("⚠️ OPENAI_API_KEY غير موجود")


# =========================================================
# LEAGUES
# =========================================================

LEAGUES = {
    "PL": "🏴 Premier League",
    "PD": "🇪🇸 La Liga",
    "SA": "🇮🇹 Serie A",
    "BL1": "🇩🇪 Bundesliga",
    "FL1": "🇫🇷 Ligue 1",
    "CL": "🏆 Champions League"
}


# =========================================================
# CACHE
# =========================================================

matches_cache = {}


# =========================================================
# OWNER
# =========================================================

def is_owner(chat_id):

    if not OWNER_CHAT_ID:
        print("⚠️ OWNER_CHAT_ID غير موجود")
        return False

    return str(chat_id) == str(OWNER_CHAT_ID)


# =========================================================
# TELEGRAM
# =========================================================

def telegram_request(method, data):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=30
        )

        result = response.json()

        if not result.get("ok"):
            print("❌ Telegram Error:", result)

        return result

    except Exception as e:

        print("❌ Telegram Exception:", e)

        return None


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram_request(
        "sendMessage",
        data
    )


def answer_callback(callback_id):

    return telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# MAIN KEYBOARD
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            ["⚽ مباريات اليوم"],
            ["📅 مباريات الغد"],
            ["🏆 الدوريات"],
            ["🤖 تحليل مباراة"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# FOOTBALL DATA API
# =========================================================

def football_get(endpoint, params=None):

    if not FOOTBALL_DATA_API_KEY:

        print("❌ FOOTBALL_DATA_API_KEY غير موجود")

        return None

    url = f"{FOOTBALL_API_URL}/{endpoint}"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_API_KEY
    }

    try:

        print("===================================")
        print("⚽ FOOTBALL API REQUEST")
        print("URL:", url)
        print("PARAMS:", params)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("STATUS:", response.status_code)

        print(
            "RESPONSE:",
            response.text[:1500]
        )

        print("===================================")

        if response.status_code != 200:

            return None

        return response.json()

    except Exception as e:

        print("❌ Football API Error:", e)

        return None


# =========================================================
# DATE
# =========================================================

def algeria_today():

    return datetime.now(
        ALGERIA_TZ
    ).strftime("%Y-%m-%d")


def algeria_tomorrow():

    return (
        datetime.now(ALGERIA_TZ)
        + timedelta(days=1)
    ).strftime("%Y-%m-%d")


# =========================================================
# MATCHES
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

    return data.get(
        "matches",
        []
    )


def get_today_matches():

    today = algeria_today()

    print("📅 Algeria today:", today)

    return get_matches_by_date(today)


def get_tomorrow_matches():

    tomorrow = algeria_tomorrow()

    print("📅 Algeria tomorrow:", tomorrow)

    return get_matches_by_date(tomorrow)


# =========================================================
# LEAGUE MATCHES
# =========================================================

def get_league_matches(league):

    today = algeria_today()

    data = football_get(
        f"competitions/{league}/matches",
        {
            "dateFrom": today,
            "dateTo": today
        }
    )

    if not data:

        return []

    return data.get(
        "matches",
        []
    )


# =========================================================
# SHOW LEAGUES
# =========================================================

def show_leagues(chat_id):

    keyboard = []

    for code, name in LEAGUES.items():

        keyboard.append(
            [
                {
                    "text": name,
                    "callback_data": f"league:{code}"
                }
            ]
        )

    send_message(
        chat_id,
        "🏆 اختر الدوري:",
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# FORMAT MATCH TIME
# =========================================================

def match_time(utc_date):

    try:

        dt = datetime.fromisoformat(
            utc_date.replace(
                "Z",
                "+00:00"
            )
        )

        local_time = dt.astimezone(
            ALGERIA_TZ
        )

        return local_time.strftime(
            "%H:%M"
        )

    except Exception:

        return "غير معروف"


# =========================================================
# SHOW MATCHES
# =========================================================

def show_matches(
    chat_id,
    matches,
    title
):

    if not matches:

        send_message(
            chat_id,
            "❌ لا توجد مباريات متاحة من Football-Data لهذا اليوم.\n\n"
            "قد يكون السبب أن البطولة أو المباراة غير موجودة ضمن التغطية المتاحة لحسابك."
        )

        return


    text = f"{title}\n\n"

    keyboard = []

    count = 0


    for match in matches:

        if count >= 30:
            break

        match_id = str(
            match.get("id")
        )

        home = match.get(
            "homeTeam",
            {}
        ).get(
            "name",
            "Home"
        )

        away = match.get(
            "awayTeam",
            {}
        ).get(
            "name",
            "Away"
        )

        competition = match.get(
            "competition",
            {}
        ).get(
            "name",
            "غير معروف"
        )

        utc_date = match.get(
            "utcDate",
            ""
        )

        time = match_time(
            utc_date
        )

        matches_cache[
            match_id
        ] = match


        text += (
            f"⚽ {home} × {away}\n"
            f"🏆 {competition}\n"
            f"🕒 {time} بتوقيت الجزائر\n\n"
        )


        keyboard.append(
            [
                {
                    "text": f"🤖 تحليل {home} × {away}",
                    "callback_data":
                        f"analysis:{match_id}"
                }
            ]
        )

        count += 1


    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# TEAM RECENT MATCHES
# =========================================================

def get_team_matches(team_id):

    if not team_id:

        return []


    data = football_get(
        f"teams/{team_id}/matches",
        {
            "status": "FINISHED",
            "limit": 5
        }
    )

    if not data:

        return []

    return data.get(
        "matches",
        []
    )


# =========================================================
# STANDINGS
# =========================================================

def get_standings(
    competition_code
):

    if not competition_code:

        return None

    return football_get(
        f"competitions/{competition_code}/standings"
    )


# =========================================================
# PREPARE AI DATA
# =========================================================

def prepare_analysis_data(match):

    home_team = match.get(
        "homeTeam",
        {}
    )

    away_team = match.get(
        "awayTeam",
        {}
    )

    home_id = home_team.get(
        "id"
    )

    away_id = away_team.get(
        "id"
    )

    competition = match.get(
        "competition",
        {}
    )

    competition_code = competition.get(
        "code"
    )


    print(
        "📊 Preparing analysis:",
        home_team.get("name"),
        "vs",
        away_team.get("name")
    )


    home_matches = get_team_matches(
        home_id
    )

    away_matches = get_team_matches(
        away_id
    )

    standings = get_standings(
        competition_code
    )


    return {

        "match": match,

        "home_recent_matches":
            home_matches,

        "away_recent_matches":
            away_matches,

        "standings":
            standings
    }


# =========================================================
# OPENAI ANALYSIS
# =========================================================

def analyze_match_with_ai(data):

    if not client:

        return (
            "❌ OpenAI غير متصل.\n\n"
            "تأكد من وجود:\n"
            "OPENAI_API_KEY\n"
            "في Render Environment."
        )


    match = data["match"]

    home = match.get(
        "homeTeam",
        {}
    ).get(
        "name",
        "الفريق المضيف"
    )

    away = match.get(
        "awayTeam",
        {}
    ).get(
        "name",
        "الفريق الضيف"
    )

    competition = match.get(
        "competition",
        {}
    ).get(
        "name",
        "غير معروف"
    )

    match_date = match.get(
        "utcDate",
        ""
    )


    football_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


    prompt = f"""
أنت محلل كرة قدم محترف.

حلل المباراة التالية اعتمادًا على البيانات
الموجودة في JSON فقط.

المباراة:
{home} ضد {away}

البطولة:
{competition}

الموعد:
{match_date}

البيانات:
{football_data}


أعطني التحليل باللغة العربية.

استخدم هذا الشكل بالضبط:

━━━━━━━━━━━━━━━━━━
⚽ تحليل المباراة
━━━━━━━━━━━━━━━━━━

🏠 {home}
نسبة الفوز: XX%

🤝 التعادل
النسبة: XX%

✈️ {away}
نسبة الفوز: XX%

⚽ الأهداف المتوقعة:
الفريق المضيف: X تقريبًا
الفريق الضيف: X تقريبًا

🥅 من الأقرب للتسجيل:
اسم اللاعب إن كان متوفرًا في البيانات
أو اكتب:
"لا توجد بيانات كافية لتحديد الهداف"

🟨 البطاقات الصفراء المتوقعة:
X إلى X تقريبًا

🏆 الأقرب للفوز:
اسم الفريق

📊 النتيجة المحتملة:
X-X

📈 مستوى الثقة:
منخفض / متوسط / مرتفع

🧠 التحليل:
تحليل مختصر يعتمد على البيانات المتوفرة.


قواعد مهمة:

1. مجموع نسب الفوز والتعادل = 100%.
2. لا تخترع أسماء لاعبين.
3. لا تخترع إحصائيات غير موجودة.
4. إذا لم توجد بيانات كافية عن الهدافين، صرّح بذلك.
5. الأهداف والبطاقات تقديرات وليست نتائج مؤكدة.
6. لا تقل إن أي نتيجة مضمونة.
7. لا تعد المستخدم بالربح.
8. كن واضحًا ومختصرًا.
"""


    try:

        print(
            "🤖 Sending analysis to OpenAI..."
        )


        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )


        result = response.output_text

        print(
            "✅ OpenAI analysis completed"
        )

        return result


    except Exception as e:

        print(
            "❌ OpenAI Analysis Error:",
            e
        )

        return (
            "❌ حدث خطأ أثناء التحليل الذكي.\n\n"
            "راجع Logs في Render."
        )


# =========================================================
# ANALYZE MATCH
# =========================================================

def analyze_match(
    chat_id,
    match_id
):

    send_message(
        chat_id,
        "🤖 جاري جمع بيانات المباراة...\n"
        "📊 أراجع نتائج الفريقين والترتيب...\n"
        "🧠 ثم أرسل التحليل الذكي.\n\n"
        "⏳ انتظر قليلًا..."
    )


    match = matches_cache.get(
        str(match_id)
    )


    if not match:

        match = football_get(
            f"matches/{match_id}"
        )


    if not match:

        send_message(
            chat_id,
            "❌ لم أتمكن من العثور على المباراة."
        )

        return


    data = prepare_analysis_data(
        match
    )


    result = analyze_match_with_ai(
        data
    )


    # Telegram message limit
    if len(result) > 4000:

        for i in range(
            0,
            len(result),
            4000
        ):

            send_message(
                chat_id,
                result[i:i + 4000]
            )

    else:

        send_message(
            chat_id,
            result
        )


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return "⚽ Football AI is running!"


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    update = request.get_json(
        silent=True
    ) or {}


    # =====================================================
    # CALLBACK
    # =====================================================

    callback = update.get(
        "callback_query"
    )


    if callback:

        chat_id = callback[
            "message"
        ][
            "chat"
        ][
            "id"
        ]


        answer_callback(
            callback["id"]
        )


        if not is_owner(
            chat_id
        ):

            return "OK"


        callback_data = callback.get(
            "data",
            ""
        )


        # الدوري
        if callback_data.startswith(
            "league:"
        ):

            league_code = (
                callback_data
                .split(":")[1]
            )


            matches = get_league_matches(
                league_code
            )


            league_name = LEAGUES.get(
                league_code,
                league_code
            )


            show_matches(
                chat_id,
                matches,
                f"🏆 {league_name}"
            )


        # التحليل
        elif callback_data.startswith(
            "analysis:"
        ):

            match_id = (
                callback_data
                .split(":")[1]
            )


            analyze_match(
                chat_id,
                match_id
            )


        return "OK"


    # =====================================================
    # MESSAGE
    # =====================================================

    message = update.get(
        "message"
    )


    if not message:

        return "OK"


    chat_id = message[
        "chat"
    ][
        "id"
    ]


    text = message.get(
        "text",
        ""
    ).strip()


    if not is_owner(
        chat_id
    ):

        send_message(
            chat_id,
            "🔒 هذا البوت خاص."
        )

        return "OK"


    # /start
    if text == "/start":

        send_message(
            chat_id,

            "⚽ أهلاً بك في Football AI 🤖\n\n"
            "يمكنك مشاهدة المباريات وتحليلها بالذكاء الاصطناعي.\n\n"
            "اختر من القائمة:",
            
            main_keyboard()
        )

        return "OK"


    # مباريات اليوم
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


    # مباريات الغد
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


    # الدوريات
    if text == "🏆 الدوريات":

        show_leagues(
            chat_id
        )

        return "OK"


    # تحليل مباراة
    if text == "🤖 تحليل مباراة":

        send_message(
            chat_id,

            "⚽ اختر «مباريات اليوم» أو «الدوريات».\n\n"
            "ثم اضغط زر 🤖 تحليل بجانب المباراة."
        )

        return "OK"


    # أي رسالة أخرى
    send_message(
        chat_id,
        "استخدم الأزرار أو أرسل /start."
    )


    return "OK"


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
