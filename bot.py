import os
import json
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, request
from openai import OpenAI


# =========================================================
# APP
# =========================================================

app = Flask(__name__)


# =========================================================
# ENV
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")


TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

FOOTBALL_API_URL = "https://v3.football.api-sports.io"

ALGERIA_TZ = ZoneInfo("Africa/Algiers")


# =========================================================
# OPENAI
# =========================================================

client = None

if OPENAI_API_KEY:

    try:

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        print("✅ OpenAI connected")

    except Exception as e:

        print(
            "❌ OpenAI Error:",
            e
        )

else:

    print(
        "⚠️ OPENAI_API_KEY غير موجود"
    )


# =========================================================
# CACHE
# =========================================================

matches_cache = {}


# =========================================================
# OWNER
# =========================================================

def is_owner(chat_id):

    if not OWNER_CHAT_ID:

        print(
            "⚠️ OWNER_CHAT_ID غير موجود"
        )

        return False

    return str(chat_id) == str(
        OWNER_CHAT_ID
    )


# =========================================================
# TELEGRAM
# =========================================================

def telegram_request(
    method,
    data
):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=30
        )

        result = response.json()

        if not result.get("ok"):

            print(
                "❌ Telegram Error:",
                result
            )

        return result

    except Exception as e:

        print(
            "❌ Telegram Exception:",
            e
        )

        return None


def send_message(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data[
            "reply_markup"
        ] = keyboard

    return telegram_request(
        "sendMessage",
        data
    )


def answer_callback(
    callback_id
):

    return telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id":
                callback_id
        }
    )


# =========================================================
# KEYBOARD
# =========================================================

def main_keyboard():

    return {

        "keyboard": [

            ["🇩🇿 مباريات الجزائر اليوم"],

            ["📅 مباريات الجزائر غدًا"],

            ["🏆 البطولات الجزائرية"],

            ["🤖 تحليل مباراة"]

        ],

        "resize_keyboard": True
    }


# =========================================================
# API FOOTBALL
# =========================================================

def football_get(
    endpoint,
    params=None
):

    if not API_FOOTBALL_KEY:

        print(
            "❌ API_FOOTBALL_KEY غير موجود"
        )

        return None


    url = (
        FOOTBALL_API_URL
        + endpoint
    )


    headers = {

        "x-apisports-key":
            API_FOOTBALL_KEY
    }


    try:

        print(
            "================================"
        )

        print(
            "⚽ API-FOOTBALL REQUEST"
        )

        print(
            "URL:",
            url
        )

        print(
            "PARAMS:",
            params
        )


        response = requests.get(

            url,

            headers=headers,

            params=params,

            timeout=30

        )


        print(
            "STATUS:",
            response.status_code
        )


        print(
            "RESPONSE:",
            response.text[:2000]
        )


        print(
            "================================"
        )


        if response.status_code != 200:

            return None


        return response.json()


    except Exception as e:

        print(
            "❌ Football API Error:",
            e
        )

        return None


# =========================================================
# DATE
# =========================================================

def today():

    return datetime.now(
        ALGERIA_TZ
    ).strftime(
        "%Y-%m-%d"
    )


# =========================================================
# ALGERIAN LEAGUE IDs
# =========================================================

# API-Football Algeria
# Ligue 1 = 186
# Ligue 2 = 187

ALGERIA_LEAGUES = {

    "186":
        "🇩🇿 Ligue 1 الجزائر",

    "187":
        "🇩🇿 Ligue 2 الجزائر"

}


# =========================================================
# GET ALGERIAN MATCHES
# =========================================================

def get_algeria_matches(
    date
):

    all_matches = []


    # Ligue 1
    for league_id in [
        "186",
        "187"
    ]:

        data = football_get(

            "/fixtures",

            {
                "league":
                    league_id,

                "season":
                    2026,

                "date":
                    date,

                "timezone":
                    "Africa/Algiers"
            }

        )


        if not data:

            continue


        matches = data.get(
            "response",
            []
        )


        for match in matches:

            match[
                "_league_id"
            ] = league_id


        all_matches.extend(
            matches
        )


    return all_matches


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

            "❌ لا توجد مباريات جزائرية "
            "متاحة لهذا اليوم في مصدر البيانات."

        )

        return


    text = (
        f"{title}\n\n"
    )


    keyboard = []


    for match in matches[:30]:

        fixture = match.get(
            "fixture",
            {}
        )


        teams = match.get(
            "teams",
            {}
        )


        home = teams.get(
            "home",
            {}
        ).get(
            "name",
            "Home"
        )


        away = teams.get(
            "away",
            {}
        ).get(
            "name",
            "Away"
        )


        match_id = str(
            fixture.get(
                "id"
            )
        )


        date_time = fixture.get(
            "date",
            ""
        )


        try:

            dt = datetime.fromisoformat(
                date_time.replace(
                    "Z",
                    "+00:00"
                )
            )

            local_dt = dt.astimezone(
                ALGERIA_TZ
            )

            time = local_dt.strftime(
                "%H:%M"
            )

        except:

            time = "غير معروف"


        league_name = (
            match.get(
                "league",
                {}
            ).get(
                "name",
                "الجزائر"
            )
        )


        matches_cache[
            match_id
        ] = match


        text += (

            f"⚽ {home} × {away}\n"

            f"🏆 {league_name}\n"

            f"🕒 {time} بتوقيت الجزائر\n\n"

        )


        keyboard.append(

            [

                {

                    "text":
                        f"🤖 تحليل {home} × {away}",

                    "callback_data":
                        f"analysis:{match_id}"

                }

            ]

        )


    send_message(

        chat_id,

        text,

        {

            "inline_keyboard":
                keyboard

        }

    )


