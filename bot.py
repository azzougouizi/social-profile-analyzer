import os
import math
import requests
from datetime import datetime, timedelta
from flask import Flask, request

app = Flask(__name__)

# =========================
# إعدادات
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FOOTBALL_API = "https://v3.football.api-sports.io"

# الموسم الحالي
SEASON = 2026

# المنطقة الزمنية للجزائر
TIMEZONE = "Africa/Algiers"

# ذاكرة بسيطة لتقليل استهلاك API
cache = {}


# =========================
# Telegram
# =========================

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
        {"callback_query_id": callback_id}
    )


# =========================
# لوحة البوت
# =========================

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


# =========================
# API Football
# =========================

def football_get(endpoint, params=None):

    if not API_FOOTBALL_KEY:
        print("❌ API_FOOTBALL_KEY غير موجود")
        return None

    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    url = f"{FOOTBALL_API}/{endpoint}"

    try:

        print("⚽ API:", endpoint, params)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("📡 Status:", response.status_code)

        if response.status_code != 200:
            print("❌ API Error:", response.text[:1000])
            return None

        data = response.json()

        if data.get("errors"):
            print("❌ API errors:", data["errors"])

        return data

    except Exception as e:

        print("❌ Football API Exception:", e)
        return None


# =========================
# البحث عن البطولات الجزائرية
# =========================

def get_algeria_leagues():

    key = "algeria_leagues"

    if key in cache:
        return cache[key]

    data = football_get(
        "leagues",
        {
            "country": "Algeria",
            "season": SEASON
        }
    )

    if not data:
        return []

    leagues = []

    for item in data.get("response", []):

        league = item.get("league", {})

        league_id = league.get("id")
        name = league.get("name")

        if league_id and name:
            leagues.append({
                "id": league_id,
                "name": name
            })

    cache[key] = leagues

    return leagues


# =========================
# مباريات حسب التاريخ
# =========================

def get_fixtures_by_date(date):

    key = f"fixtures_{date}"

    if key in cache:
        return cache[key]

    data = football_get(
        "fixtures",
        {
            "date": date,
            "timezone": TIMEZONE
        }
    )

    if not data:
        return []

    fixtures = data.get("response", [])

    # نحتفظ بالمباريات الجزائرية فقط
    algeria_leagues = get_algeria_leagues()

    algeria_ids = {
        str(x["id"])
        for x in algeria_leagues
    }

    result = []

    for fixture in fixtures:

        league = fixture.get("league", {})
        league_id = str(league.get("id"))

        if league_id in algeria_ids:
            result.append(fixture)

    cache[key] = result

    return result


def get_today_fixtures():

    today = datetime.now().strftime("%Y-%m-%d")

    return get_fixtures_by_date(today)


