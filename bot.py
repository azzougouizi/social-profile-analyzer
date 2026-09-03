import os
import requests
from datetime import datetime

from flask import Flask, request

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FOOTBALL_API = "https://v3.football.api-sports.io"

SEASON = 2026
TIMEZONE = "Africa/Algiers"

# Cache لتقليل استهلاك API
cache = {}


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
            print("❌ Telegram:", result)

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

    return telegram_request("sendMessage", data)


def answer_callback(callback_id):
    return telegram_request(
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
            ["🇩🇿 Ligue 1"],
            ["🇩🇿 Ligue 2"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


# =========================================================
# API FOOTBALL
# =========================================================

def football_get(endpoint, params=None, cache_key=None):

    if not API_FOOTBALL_KEY:
        print("❌ API_FOOTBALL_KEY غير موجود")
        return None

    if cache_key and cache_key in cache:
        return cache[cache_key]

    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    url = f"{FOOTBALL_API}/{endpoint}"

    try:

        print("================================")
        print("⚽ API REQUEST")
        print("Endpoint:", endpoint)
        print("Params:", params)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("Status:", response.status_code)

        if response.status_code != 200:
            print("❌ API ERROR:", response.text[:1500])
            return None

        data = response.json()

        if data.get("errors"):
            print("⚠️ API errors:", data["errors"])

        if cache_key:
            cache[cache_key] = data

        return data

    except Exception as e:

        print("❌ API Exception:", e)
        return None


# =========================================================
# FIND ALGERIAN LEAGUE IDs
# =========================================================

def get_algerian_league_id(league_type):

    cache_key = "algerian_league_ids"

    data = football_get(
        "leagues",
        {
            "country": "Algeria",
            "season": SEASON
        },
        cache_key
    )

    if not data:
        return None

    leagues = data.get("response", [])

    print("🇩🇿 Algerian competitions:")

    for item in leagues:

        league = item.get("league", {})
        league_id = league.get("id")
        name = league.get("name", "")

        print(league_id, name)

        normalized = name.lower()

        if league_type == "L1":

            if (
                "ligue 1" in normalized
                or "league 1" in normalized
            ):
                return league_id

        if league_type == "L2":

            if (
                "ligue 2" in normalized
                or "league 2" in normalized
            ):
                return league_id

    return None


# =========================================================
# TODAY FIXTURES
# =========================================================

def get_today_fixtures(league_type):

    league_id = get_algerian_league_id(
        league_type
    )

    if not league_id:
        print(
            "❌ لم يتم العثور على League ID:",
            league_type
        )
        return []

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cache_key = f"{league_type}_{today}"

    data = football_get(
        "fixtures",
        {
            "league": league_id,
            "season": SEASON,
            "date": today,
            "timezone": TIMEZONE
        },
        cache_key
    )

    if not data:
        return []

    return data.get("response", [])


# =========================================================
# FORMAT MATCH
# =========================================================

def get_match_time(fixture):

    date = (
        fixture
        .get("fixture", {})
        .get("date")
    )

    if not date:
        return "غير معروف"

    try:

        dt = datetime.fromisoformat(
            date.replace("Z", "+00:00")
        )

        return dt.strftime("%H:%M")

    except:

        return "غير معروف"


def get_match_status(fixture):

    status = (
        fixture
        .get("fixture", {})
        .get("status", {})
    )

    short = status.get("short", "")
    elapsed = status.get("elapsed")

    if short == "NS":
        return "لم تبدأ"

    if short == "1H":
        return f"مباشر 🔴 {elapsed or ''}'"

    if short == "2H":
        return f"مباشر 🔴 {elapsed or ''}'"

    if short == "HT":
        return "استراحة ⏸️"

    if short == "FT":
        return "انتهت ✅"

    if short == "PST":
        return "مؤجلة"

    if short == "CANC":
        return "ملغاة"

    return short or "غير معروف"


# =========================================================
# SHOW LEAGUE MATCHES
# =========================================================

def show_league_matches(
    chat_id,
    league_type
):

    send_message(
        chat_id,
        "⏳ جاري تحميل مباريات اليوم..."
    )

    fixtures = get_today_fixtures(
        league_type
    )

    if not fixtures:

        name = (
            "Ligue 1"
            if league_type == "L1"
            else "Ligue 2"
        )

        send_message(
            chat_id,
            f"🇩🇿 {name}\n\n"
            "❌ لا توجد مباريات متاحة اليوم "
            "أو أن API-Football لم يوفر بيانات هذه البطولة."
        )

        return

    name = (
        "🇩🇿 Ligue 1"
        if league_type == "L1"
        else "🇩🇿 Ligue 2"
    )

    text = (
        f"{name}\n"
        f"📅 مباريات اليوم\n\n"
    )

    keyboard = []

    for fixture in fixtures:

        fixture_id = (
            fixture
            .get("fixture", {})
            .get("id")
        )

        teams = fixture.get(
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

        home_name = home.get(
            "name",
            "الفريق الأول"
        )

        away_name = away.get(
            "name",
            "الفريق الثاني"
        )

        home_logo = home.get(
            "logo"
        )

        away_logo = away.get(
            "logo"
        )

        score = fixture.get(
            "goals",
            {}
        )

        home_score = score.get(
            "home"
        )

        away_score = score.get(
            "away"
        )

        status = get_match_status(
            fixture
        )

        time = get_match_time(
            fixture
        )

        # إذا المباراة لم تبدأ
        if home_score is None:
            score_text = f"🕒 {time}"
        else:
            score_text = (
                f"⚽ {home_score} - "
                f"{away_score}"
            )

        text += (
            f"🏠 {home_name}\n"
            f"✈️ {away_name}\n"
            f"{score_text}\n"
            f"📌 {status}\n\n"
        )

        if fixture_id:

            keyboard.append([
                {
                    "text": (
                        f"🔎 تحليل "
                        f"{home_name} × {away_name}"
                    ),
                    "callback_data": (
                        f"analysis:{fixture_id}"
                    )
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
# GET FIXTURE
# =========================================================

def get_fixture(fixture_id):

    data = football_get(
        "fixtures",
        {
            "id": fixture_id
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
# PREDICTION
# =========================================================

def get_prediction(fixture_id):

    cache_key = (
        f"prediction_{fixture_id}"
    )

    data = football_get(
        "predictions",
        {
            "fixture": fixture_id
        },
        cache_key
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
# RECENT TEAM FORM
# =========================================================

def get_team_recent_matches(team_id):

    if not team_id:
        return []

    cache_key = (
        f"team_recent_{team_id}"
    )

    data = football_get(
        "fixtures",
        {
            "team": team_id,
            "last": 5
        },
        cache_key
    )

    if not data:
        return []

    return data.get(
        "response",
        []
    )


def calculate_form(
    team_id
):

    matches = get_team_recent_matches(
        team_id
    )

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    played = 0

    for match in matches:

        status = (
            match
            .get("fixture", {})
            .get("status", {})
            .get("short")
        )

        if status != "FT":
            continue

        teams = match.get(
            "teams",
            {}
        )

        goals = match.get(
            "goals",
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

        home_id = home.get("id")
        away_id = away.get("id")

        hg = goals.get("home")
        ag = goals.get("away")

        if hg is None or ag is None:
            continue

        if team_id == home_id:

            gf = hg
            ga = ag

        elif team_id == away_id:

            gf = ag
            ga = hg

        else:
            continue

        played += 1

        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1

        elif gf == ga:
            draws += 1

        else:
            losses += 1

    if played == 0:

        return {
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "win_rate": 0,
            "draw_rate": 0,
            "goals_for": 0,
            "goals_against": 0
        }

    return {
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": wins / played * 100,
        "draw_rate": draws / played * 100,
        "goals_for": goals_for,
        "goals_against": goals_against
    }


# =========================================================
# PERCENT
# =========================================================

def parse_percent(value):

    if value is None:
        return None

    try:

        return float(
            str(value)
            .replace("%", "")
            .strip()
        )

    except:

        return None


# =========================================================
# PREDICTED SCORE
# =========================================================

def predicted_score_from_api(
    prediction
):

    if not prediction:
        return None

    predictions = prediction.get(
        "predictions",
        {}
    )

    goals = predictions.get(
        "goals",
        {}
    )

    home = goals.get(
        "home"
    )

    away = goals.get(
        "away"
    )

    if home is None or away is None:
        return None

    try:

        return (
            f"{float(home):.1f} - "
            f"{float(away):.1f}"
        )

    except:

        return None


# =========================================================
# BUILD ANALYSIS
# =========================================================

def analyze_match(
    fixture_id
):

    fixture = get_fixture(
        fixture_id
    )

    if not fixture:
        return (
            "❌ لم أتمكن من العثور "
            "على بيانات المباراة."
        )

    teams = fixture.get(
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

    home_id = home.get("id")
    away_id = away.get("id")

    home_name = home.get(
        "name",
        "الفريق الأول"
    )

    away_name = away.get(
        "name",
        "الفريق الثاني"
    )

    league = fixture.get(
        "league",
        {}
    ).get(
        "name",
        "الجزائر"
    )

    match_status = get_match_status(
        fixture
    )

    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    prediction = get_prediction(
        fixture_id
    )

    home_prob = None
    draw_prob = None
    away_prob = None

    predicted_winner = None
    advice = None

    if prediction:

        predictions = prediction.get(
            "predictions",
            {}
        )

        percent = predictions.get(
            "percent",
            {}
        )

        home_prob = parse_percent(
            percent.get("home")
        )

        draw_prob = parse_percent(
            percent.get("draw")
        )

        away_prob = parse_percent(
            percent.get("away")
        )

        winner = predictions.get(
            "winner"
        )

        if winner:

            predicted_winner = winner.get(
                "name"
            )

        advice = predictions.get(
            "advice"
        )

    # -----------------------------------------------------
    # Recent form
    # -----------------------------------------------------

    home_form = calculate_form(
        home_id
    )

    away_form = calculate_form(
        away_id
    )

    # -----------------------------------------------------
    # Fallback probabilities
    # -----------------------------------------------------

    if (
        home_prob is None
        or draw_prob is None
        or away_prob is None
    ):

        home_strength = (
            home_form["win_rate"] + 5
        )

        away_strength = (
            away_form["win_rate"]
        )

        draw_strength = (
            (
                home_form["draw_rate"]
                +
                away_form["draw_rate"]
            ) / 2
        )

        total = (
            home_strength
            +
            away_strength
            +
            draw_strength
        )

        if total <= 0:

            home_prob = 40
            draw_prob = 30
            away_prob = 30

        else:

            home_prob = (
                home_strength
                / total
                * 100
            )

            draw_prob = (
                draw_strength
                / total
                * 100
            )

            away_prob = (
                away_strength
                / total
                * 100
            )

    # -----------------------------------------------------
    # Normalize
    # -----------------------------------------------------

    total = (
        home_prob
        +
        draw_prob
        +
        away_prob
    )

    if total > 0:

        home_prob = (
            home_prob / total * 100
        )

        draw_prob = (
            draw_prob / total * 100
        )

        away_prob = (
            away_prob / total * 100
        )

    # -----------------------------------------------------
    # Expected goals
    # -----------------------------------------------------

    home_avg = 0
    away_avg = 0

    if home_form["played"] > 0:

        home_avg = (
            home_form["goals_for"]
            /
            home_form["played"]
        )

    if away_form["played"] > 0:

        away_avg = (
            away_form["goals_for"]
            /
            away_form["played"]
        )

    expected_goals = (
        home_avg + away_avg
    )

    # -----------------------------------------------------
    # Score
    # -----------------------------------------------------

    predicted_score = (
        predicted_score_from_api(
            prediction
        )
    )

    if not predicted_score:

        home_score = max(
            0,
            round(home_avg)
        )

        away_score = max(
            0,
            round(away_avg)
        )

        predicted_score = (
            f"{home_score} - "
            f"{away_score}"
        )

    # -----------------------------------------------------
    # Winner
    # -----------------------------------------------------

    probabilities = [
        (home_name, home_prob),
        ("التعادل", draw_prob),
        (away_name, away_prob)
    ]

    winner, highest = max(
        probabilities,
        key=lambda x: x[1]
    )

    if highest >= 70:
        confidence = "🟢 مرتفعة"

    elif highest >= 55:
        confidence = "🟡 متوسطة"

    else:
        confidence = "🟠 منخفضة"

    # -----------------------------------------------------
    # Current score
    # -----------------------------------------------------

    goals = fixture.get(
        "goals",
        {}
    )

    current_home = goals.get(
        "home"
    )

    current_away = goals.get(
        "away"
    )

    current_score = ""

    if (
        current_home is not None
        and current_away is not None
    ):

        current_score = (
            f"\n\n⚽ النتيجة الحالية: "
            f"{current_home} - "
            f"{current_away}"
        )

    # -----------------------------------------------------
    # Form text
    # -----------------------------------------------------

    home_form_text = (
        f"{home_form['wins']} فوز | "
        f"{home_form['draws']} تعادل | "
        f"{home_form['losses']} خسارة"
    )

    away_form_text = (
        f"{away_form['wins']} فوز | "
        f"{away_form['draws']} تعادل | "
        f"{away_form['losses']} خسارة"
    )

    # -----------------------------------------------------
    # API advice
    # -----------------------------------------------------

    advice_text = ""

    if advice:
        advice_text = (
            f"\n💡 توصية النموذج:\n"
            f"{advice}\n"
        )

    # -----------------------------------------------------
    # Final
    # -----------------------------------------------------

    result = f"""
━━━━━━━━━━━━━━━━━━━━
🇩🇿 ⚽ تحليل المباراة
━━━━━━━━━━━━━━━━━━━━

🏆 البطولة:
{league}

🏠 {home_name}

🟢 احتمال الفوز:
{home_prob:.1f}%

📊 آخر 5 مباريات:
{home_form_text}


🤝 التعادل:

{draw_prob:.1f}%


✈️ {away_name}

🔵 احتمال الفوز:
{away_prob:.1f}%

📊 آخر 5 مباريات:
{away_form_text}


⚽ الأهداف المتوقعة:

حوالي {expected_goals:.1f} هدف


🏆 الأقرب للفوز:

{winner}


📊 النتيجة المحتملة:

{predicted_score}


📈 مستوى الثقة:

{confidence}


📌 حالة المباراة:

{match_status}
{current_score}

🧠 التحليل:

تمت مقارنة احتمالات الفريقين مع
الفورمة الأخيرة والبيانات المتاحة
من API-Football.
{advice_text}
⚠️ هذه توقعات إحصائية وليست نتيجة مضمونة.
━━━━━━━━━━━━━━━━━━━━
"""

    return result


# =========================================================
# CALLBACK
# =========================================================

def handle_callback(
    callback
):

    callback_id = callback.get(
        "id"
    )

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

    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    if data.startswith(
        "analysis:"
    ):

        fixture_id = data.split(
            ":",
            1
        )[1]

        send_message(
            chat_id,
            "🤖 جاري تحليل المباراة...\n"
            "⏳ انتظر قليلًا..."
        )

        result = analyze_match(
            fixture_id
        )

        # Telegram message limit
        if len(result) <= 4000:

            send_message(
                chat_id,
                result
            )

        else:

            for i in range(
                0,
                len(result),
                4000
            ):

                send_message(
                    chat_id,
                    result[i:i + 4000]
                )

        return "OK"

    return "OK"


# =========================================================
# WEB
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return (
        "🇩🇿 Algeria Football Bot "
        "is running!"
    )


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

        return handle_callback(
            callback
        )

    # =====================================================
    # MESSAGE
    # =====================================================

    message = update.get(
        "message"
    )

    if not message:
        return "OK"

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

    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        send_message(
            chat_id,
            "🇩🇿⚽ مرحبًا بك في بوت "
            "تحليل كرة القدم الجزائرية\n\n"
            "اختر البطولة:",
            main_keyboard()
        )

        return "OK"

    # =====================================================
    # LIGUE 1
    # =====================================================

    if text == "🇩🇿 Ligue 1":

        show_league_matches(
            chat_id,
            "L1"
        )

        return "OK"

    # =====================================================
    # LIGUE 2
    # =====================================================

    if text == "🇩🇿 Ligue 2":

        show_league_matches(
            chat_id,
            "L2"
        )

        return "OK"

    # =====================================================
    # UNKNOWN
    # =====================================================

    send_message(
        chat_id,
        "استخدم /start لعرض البطولات."
    )

    return "OK"


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