# =========================================================
# STANDINGS
# =========================================================

def get_standings(
    league_id
):

    data = football_get(

        "/standings",

        {

            "league":
                league_id,

            "season":
                2026

        }

    )


    if not data:

        return []


    return data.get(
        "response",
        []
    )


# =========================================================
# TEAM RECENT MATCHES
# =========================================================

def get_team_recent_matches(
    team_id
):

    if not team_id:

        return []


    data = football_get(

        "/fixtures",

        {

            "team":
                team_id,

            "last":
                5

        }

    )


    if not data:

        return []


    return data.get(
        "response",
        []
    )


# =========================================================
# TEAM PLAYERS
# =========================================================

def get_team_players(
    team_id
):

    if not team_id:

        return []


    data = football_get(

        "/players",

        {

            "team":
                team_id,

            "season":
                2026

        }

    )


    if not data:

        return []


    return data.get(
        "response",
        []
    )


# =========================================================
# MATCH DETAILS
# =========================================================

def get_match_details(
    match_id
):

    data = football_get(

        "/fixtures",

        {

            "id":
                match_id

        }

    )


    if not data:

        return None


    response = data.get(
        "response",
        []
    )


    if not response:

        return None


    return response[0]


# =========================================================
# PREPARE ANALYSIS
# =========================================================

def prepare_analysis(
    match
):

    teams = match.get(
        "teams",
        {}
    )


    home = teams.get(
        "home",
        {}
    )


    away = teams.get(
        "away",
        {}
    )


    home_id = home.get(
        "id"
    )


    away_id = away.get(
        "id"
    )


    league = match.get(
        "league",
        {}
    )


    league_id = league.get(
        "id"
    )


    print(
        "📊 Gathering analysis data..."
    )


    home_recent = (
        get_team_recent_matches(
            home_id
        )
    )


    away_recent = (
        get_team_recent_matches(
            away_id
        )
    )


    standings = (
        get_standings(
            league_id
        )
    )


    return {

        "match":
            match,

        "home_recent":
            home_recent,

        "away_recent":
            away_recent,

        "standings":
            standings

    }


# =========================================================
# AI ANALYSIS
# =========================================================