def get_tomorrow_fixtures():

    tomorrow = (
        datetime.now() + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    return get_fixtures_by_date(tomorrow)


# =========================
# تنسيق الوقت
# =========================

def fixture_time(fixture):

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


# =========================
# عرض المباريات
# =========================

def show_fixtures(chat_id, fixtures, title):

    if not fixtures:

        send_message(
            chat_id,
            f"{title}\n\n"
            "❌ لا توجد مباريات جزائرية متاحة حاليًا."
        )

        return

    text = f"{title}\n\n"

    keyboard = []

    for fixture in fixtures[:20]:

        fixture_id = fixture.get("fixture", {}).get("id")

        teams = fixture.get("teams", {})

        home = teams.get("home", {}).get(
            "name",
            "الفريق المحلي"
        )

        away = teams.get("away", {}).get(
            "name",
            "الفريق الضيف"
        )

        league = fixture.get(
            "league",
            {}
        ).get(
            "name",
            "البطولة"
        )

        time = fixture_time(fixture)

        text += (
            f"⚽ {home} × {away}\n"
            f"🏆 {league}\n"
            f"🕒 {time}\n\n"
        )

        keyboard.append([
            {
                "text": f"🤖 تحليل {home} × {away}",
                "callback_data": f"analysis:{fixture_id}"
            }
        ])

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================
# بيانات الفريق الأخيرة
# =========================

def get_team_recent_matches(team_id):

    if not team_id:
        return []

    key = f"team_{team_id}_recent"

    if key in cache:
        return cache[key]

    data = football_get(
        "fixtures",
        {
            "team": team_id,
            "last": 5,
            "status": "FT"
        }
    )

    if not data:
        return []

    matches = data.get("response", [])

    cache[key] = matches

    return matches


# =========================
# حساب نتائج الفريق
# =========================

def calculate_team_form(team_id):

    matches = get_team_recent_matches(team_id)

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    for match in matches:

        teams = match.get("teams", {})
        goals = match.get("goals", {})

        home = teams.get("home", {})
        away = teams.get("away", {})

        home_id = home.get("id")
        away_id = away.get("id")

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        if team_id == home_id:

            goals_for += home_goals
            goals_against += away_goals

            if home_goals > away_goals:
                wins += 1

            elif home_goals == away_goals:
                draws += 1

            else:
                losses += 1

        elif team_id == away_id:

            goals_for += away_goals
            goals_against += home_goals

            if away_goals > home_goals:
                wins += 1

            elif away_goals == home_goals:
                draws += 1

            else:
                losses += 1

    total = wins + draws + losses

    if total == 0:

        return {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "win_rate": 0,
            "draw_rate": 0,
            "loss_rate": 0,
            "goals_for": 0,
            "goals_against": 0,
            "matches": 0
        }

    return {
        "wins": wins,
        "draws": draws,
        "losses": losses,

        "win_rate": wins / total * 100,
        "draw_rate": draws / total * 100,
        "loss_rate": losses / total * 100,

        "goals_for": goals_for,
        "goals_against": goals_against,

        "matches": total
    }


# =========================
# التوقعات الرسمية من API
# =========================

def get_prediction(fixture_id):

    data = football_get(
        "predictions",
        {
            "fixture": fixture_id
        }
    )

    if not data:
        return None

    response = data.get("response", [])

    if not response:
        return None

    return response[0]


# =========================
# تحليل المباراة
# =========================

def analyze_fixture(fixture):

    fixture_data = fixture.get("fixture", {})
    teams = fixture.get("teams", {})

    fixture_id = fixture_data.get("id")

    home = teams.get("home", {})
    away = teams.get("away", {})

    home_id = home.get("id")
    away_id = away.get("id")

    home_name = home.get("name", "الفريق الأول")
    away_name = away.get("name", "الفريق الثاني")

    # فورمة الفريقين
    home_form = calculate_team_form(home_id)
    away_form = calculate_team_form(away_id)

    # محاولة الحصول على توقعات API
    prediction = get_prediction(fixture_id)

    home_probability = None
    draw_probability = None
    away_probability = None

    predicted_score = None

    if prediction:

        predictions = prediction.get(
            "predictions",
            {}
        )

        percent = predictions.get(
            "percent",
            {}
        )

        home_probability = parse_percent(
            percent.get("home")
        )

        draw_probability = parse_percent(
            percent.get("draw")
        )

        away_probability = parse_percent(
            percent.get("away")
        )

        score = predictions.get(
            "goals",
            {}
        )

        # أحيانًا تأتي الأهداف المتوقعة
        home_goals = score.get("home")
        away_goals = score.get("away")

        if home_goals is not None and away_goals is not None:

            try:
                predicted_score = (
                    f"{float(home_goals):.1f} - "
                    f"{float(away_goals):.1f}"
                )
            except:
                pass

    # إذا لم تتوفر النسب من API
    # نحسب تقديرًا بسيطًا من الفورمة
    if (
        home_probability is None
        or draw_probability is None
        or away_probability is None
    ):

        home_strength = (
            home_form["win_rate"] + 5
        )

        away_strength = (
            away_form["win_rate"]
        )

        draw_strength = (
            (home_form["draw_rate"] +
             away_form["draw_rate"]) / 2
        )

        total = (
            home_strength +
            away_strength +
            draw_strength
        )

        if total <= 0:

            home_probability = 40
            draw_probability = 30
            away_probability = 30

        else:

            home_probability = (
                home_strength / total * 100
            )

            draw_probability = (
                draw_strength / total * 100
            )

            away_probability = (
                away_strength / total * 100
            )

    # تطبيع النسب لتساوي 100
    total_probability = (
        home_probability +
        draw_probability +
        away_probability
    )

    if total_probability > 0:

        home_probability = (
            home_probability /
            total_probability *
            100
        )

        draw_probability = (
            draw_probability /
            total_probability *
            100
        )

        away_probability = (
            away_probability /
            total_probability *
            100
        )

    # الأهداف المتوقعة
    home_avg_goals = 0
    away_avg_goals = 0

    if home_form["matches"] > 0:

        home_avg_goals = (
            home_form["goals_for"] /
            home_form["matches"]
        )

    if away_form["matches"] > 0:

        away_avg_goals = (
            away_form["goals_for"] /
            away_form["matches"]
        )

    expected_goals = (
        home_avg_goals +
        away_avg_goals
    )

    # نتيجة تقريبية
    if not predicted_score:

        home_expected = max(
            0,
            round(home_avg_goals * 0.7 + 0.4)
        )

        away_expected = max(
            0,
            round(away_avg_goals * 0.7 + 0.3)
        )

        predicted_score = (
            f"{home_expected} - {away_expected}"
        )

    # الأقرب للفوز
    probabilities = {
        home_name: home_probability,
        "التعادل": draw_probability,
        away_name: away_probability
    }

    winner = max(
        probabilities,
        key=probabilities.get
    )

    highest = probabilities[winner]

    if highest >= 65:
        confidence = "مرتفع"
    elif highest >= 50:
        confidence = "متوسط"
    else:
        confidence = "منخفض"

    # البطاقات
    # لا نخترع رقمًا دقيقًا إذا لم توجد بيانات
    yellow_cards = "غير متوفر"

    analysis = build_analysis_text(
        home_name,
        away_name,
        home_probability,
        draw_probability,
        away_probability,
        expected_goals,
        yellow_cards,
        winner,
        predicted_score,
        confidence,
        home_form,
        away_form
    )

    return analysis


# =========================
# تحويل النسبة
# =========================

def parse_percent(value):

    if value is None:
        return None

    try:

        value = str(value)

        value = (
            value
            .replace("%", "")
            .strip()
        )

        return float(value)

    except:

        return None


# =========================
# نص التحليل
# =========================

def build_analysis_text(
    home,
    away,
    home_probability,
    draw_probability,
    away_probability,
    expected_goals,
    yellow_cards,
    winner,
    predicted_score,
    confidence,
    home_form,
    away_form
):

    form_home = (
        f"{home_form['wins']} فوز / "
        f"{home_form['draws']} تعادل / "
        f"{home_form['losses']} خسارة"
    )

    form_away = (
        f"{away_form['wins']} فوز / "
        f"{away_form['draws']} تعادل / "
        f"{away_form['losses']} خسارة"
    )

    return f"""
━━━━━━━━━━━━━━━━━━
🇩🇿 ⚽ تحليل المباراة
━━━━━━━━━━━━━━━━━━

🏠 {home}

🟢 نسبة الفوز:
{home_probability:.1f}%

📊 آخر النتائج:
{form_home}


🤝 التعادل:

{draw_probability:.1f}%


✈️ {away}

🔵 نسبة الفوز:
{away_probability:.1f}%

📊 آخر النتائج:
{form_away}


⚽ الأهداف المتوقعة:

حوالي {expected_goals:.1f} هدف


🟨 البطاقات الصفراء:

{yellow_cards}


🏆 الأقرب للفوز:

{winner}


📊 النتيجة المحتملة:

{predicted_score}


📈 مستوى الثقة:

{confidence}


🧠 التحليل:

تم الاعتماد على بيانات المباراة وفورمة الفريقين
والبيانات المتاحة من API.

⚠️ هذه توقعات إحصائية وليست نتيجة مضمونة.
━━━━━━━━━━━━━━━━━━
"""


# =========================
# تحليل مباراة من ID
# =========================

def analyze_match(chat_id, fixture_id):

    send_message(
        chat_id,
        "🤖 جاري جمع البيانات...\n"
        "⏳ انتظر قليلًا..."
    )

    data = football_get(
        "fixtures",
        {
            "id": fixture_id
        }
    )

    if not data:

        send_message(
            chat_id,
            "❌ لم أتمكن من الحصول على بيانات المباراة."
        )

        return

    fixtures = data.get("response", [])

    if not fixtures:

        send_message(
            chat_id,
            "❌ المباراة غير موجودة."
        )

        return

    fixture = fixtures[0]

    result = analyze_fixture(fixture)

    # Telegram لديه حد لحجم الرسالة
    if len(result) > 4000:

        for i in range(0, len(result), 4000):

            send_message(
                chat_id,
                result[i:i + 4000]
            )

    else:

        send_message(
            chat_id,
            result
        )


# =========================
# عرض البطولات الجزائرية
# =========================

def show_leagues(chat_id):

    leagues = get_algeria_leagues()

    if not leagues:

        send_message(
            chat_id,
            "❌ لم أتمكن من تحميل البطولات الجزائرية."
        )

        return

    keyboard = []

    for league in leagues:

        keyboard.append([
            {
                "text": f"🏆 {league['name']}",
                "callback_data": (
                    f"league:{league['id']}"
                )
            }
        ])

    send_message(
        chat_id,
        "🇩🇿 اختر البطولة:",
        {
            "inline_keyboard": keyboard
        }
    )


# =========================
# مباريات بطولة
# =========================

def get_league_fixtures(league_id):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    data = football_get(
        "fixtures",
        {
            "league": league_id,
            "season": SEASON,
            "from": today,
            "to": (
                datetime.now() +
                timedelta(days=7)
            ).strftime("%Y-%m-%d"),
            "timezone": TIMEZONE
        }
    )

    if not data:
        return []

    return data.get("response", [])


# =========================
# Webhook
# =========================

@app.route("/", methods=["GET"])
def home():

    return "🇩🇿 Algeria Football AI is running!"


@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    update = (
        request.get_json(
            silent=True
        ) or {}
    )

    # =====================
    # الأزرار
    # =====================

    callback = update.get(
        "callback_query"
    )

    if callback:

        message = callback.get(
            "message",
            {}
        )

        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get("id")

        answer_callback(
            callback.get("id")
        )

        callback_data = callback.get(
            "data",
            ""
        )

        # تحليل مباراة
        if callback_data.startswith(
            "analysis:"
        ):

            fixture_id = (
                callback_data
                .split(":", 1)[1]
            )

            analyze_match(
                chat_id,
                fixture_id
            )

            return "OK"

        # بطولة
        if callback_data.startswith(
            "league:"
        ):

            league_id = (
                callback_data
                .split(":", 1)[1]
            )

            fixtures = get_league_fixtures(
                league_id
            )

            show_fixtures(
                chat_id,
                fixtures,
                "🏆 مباريات البطولة"
            )

            return "OK"

        return "OK"

    # =====================
    # الرسائل
    # =====================

    message = update.get(
        "message"
    )

    if not message:
        return "OK"

    chat_id = message.get(
        "chat",
        {}
    ).get("id")

    text = (
        message.get("text", "")
        .strip()
    )

    # /start
    if text == "/start":

        send_message(
            chat_id,
            "🇩🇿⚽ أهلاً بك في بوت تحليل كرة القدم الجزائرية 🤖\n\n"
            "يمكنك مشاهدة مباريات الجزائر وتحليلها.",
            main_keyboard()
        )

        return "OK"

    # مباريات اليوم
    if text == "🇩🇿 مباريات الجزائر اليوم":

        send_message(
            chat_id,
            "⏳ جاري البحث عن مباريات الجزائر اليوم..."
        )

        fixtures = get_today_fixtures()

        show_fixtures(
            chat_id,
            fixtures,
            "🇩🇿 مباريات الجزائر اليوم"
        )

        return "OK"

    # مباريات الغد
    if text == "📅 مباريات الجزائر غدًا":

        send_message(
            chat_id,
            "⏳ جاري البحث عن مباريات الجزائر غدًا..."
        )

        fixtures = get_tomorrow_fixtures()

        show_fixtures(
            chat_id,
            fixtures,
            "📅 مباريات الجزائر غدًا"
        )

        return "OK"

    # البطولات
    if text == "🏆 البطولات الجزائرية":

        show_leagues(chat_id)

        return "OK"

    # التحليل
    if text == "🤖 تحليل مباراة":

        send_message(
            chat_id,
            "⚽ اختر «مباريات الجزائر اليوم» "
            "أو «البطولات الجزائرية»، "
            "ثم اضغط زر 🤖 تحليل بجانب المباراة."
        )

        return "OK"

    send_message(
        chat_id,
        "استخدم /start لعرض القائمة."
    )

    return "OK"


# =========================
# تشغيل Render
# =========================

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
