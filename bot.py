import os
import math
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, request


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# كود الدخول
ACCESS_CODE = "1230"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

TIMEZONE = ZoneInfo("Africa/Algiers")

# حفظ المستخدمين الذين قاموا بتفعيل الدخول
authorized_users = set()


# =========================================================
# SOURCES
# =========================================================
#
# مصدر مجاني ولا يحتاج API KEY
#
# Premier League
# Algerian Ligue 1
#
# =========================================================

ESPN_ENGLAND_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "soccer/eng.1/scoreboard"
)

ESPN_ALGERIA_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "soccer/alg.1/scoreboard"
)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================================================
# TIME
# =========================================================

def now_algeria():
    return datetime.now(TIMEZONE)


def today_string():
    return now_algeria().strftime("%Y%m%d")


def today_display():
    return now_algeria().strftime("%d/%m/%Y")


# =========================================================
# TELEGRAM
# =========================================================

def telegram_request(method, data):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=25
        )

        result = response.json()

        if not result.get("ok"):
            print("Telegram Error:", result)

        return result

    except Exception as e:

        print("Telegram Exception:", e)

        return None


def telegram_send(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
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
# KEYBOARDS
# =========================================================

def access_keyboard():

    return {
        "remove_keyboard": True
    }


def main_keyboard():

    return {
        "keyboard": [

            [
                "🇩🇿 مباريات الجزائر اليوم"
            ],

            [
                "🏴 مباريات إنجلترا اليوم"
            ],

            [
                "🔴 بث مباشر"
            ],

            [
                "ℹ️ معلومات البوت"
            ]

        ],

        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def live_keyboard():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "🔄 تحديث البث المباشر",
                    "callback_data": "refresh_live"
                }
            ]

        ]
    }


# =========================================================
# TEAM NAMES
# =========================================================

TEAM_NAMES = {

    # =====================================================
    # ALGERIA
    # =====================================================

    "MC Alger": "مولودية الجزائر",
    "Mouloudia Club d'Alger": "مولودية الجزائر",

    "CR Belouizdad": "شباب بلوزداد",

    "USM Alger": "اتحاد العاصمة",

    "JS Kabylie": "شبيبة القبائل",

    "ES Sétif": "وفاق سطيف",

    "ES Setif": "وفاق سطيف",

    "CS Constantine": "شباب قسنطينة",

    "ASO Chlef": "أولمبي الشلف",

    "MC Oran": "مولودية وهران",

    "JS Saoura": "شبيبة الساورة",

    "US Biskra": "اتحاد بسكرة",

    "USM Khenchela": "اتحاد خنشلة",

    "Olympique Akbou": "أولمبي أقبو",

    "Paradou AC": "بارادو",

    "NC Magra": "نجم مقرة",

    "Ben Aknoun": "نجم بن عكنون",

    "ES Mostaganem": "ترجي مستغانم",

    "MC El Bayadh": "مولودية البيض",

    "AS Khroub": "جمعية الخروب",

    "WA Tlemcen": "وداد تلمسان",


    # =====================================================
    # ENGLAND
    # =====================================================

    "Arsenal": "أرسنال",

    "Aston Villa": "أستون فيلا",

    "Bournemouth": "بورنموث",

    "Brentford": "برينتفورد",

    "Brighton & Hove Albion": "برايتون",

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

    "Wolverhampton Wanderers": "وولفرهامبتون",

    "Burnley": "بيرنلي",

}


def arabic_team(name):

    return TEAM_NAMES.get(
        name,
        name
    )


# =========================================================
# GET ESPN DATA
# =========================================================

def get_scoreboard(url, date=None):

    params = {}

    if date:
        params["dates"] = date

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        print(
            "SOURCE STATUS:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "SOURCE ERROR:",
                response.text[:500]
            )

            return []

        data = response.json()

        return data.get(
            "events",
            []
        )

    except Exception as e:

        print(
            "SOURCE EXCEPTION:",
            e
        )

        return []


# =========================================================
# PARSE MATCH
# =========================================================