def analyze_with_ai(
    data
):

    if not client:

        return (

            "❌ OpenAI غير متصل.\n\n"

            "أضف OPENAI_API_KEY "
            "في Render."

        )


    match = data[
        "match"
    ]


    teams = match.get(
        "teams",
        {}
    )


    home = teams.get(
        "home",
        {}
    ).get(
        "name",
        "الفريق المضيف"
    )


    away = teams.get(
        "away",
        {}
    ).get(
        "name",
        "الفريق الضيف"
    )


    league = match.get(
        "league",
        {}
    ).get(
        "name",
        "الجزائر"
    )


    football_data = json.dumps(

        data,

        ensure_ascii=False,

        indent=2

    )


    prompt = f"""

أنت محلل كرة قدم محترف متخصص
في كرة القدم الجزائرية.

حلل المباراة التالية اعتمادًا على
البيانات الموجودة في JSON.

المباراة:

{home} ضد {away}

البطولة:

{league}

البيانات:

{football_data}


أريد النتيجة بالعربية.

استخدم الشكل التالي:

━━━━━━━━━━━━━━━━━━
🇩🇿 تحليل المباراة
━━━━━━━━━━━━━━━━━━

🏠 {home}

نسبة الفوز:
XX%

🤝 التعادل:

XX%

✈️ {away}

نسبة الفوز:
XX%

⚽ الأهداف المتوقعة:

{home}: X تقريبًا

{away}: X تقريبًا


🥅 الأقرب للتسجيل:

اذكر اللاعب فقط إذا كانت
البيانات تسمح بذلك.

إذا لم توجد بيانات كافية:
"لا توجد بيانات كافية"


🟨 البطاقات الصفراء:

X إلى X تقريبًا


🏆 الفريق الأقرب للفوز:

اسم الفريق


📊 النتيجة المحتملة:

X-X


📈 مستوى الثقة:

منخفض / متوسط / مرتفع


🧠 التحليل:

اكتب تحليلًا مختصرًا وقويًا
اعتمادًا على نتائج الفريقين،
الترتيب، الأداء الأخير،
وعامل الأرض.


قواعد مهمة:

- مجموع نسب الفوز والتعادل = 100%.
- لا تخترع أسماء اللاعبين.
- لا تخترع إحصائيات.
- إذا كانت البيانات ناقصة قل ذلك.
- الأهداف والبطاقات توقعات وليست ضمانًا.
- لا توجد نتيجة مضمونة.
- لا تعد المستخدم بالربح.
"""


    try:

        response = client.responses.create(

            model="gpt-5.6-luna",

            input=prompt

        )


        return response.output_text


    except Exception as e:

        print(
            "❌ OpenAI Error:",
            e
        )


        return (

            "❌ حدث خطأ أثناء التحليل.\n\n"

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

        "🤖 جاري تحليل المباراة...\n\n"

        "📊 النتائج السابقة\n"

        "🏆 ترتيب الفريقين\n"

        "⚽ الأداء الأخير\n"

        "🧠 التحليل بالذكاء الاصطناعي\n\n"

        "⏳ انتظر قليلًا..."

    )


    match = matches_cache.get(
        str(match_id)
    )


    if not match:

        match = get_match_details(
            match_id
        )


    if not match:

        send_message(

            chat_id,

            "❌ لم أجد المباراة."

        )

        return


    data = prepare_analysis(
        match
    )


    result = analyze_with_ai(
        data
    )


    if len(result) > 4000:

        for i in range(
            0,
            len(result),
            4000
        ):

            send_message(

                chat_id,

                result[
                    i:i + 4000
                ]

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

    return (
        "🇩🇿 Algeria Football AI is running!"
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)

def webhook():

    update = (
        request.get_json(
            silent=True
        )
        or {}
    )


    # =====================================================
    # CALLBACK
    # =====================================================

    callback = update.get(
        "callback_query"
    )


    if callback:

        chat_id = (
            callback[
                "message"
            ][
                "chat"
            ][
                "id"
            ]
        )


        answer_callback(
            callback["id"]
        )


        if not is_owner(
            chat_id
        ):

            return "OK"


        data = callback.get(
            "data",
            ""
        )


        if data.startswith(
            "analysis:"
        ):

            match_id = (
                data.split(":")[1]
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


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        send_message(

            chat_id,

            "🇩🇿⚽ أهلاً بك في\n"

            "Algeria Football AI 🤖\n\n"

            "تحليل كرة القدم الجزائرية "
            "بالذكاء الاصطناعي.\n\n"

            "اختر من القائمة:",

            main_keyboard()

        )

        return "OK"


    # =====================================================
    # TODAY
    # =====================================================

    if text == "🇩🇿 مباريات الجزائر اليوم":

        send_message(

            chat_id,

            "⏳ جاري البحث عن مباريات "
            "الجزائر اليوم..."

        )


        matches = get_algeria_matches(
            today()
        )


        show_matches(

            chat_id,

            matches,

            "🇩🇿 مباريات الجزائر اليوم"

        )


        return "OK"


    # =====================================================
    # TOMORROW
    # =====================================================

    if text == "📅 مباريات الجزائر غدًا":

        send_message(

            chat_id,

            "⏳ جاري البحث عن مباريات "
            "الجزائر غدًا..."

        )


        tomorrow = (
            datetime.now(
                ALGERIA_TZ
            ).strftime(
                "%Y-%m-%d"
            )
        )


        # حساب الغد
        from datetime import timedelta

        tomorrow = (

            datetime.now(
                ALGERIA_TZ
            )
            + timedelta(days=1)

        ).strftime(
            "%Y-%m-%d"
        )


        matches = get_algeria_matches(
            tomorrow
        )


        show_matches(

            chat_id,

            matches,

            "📅 مباريات الجزائر غدًا"

        )


        return "OK"


    # =====================================================
    # LEAGUES
    # =====================================================

    if text == "🏆 البطولات الجزائرية":

        keyboard = {

            "inline_keyboard": [

                [
                    {
                        "text":
                            "🇩🇿 Ligue 1",

                        "callback_data":
                            "league:186"
                    }
                ],

                [
                    {
                        "text":
                            "🇩🇿 Ligue 2",

                        "callback_data":
                            "league:187"
                    }
                ]

            ]

        }


        send_message(

            chat_id,

            "🏆 اختر البطولة:",

            keyboard

        )


        return "OK"


    # =====================================================
    # LEAGUE CALLBACK
    # =====================================================

    # يتم التعامل معه هنا أيضًا
    # لأن callback يصل إلى نفس المسار

    if text == "🤖 تحليل مباراة":

        send_message(

            chat_id,

            "⚽ اختر مباراة من قائمة "
            "المباريات، ثم اضغط زر 🤖 تحليل."

        )

        return "OK"


    send_message(

        chat_id,

        "استخدم أزرار القائمة أو أرسل /start."

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
