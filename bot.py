import os
import json
import requests
from datetime import datetime, timedelta

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


# =========================================================
# API URLS
# =========================================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

FOOTBALL_API_URL = "https://api.football-data.org/v4"


# =========================================================
# OPENAI
# =========================================================

client = None

if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI connected")
    except Exception as e:
        print("❌ OpenAI Error:", e)

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
# SECURITY
# =========================================================

def is_owner(chat_id):

    if not OWNER_CHAT_ID:
        return True

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
            print("Telegram Error:", result)

        return result

    except Exception as e:

        print("Telegram Exception:", e)

        return None


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram_request("sendMessage", data)


def answer_callback(callback_id):

    telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# MAIN MENU
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

        print("⚽ Request:", url)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("📡 Status:", response.status_code)

        if response.status_code != 200:

            print("❌ API Response:", response.text[:1000])

            return None

        return response.json()

    except Exception as e:

        print("❌ Football API Error:", e)

        return None


# =========================================================
# GET MATCHES
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

    today = datetime.utcnow().strftime("%Y-%m-%d")

    return get_matches_by_date(today)


def get_tomorrow_matches():

    tomorrow = (
        datetime.utcnow() + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    return get_matches_by_date(tomorrow)


# =========================================================
# LEAGUE MATCHES
# =========================================================

def get_league_matches(league):

    today = datetime.utcnow().strftime("%Y-%m-%d")

    data = football_get(
        f"competitions/{league}/matches",
        {
            "dateFrom": today,
            "dateTo": today
        }
    )

    if not data:
        return []

    return data.get("matches", [])


# =========================================================
# SHOW LEAGUES
# =========================================================

def show_leagues(chat_id):

    keyboard = []

    for code, name in LEAGUES.items():

        keyboard.append([

            {
                "text": name,
                "callback_data": f"league:{code}"
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
# SHOW MATCHES
# =========================================================

def show_matches(chat_id, matches, title):

    if not matches:

        send_message(
            chat_id,
            "❌ لم أجد مباريات.\n\n"
            "إذا كنت متأكدًا أن هناك مباريات، راجع FOOTBALL_DATA_API_KEY."
        )

        return

    keyboard = []

    text = f"{title}\n\n"

    for match in matches[:30]:

        match_id = str(match.get("id"))

        home = match.get("homeTeam", {}).get("name", "Home")
        away = match.get("awayTeam", {}).get("name", "Away")

        competition = match.get(
            "competition", {}
        ).get("name", "")

        utc_date = match.get("utcDate", "")

        matches_cache[match_id] = match

        try:

            dt = datetime.fromisoformat(
                utc_date.replace("Z", "+00:00")
            )

            time = dt.strftime("%H:%M UTC")

        except:

            time = "غير معروف"

        text += (
            f"⚽ {home} × {away}\n"
            f"🏆 {competition}\n"
            f"🕒 {time}\n\n"
        )

        keyboard.append([

            {
                "text": f"🤖 تحليل {home} × {away}",
                "callback_data": f"analysis:{match_id}"
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
# GET TEAM RECENT MATCHES
# =========================================================

def get_team_matches(team_id):

    data = football_get(
        f"teams/{team_id}/matches",
        {
            "status": "FINISHED",
            "limit": 5
        }
    )

    if not data:
        return []

    return data.get("matches", [])


# =========================================================
# GET STANDINGS
# =========================================================

def get_standings(competition_code):

    if not competition_code:
        return None

    return football_get(
        f"competitions/{competition_code}/standings"
    )


# =========================================================
# PREPARE DATA FOR AI
# =========================================================

def prepare_analysis_data(match):

    home_team = match.get("homeTeam", {})
    away_team = match.get("awayTeam", {})

    home_id = home_team.get("id")
    away_id = away_team.get("id")

    competition = match.get("competition", {})

    competition_code = competition.get("code")

    # آخر مباريات الفريقين
    home_matches = get_team_matches(home_id) if home_id else []
    away_matches = get_team_matches(away_id) if away_id else []

    # ترتيب الدوري
    standings = get_standings(competition_code)

    data = {

        "match": match,

        "home_recent_matches": home_matches,

        "away_recent_matches": away_matches,

        "standings": standings

    }

    return data


# =========================================================
# AI ANALYSIS
# =========================================================

def analyze_match_with_ai(data):

    if not client:

        return (
            "❌ OpenAI غير متصل.\n"
            "أضف OPENAI_API_KEY في Render."
        )

    match = data["match"]

    home = match.get(
        "homeTeam", {}
    ).get("name")

    away = match.get(
        "awayTeam", {}
    ).get("name")

    competition = match.get(
        "competition", {}
    ).get("name")

    match_date = match.get("utcDate")

    # نرسل البيانات الحقيقية للذكاء الاصطناعي
    football_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
أنت محلل كرة قدم محترف.

حلل المباراة التالية اعتمادًا فقط على البيانات
الموجودة في JSON أدناه.

المباراة:
{home} ضد {away}

البطولة:
{competition}

الموعد:
{match_date}

البيانات:

{football_data}

أريد منك إرجاع النتيجة باللغة العربية فقط
وبهذا الشكل المنظم:

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
X إلى X أهداف تقريبًا

🟨 البطاقات الصفراء المتوقعة:
X إلى X بطاقات تقريبًا

🏆 الأقرب للفوز:
اسم الفريق أو التعادل

📊 النتيجة المحتملة:
مثال: 2-1

🧠 التحليل:
اكتب تحليلًا مختصرًا اعتمادًا على البيانات المتوفرة.

قواعد مهمة جدًا:

1. مجموع نسب الفوز والتعادل يجب أن يساوي 100%.
2. لا تخترع إحصائيات غير موجودة في البيانات.
3. إذا كانت البيانات غير كافية، قل إن الثقة منخفضة.
4. البطاقات والأهداف مجرد تقديرات احتمالية.
5. لا تقل إن أي نتيجة مضمونة.
6. لا تقدم وعودًا بالربح.
"""

    try:

        response = client.responses.create(

            model="gpt-5-mini",

            input=prompt
        )

        return response.output_text

    except Exception as e:

        print("❌ OpenAI Analysis Error:", e)

        return (
            "❌ حدث خطأ أثناء التحليل الذكي.\n\n"
            "راجع Logs في Render."
        )


# =========================================================
# ANALYZE MATCH
# =========================================================

def analyze_match(chat_id, match_id):

    send_message(
        chat_id,
        "🤖 جاري جمع بيانات الفريقين وتحليل المباراة...\n⏳ انتظر قليلًا."
    )

    match = matches_cache.get(str(match_id))

    if not match:

        match = football_get(f"matches/{match_id}")

    if not match:

        send_message(
            chat_id,
            "❌ لم أتمكن من العثور على المباراة."
        )

        return

    data = prepare_analysis_data(match)

    result = analyze_match_with_ai(data)

    # Telegram limit
    if len(result) > 4000:

        for i in range(0, len(result), 4000):

            send_message(
                chat_id,
                result[i:i + 4000]
            )

    else:

        send_message(chat_id, result)


# =========================================================
# FLASK HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "⚽ Football AI is running!"


# =========================================================
# TELEGRAM WEBHOOK
# =========================================================

@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    update = request.get_json(
        silent=True
    ) or {}


    # =====================================================
    # CALLBACK BUTTONS
    # =====================================================

    callback = update.get("callback_query")

    if callback:

        chat_id = callback[
            "message"
        ]["chat"]["id"]

        answer_callback(callback["id"])

        if not is_owner(chat_id):

            return "OK"

        callback_data = callback.get("data", "")


        # LEAGUE
        if callback_data.startswith("league:"):

            league_code = callback_data.split(":")[1]

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


        # ANALYSIS
        elif callback_data.startswith("analysis:"):

            match_id = callback_data.split(":")[1]

            analyze_match(
                chat_id,
                match_id
            )

        return "OK"


    # =====================================================
    # NORMAL MESSAGE
    # =====================================================

    message = update.get("message")

    if not message:

        return "OK"

    chat_id = message["chat"]["id"]

    text = message.get(
        "text",
        ""
    ).strip()


    # =====================================================
    # OWNER ONLY
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
            "يمكنك مشاهدة المباريات وتحليلها بالذكاء الاصطناعي.",
            main_keyboard()
        )

        return "OK"


    # =====================================================
    # TODAY
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
    # TOMORROW
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
    # LEAGUES
    # =====================================================

    if text == "🏆 الدوريات":

        show_leagues(chat_id)

        return "OK"


    # =====================================================
    # ANALYSIS HELP
    # =====================================================

    if text == "🤖 تحليل مباراة":

        send_message(
            chat_id,
            "⚽ اختر «مباريات اليوم» أو «الدوريات»، "
            "ثم اضغط زر 🤖 تحليل بجانب المباراة."
        )

        return "OK"


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
        os.getenv("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