def parse_event(event, league):

    try:

        competitions = event.get(
            "competitions",
            []
        )

        if not competitions:
            return None

        competition = competitions[0]

        competitors = competition.get(
            "competitors",
            []
        )

        home = None
        away = None

        for competitor in competitors:

            team = competitor.get(
                "team",
                {}
            )

            team_name = team.get(
                "displayName",
                "Unknown"
            )

            score = competitor.get(
                "score",
                "0"
            )

            item = {

                "name": arabic_team(team_name),

                "raw_name": team_name,

                "score": score

            }

            if competitor.get("home"):

                home = item

            else:

                away = item

        if not home or not away:

            return None

        status = competition.get(
            "status",
            {}
        )

        status_type = status.get(
            "type",
            {}
        )

        status_name = status_type.get(
            "name",
            ""
        )

        status_detail = status_type.get(
            "detail",
            ""
        )

        clock = status.get(
            "displayClock",
            ""
        )

        date_value = event.get(
            "date"
        )

        match_time = "غير محدد"

        if date_value:

            try:

                dt = datetime.fromisoformat(
                    date_value.replace(
                        "Z",
                        "+00:00"
                    )
                )

                dt = dt.astimezone(
                    TIMEZONE
                )

                match_time = dt.strftime(
                    "%H:%M"
                )

            except:
                pass

        return {

            "id": event.get("id"),

            "league": league,

            "home": home["name"],

            "away": away["name"],

            "home_score": home["score"],

            "away_score": away["score"],

            "time": match_time,

            "status": status_name,

            "status_detail": status_detail,

            "clock": clock,

            "raw_date": date_value

        }

    except Exception as e:

        print(
            "PARSE ERROR:",
            e
        )

        return None


# =========================================================
# TODAY MATCHES
# =========================================================

def get_algeria_matches():

    events = get_scoreboard(
        ESPN_ALGERIA_URL,
        today_string()
    )

    matches = []

    for event in events:

        match = parse_event(
            event,
            "🇩🇿 الدوري الجزائري"
        )

        if match:

            matches.append(match)

    return matches


def get_england_matches():

    events = get_scoreboard(
        ESPN_ENGLAND_URL,
        today_string()
    )

    matches = []

    for event in events:

        match = parse_event(
            event,
            "🏴 الدوري الإنجليزي الممتاز"
        )

        if match:

            matches.append(match)

    return matches


# =========================================================
# LIVE MATCHES
# =========================================================

def is_live(match):

    status = match.get(
        "status",
        ""
    )

    live_statuses = [

        "STATUS_IN_PROGRESS",

        "STATUS_HALFTIME",

        "STATUS_DELAYED"

    ]

    return status in live_statuses


def get_live_matches():

    matches = []

    # Algeria
    algeria = get_algeria_matches()

    # England
    england = get_england_matches()

    all_matches = (
        algeria
        +
        england
    )

    for match in all_matches:

        if is_live(match):

            matches.append(match)

    return matches


# =========================================================
# TEAM STRENGTH MODEL
# =========================================================

BASE_STRENGTH = {

    # Algeria

    "مولودية الجزائر": 1.25,

    "شباب بلوزداد": 1.20,

    "شبيبة القبائل": 1.15,

    "اتحاد العاصمة": 1.15,

    "شباب قسنطينة": 1.05,

    "وفاق سطيف": 1.05,

    "شبيبة الساورة": 1.00,

    "مولودية وهران": 0.95,

    "أولمبي الشلف": 0.95,

    "بارادو": 1.00,

    "أولمبي أقبو": 0.90,

    "اتحاد خنشلة": 0.90,

    "اتحاد بسكرة": 0.85,


    # England

    "مانشستر سيتي": 1.35,

    "ليفربول": 1.32,

    "أرسنال": 1.32,

    "تشيلسي": 1.18,

    "مانشستر يونايتد": 1.15,

    "نيوكاسل": 1.12,

    "أستون فيلا": 1.05,

    "توتنهام": 1.05,

    "برايتون": 1.00,

    "كريستال بالاس": 0.95,

    "فولهام": 0.92,

    "برينتفورد": 0.95,

    "إيفرتون": 0.88,

    "بورنموث": 0.95,

    "نوتنغهام فورست": 0.92,

    "ليدز يونايتد": 0.88,

    "سندرلاند": 0.82,

    "بيرنلي": 0.82,

    "وست هام": 0.95,

    "وولفرهامبتون": 0.85

}


def team_strength(team):

    return BASE_STRENGTH.get(
        team,
        1.0
    )


# =========================================================
# POISSON MODEL
# =========================================================

def poisson_probability(k, lam):

    if lam <= 0:

        return 0

    return (

        math.exp(-lam)

        *

        (lam ** k)

        /

        math.factorial(k)

    )


def outcome_probabilities(
    home_lambda,
    away_lambda
):

    home_win = 0

    draw = 0

    away_win = 0

    scores = []

    for home_goals in range(9):

        for away_goals in range(9):

            probability = (

                poisson_probability(
                    home_goals,
                    home_lambda
                )

                *

                poisson_probability(
                    away_goals,
                    away_lambda
                )

            )

            scores.append(
                (
                    home_goals,
                    away_goals,
                    probability
                )
            )

            if home_goals > away_goals:

                home_win += probability

            elif home_goals == away_goals:

                draw += probability

            else:

                away_win += probability

    return (

        home_win,

        draw,

        away_win,

        scores

    )


# =========================================================
# OVER / UNDER
# =========================================================

def under_probability(
    total_lambda,
    line
):

    max_goals = math.floor(line)

    result = 0

    for goals in range(
        max_goals + 1
    ):

        result += poisson_probability(
            goals,
            total_lambda
        )

    return result


def over_probability(
    total_lambda,
    line
):

    return max(

        0,

        1 -

        under_probability(
            total_lambda,
            line
        )

    )


# =========================================================
# BTTS
# =========================================================

def btts_probability(
    home_lambda,
    away_lambda
):

    home_zero = poisson_probability(
        0,
        home_lambda
    )

    away_zero = poisson_probability(
        0,
        away_lambda
    )

    both_zero = math.exp(

        -(

            home_lambda
            +
            away_lambda

        )

    )

    yes = (

        1
        -
        home_zero
        -
        away_zero
        +
        both_zero

    )

    return max(
        0,
        min(
            1,
            yes
        )
    )


# =========================================================
# MATCH ANALYSIS
# =========================================================

def calculate_analysis(match):

    home = match["home"]

    away = match["away"]

    home_strength = team_strength(
        home
    )

    away_strength = team_strength(
        away
    )

    league = match["league"]

    # Different goal environments

    if "الجزائري" in league:

        base_goal = 1.05

        home_advantage = 0.18

    else:

        base_goal = 1.35

        home_advantage = 0.22


    # Expected goals

    home_lambda = (

        base_goal
        *
        home_strength
        *
        (1 + home_advantage)

        /

        max(
            0.75,
            away_strength
        )

    )


    away_lambda = (

        base_goal
        *
        away_strength

        /

        max(
            0.75,
            home_strength
        )

    )


    # Realistic limits

    home_lambda = max(

        0.25,

        min(
            home_lambda,
            3.5
        )

    )


    away_lambda = max(

        0.20,

        min(
            away_lambda,
            3.2
        )

    )


    home_win, draw, away_win, scores = (

        outcome_probabilities(

            home_lambda,

            away_lambda

        )

    )


    scores.sort(

        key=lambda x: x[2],

        reverse=True

    )


    btts_yes = btts_probability(

        home_lambda,

        away_lambda

    )


    strongest = max(

        [

            (home, home_win),

            ("تعادل", draw),

            (away, away_win)

        ],

        key=lambda x: x[1]

    )[0]


    return {

        "home_lambda": home_lambda,

        "away_lambda": away_lambda,

        "home_win": home_win,

        "draw": draw,

        "away_win": away_win,

        "scores": scores[:5],

        "btts_yes": btts_yes,

        "btts_no": 1 - btts_yes,

        "strongest": strongest

    }


# =========================================================
# FORMAT
# =========================================================

def pct(value):

    return f"{value * 100:.1f}%"


def format_match_analysis(match):

    analysis = calculate_analysis(
        match
    )

    total_lambda = (

        analysis["home_lambda"]

        +

        analysis["away_lambda"]

    )


    home = match["home"]

    away = match["away"]


    text = []

    text.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    text.append(
        f"⚽ <b>{home} × {away}</b>"
    )

    text.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    text.append("")

    text.append(
        f"🏆 {match['league']}"
    )

    text.append(
        f"🕐 الساعة: {match['time']}"
    )

    text.append("")

    text.append(
        "📊 <b>احتمالات المباراة</b>"
    )

    text.append("")

    text.append(
        f"🏠 فوز {home}: "
        f"<b>{pct(analysis['home_win'])}</b>"
    )

    text.append(
        f"🤝 التعادل: "
        f"<b>{pct(analysis['draw'])}</b>"
    )

    text.append(
        f"✈️ فوز {away}: "
        f"<b>{pct(analysis['away_win'])}</b>"
    )

    text.append("")

    text.append(
        f"🎯 الأقرب: "
        f"<b>{analysis['strongest']}</b>"
    )

    text.append("")

    text.append(
        "⚽ <b>الأهداف المتوقعة</b>"
    )

    text.append(
        f"المعدل المتوقع: "
        f"<b>{total_lambda:.2f}</b> هدف"
    )

    text.append("")

    text.append(
        "📈 <b>Over / Under</b>"
    )

    lines = [

        0.5,

        1.5,

        2.5,

        3.5,

        4.5,

        5.5

    ]


    for line in lines:

        over = over_probability(

            total_lambda,

            line

        )


        under = 1 - over


        text.append(

            f"⚽ {line} | "

            f"Over <b>{pct(over)}</b> "

            f"• Under <b>{pct(under)}</b>"

        )


    text.append("")

    text.append(
        "🥅 <b>يسجل الفريقان</b>"
    )

    text.append(

        f"نعم: <b>{pct(analysis['btts_yes'])}</b>"

    )

    text.append(

        f"لا: <b>{pct(analysis['btts_no'])}</b>"

    )

    text.append("")

    text.append(
        "🔢 <b>النتائج الأكثر احتمالًا</b>"
    )

    for h, a, probability in analysis["scores"]:

        text.append(

            f"⚽ {h} - {a} "

            f"<b>{pct(probability)}</b>"

        )


    text.append("")

    text.append(
        "⚠️ <i>هذا تحليل احتمالي إحصائي وليس ضمانًا للنتيجة.</i>"
    )

    return "\n".join(text)


# =========================================================
# LIVE FORMAT
# =========================================================

def format_live_match(match):

    home = match["home"]

    away = match["away"]

    home_score = match["home_score"]

    away_score = match["away_score"]

    detail = match["status_detail"]

    clock = match["clock"]


    text = []

    text.append(
        "🔴 <b>بث مباشر</b>"
    )

    text.append("")

    text.append(
        f"🏆 {match['league']}"
    )

    text.append("")

    text.append(
        f"🏠 <b>{home}</b>"
    )

    text.append(
        f"⚽ <b>{home_score} - {away_score}</b>"
    )

    text.append(
        f"✈️ <b>{away}</b>"
    )

    text.append("")

    if clock:

        text.append(
            f"⏱️ {clock}"
        )

    if detail:

        text.append(
            f"📌 {detail}"
        )

    return "\n".join(text)


# =========================================================
# LIVE BUTTON
# =========================================================

def live_button(match):

    match_id = match.get("id")

    if not match_id:

        return None

    return {

        "inline_keyboard": [

            [

                {

                    "text": (
                        "📊 تحليل المباراة"
                    ),

                    "callback_data": (
                        f"analysis:{match_id}"
                    )

                }

            ]

        ]

    }


# =========================================================
# FIND MATCH BY ID
# =========================================================

def find_match(match_id):

    all_matches = (

        get_algeria_matches()

        +

        get_england_matches()

    )

    for match in all_matches:

        if str(match.get("id")) == str(match_id):

            return match

    return None


# =========================================================
# ACCESS CHECK
# =========================================================

def is_authorized(chat_id):

    return chat_id in authorized_users


# =========================================================
# CALLBACK
# =========================================================

def handle_callback(callback):

    callback_id = callback.get("id")

    message = callback.get(
        "message",
        {}
    )

    chat_id = (

        message
        .get("chat", {})
        .get("id")

    )

    data = callback.get(
        "data",
        ""
    )


    answer_callback(
        callback_id
    )


    if not is_authorized(chat_id):

        telegram_send(

            chat_id,

            "🔐 يجب إدخال كود الدخول أولًا."

        )

        return "ok"


    # -----------------------------------------------------
    # REFRESH LIVE
    # -----------------------------------------------------

    if data == "refresh_live":

        telegram_send(

            chat_id,

            "🔄 جاري تحديث البث المباشر..."

        )


        live_matches = get_live_matches()


        if not live_matches:

            telegram_send(

                chat_id,

                "🔴 لا توجد مباراة مباشرة حاليًا.\n\n"
                "اضغط على الزر لاحقًا للتحديث.",

                live_keyboard()

            )

            return "ok"


        for match in live_matches:

            telegram_send(

                chat_id,

                format_live_match(match),

                live_button(match)

            )


        telegram_send(

            chat_id,

            "🔄 يمكنك تحديث النتائج مرة أخرى:",

            live_keyboard()

        )

        return "ok"


    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    if data.startswith("analysis:"):

        match_id = data.split(
            ":",
            1
        )[1]


        telegram_send(

            chat_id,

            "🤖 جاري تحليل المباراة..."

        )


        match = find_match(
            match_id
        )


        if not match:

            telegram_send(

                chat_id,

                "❌ لم أتمكن من العثور على المباراة."

            )

            return "ok"


        telegram_send(

            chat_id,

            format_match_analysis(match)

        )

        return "ok"


    return "ok"


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    try:

        update = request.get_json(
            silent=True
        ) or {}


        # =================================================
        # CALLBACK
        # =================================================

        callback = update.get(
            "callback_query"
        )


        if callback:

            return handle_callback(
                callback
            )


        # =================================================
        # MESSAGE
        # =================================================

        message = update.get(
            "message"
        )


        if not message:

            return "ok"


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

            return "ok"


        # =================================================
        # START
        # =================================================

        if text == "/start":

            telegram_send(

                chat_id,

                "🔐 <b>مرحبًا بك</b>\n\n"
                "أدخل كود الدخول للمتابعة."

            )

            return "ok"


        # =================================================
        # ACCESS CODE
        # =================================================

        if text == ACCESS_CODE:

            authorized_users.add(
                chat_id
            )


            telegram_send(

                chat_id,

                "✅ <b>تم تفعيل الدخول بنجاح!</b>\n\n"
                "⚽ اختر الخدمة التي تريد استخدامها:",

                main_keyboard()

            )

            return "ok"


        # =================================================
        # CHECK ACCESS
        # =================================================

        if not is_authorized(chat_id):

            telegram_send(

                chat_id,

                "🔐 يجب إدخال كود الدخول أولًا.\n\n"
                "اكتب الكود للمتابعة."

            )

            return "ok"


        # =================================================
        # ALGERIA
        # =================================================

        if text == "🇩🇿 مباريات الجزائر اليوم":

            telegram_send(

                chat_id,

                "⏳ جاري البحث عن مباريات الجزائر اليوم..."

            )


            matches = get_algeria_matches()


            if not matches:

                telegram_send(

                    chat_id,

                    f"🇩🇿 لا توجد مباريات متاحة اليوم "
                    f"({today_display()}).",

                    main_keyboard()

                )

                return "ok"


            telegram_send(

                chat_id,

                f"🇩🇿 <b>مباريات الجزائر اليوم</b>\n"
                f"📅 {today_display()}\n\n"
                f"⚽ عدد المباريات: <b>{len(matches)}</b>",

                main_keyboard()

            )


            for match in matches:

                keyboard = {

                    "inline_keyboard": [

                        [

                            {

                                "text": (
                                    "📊 تحليل المباراة"
                                ),

                                "callback_data": (
                                    f"analysis:{match['id']}"
                                )

                            }

                        ]

                    ]

                }


                telegram_send(

                    chat_id,

                    f"⚽ <b>{match['home']} × {match['away']}</b>\n\n"
                    f"🕐 الساعة: {match['time']}\n"
                    f"🏆 {match['league']}",

                    keyboard

                )


            return "ok"


        # =================================================
        # ENGLAND
        # =================================================

        if text == "🏴 مباريات إنجلترا اليوم":

            telegram_send(

                chat_id,

                "⏳ جاري البحث عن مباريات إنجلترا اليوم..."

            )


            matches = get_england_matches()


            if not matches:

                telegram_send(

                    chat_id,

                    f"🏴 لا توجد مباريات متاحة اليوم "
                    f"({today_display()}).",

                    main_keyboard()

                )

                return "ok"


            telegram_send(

                chat_id,

                f"🏴 <b>مباريات إنجلترا اليوم</b>\n"
                f"📅 {today_display()}\n\n"
                f"⚽ عدد المباريات: <b>{len(matches)}</b>",

                main_keyboard()

            )


            for match in matches:

                keyboard = {

                    "inline_keyboard": [

                        [

                            {

                                "text": (
                                    "📊 تحليل المباراة"
                                ),

                                "callback_data": (
                                    f"analysis:{match['id']}"
                                )

                            }

                        ]

                    ]

                }


                telegram_send(

                    chat_id,

                    f"⚽ <b>{match['home']} × {match['away']}</b>\n\n"
                    f"🕐 الساعة: {match['time']}\n"
                    f"🏆 {match['league']}",

                    keyboard

                )


            return "ok"


        # =================================================
        # LIVE
        # =================================================

        if text == "🔴 بث مباشر":

            telegram_send(

                chat_id,

                "🔄 جاري البحث عن المباريات المباشرة..."

            )


            live_matches = get_live_matches()


            if not live_matches:

                telegram_send(

                    chat_id,

                    "🔴 <b>البث المباشر</b>\n\n"
                    "لا توجد مباراة مباشرة حاليًا.\n\n"
                    "يمكنك الضغط على تحديث لاحقًا.",

                    live_keyboard()

                )

                return "ok"


            telegram_send(

                chat_id,

                f"🔴 <b>المباريات المباشرة الآن</b>\n\n"
                f"عدد المباريات: <b>{len(live_matches)}</b>",

                live_keyboard()

            )


            for match in live_matches:

                telegram_send(

                    chat_id,

                    format_live_match(match),

                    live_button(match)

                )


            return "ok"


        # =================================================
        # INFO
        # =================================================

        if text == "ℹ️ معلومات البوت":

            telegram_send(

                chat_id,

                "ℹ️ <b>معلومات البوت</b>\n\n"
                "🇩🇿 الدوري الجزائري\n"
                "🏴 الدوري الإنجليزي الممتاز\n"
                "🔴 مباريات مباشرة\n"
                "📊 تحليل احتمالي للمباريات\n"
                "⚽ توقع عدد الأهداف\n"
                "📈 Over / Under\n"
                "🥅 احتمال تسجيل الفريقين\n"
                "🎯 النتائج الأكثر احتمالًا\n\n"
                "⚠️ التحليلات إحصائية واحتمالية وليست نتائج مضمونة.",

                main_keyboard()

            )

            return "ok"


        # =================================================
        # UNKNOWN
        # =================================================

        telegram_send(

            chat_id,

            "اختر أحد الخيارات من القائمة 👇",

            main_keyboard()

        )


        return "ok"


    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            e
        )

        return "ok"


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return (

        "Football Bot is running! "

        f"Date: {today_display()}"

    )


# =========================================================
# DEBUG
# =========================================================

@app.route(
    "/debug",
    methods=["GET"]
)
def debug():

    return {

        "date": today_display(),

        "algeria": get_algeria_matches(),

        "england": get_england_matches(),

        "live": get_live_matches()

    }


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(

        os.getenv(
            "PORT",
            "10000"
        )

    )


    app.run(

        host="0.0.0.0",

        port=port

    )
