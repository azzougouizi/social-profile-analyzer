import os
import requests
from datetime import datetime, timezone
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALLDATA_API_KEY = os.getenv("FOOTBALLDATA_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FOOTBALL_API = "https://footballdata.io/api/v1"

TIMEZONE_NAME = "Africa/Algiers"

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
# FOOTBALLDATA.IO API
# =========================================================

def football_get(endpoint, params=None, cache_key=None):

    if not FOOTBALLDATA_API_KEY:
        print("❌ FOOTBALLDATA_API_KEY غير موجود في Render")
        return None

    if cache_key and cache_key in cache:
        return cache[cache_key]

    headers = {
        "Authorization": f"Bearer {FOOTBALLDATA_API_KEY}",
        "Accept": "application/json"
    }

    url = f"{FOOTBALL_API}/{endpoint.lstrip('/')}"

    try:
        print("================================")
        print("⚽ FOOTBALLDATA REQUEST")
        print("Endpoint:", endpoint)
        print("Params:", params)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("Status:", response.status_code)

        try:
            data = response.json()
        except Exception:
            print("❌ API لم ترجع JSON")
            print(response.text[:1500])
            return None

        if response.status_code != 200:
            print("❌ API ERROR:", data)
            return None

        if not data.get("success", True):
            print("⚠️ API ERROR:", data)
            return None

        if cache_key:
            cache[cache_key] = data

        return data

    except Exception as e:
        print("❌ API Exception:", e)
        return None


# =========================================================
# GENERIC HELPERS
# =========================================================

def get_data(data):
    """
    Footballdata.io قد يعيد:
    data = [...]
    أو data = {...}
    """
    if not data:
        return None

    return data.get("data")


def as_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        # حالات شائعة
        for key in [
            "matches",
            "fixtures",
            "leagues",
            "results",
            "items"
        ]:
            if isinstance(value.get(key), list):
                return value[key]

    return []


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


# =========================================================
# FIND ALGERIAN LEAGUES
# =========================================================

def get_algerian_leagues():

    cache_key = "algerian_leagues"

    data = football_get(
        "leagues",
        {
            "country": "Algeria"
        },
        cache_key
    )

    if not data:
        return []

    raw = get_data(data)

    leagues = as_list(raw)

    print("🇩🇿 Algerian competitions:")

    for league in leagues:
        league_id = (
            league.get("league_id")
            or league.get("id")
        )

        name = (
            league.get("league_name")
            or league.get("name")
            or ""
        )

        print(
            "ID:",
            league_id,
            "|",
            name
        )

    return leagues


def get_league_id(league_type):

    leagues = get_algerian_leagues()

    wanted = (
        "ligue 1"
        if league_type == "L1"
        else "ligue 2"
    )

    # البحث الدقيق أولاً
    for league in leagues:

        name = normalize_text(
            league.get("league_name")
            or league.get("name")
        )

        if name == wanted:

            return (
                league.get("league_id")
                or league.get("id")
            )

    # بحث مرن
    for league in leagues:

        name = normalize_text(
            league.get("league_name")
            or league.get("name")
        )

        if wanted in name:

            return (
                league.get("league_id")
                or league.get("id")
            )

    print(
        "❌ لم يتم العثور على League ID:",
        league_type
    )

    return None


# =========================================================
# TODAY
# =========================================================

def get_algeria_today():
    """
    تاريخ الجزائر.
    الخادم قد يكون UTC، لذلك نستخدم تاريخ النظام
    مع محاولة الاعتماد على التاريخ الحالي.
    """

    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")


# =========================================================
# TODAY FIXTURES
# =========================================================

def get_today_fixtures(league_type):

    league_id = get_league_id(
        league_type
    )

    if not league_id:
        return []

    today = get_algeria_today()

    cache_key = (
        f"today_{league_type}_{today}"
    )

    # حسب توثيق Footballdata:
    # /matches?date=YYYY-MM-DD&league_id=...
    data = football_get(
        "matches",
        {
            "date": today,
            "league_id": league_id,
            "limit": 100
        },
        cache_key
    )

    if not data:
        return []

    raw = get_data(data)

    matches = as_list(raw)

    return matches


# =========================================================
# MATCH FIELD HELPERS
# =========================================================

def get_team(match, side):

    teams = match.get(
        "teams",
        {}
    )

    if isinstance(teams, dict):

        team = teams.get(
            side,
            {}
        )

        if isinstance(team, dict):
            return team

    # بعض الاستجابات قد تستخدم home_team / away_team
    team = match.get(
        f"{side}_team",
        {}
    )

    if isinstance(team, dict):
        return team

    return {}


def get_team_id(match, side):

    team = get_team(
        match,
        side
    )

    return (
        team.get("team_id")
        or team.get("id")
    )


def get_team_name(match, side):

    team = get_team(
        match,
        side
    )

    return (
        team.get("team_name")
        or team.get("name")
        or "غير معروف"
    )


def get_match_id(match):

    return (
        match.get("match_id")
        or match.get("id")
    )


def get_match_date(match):

    return (
        match.get("date")
        or match.get("match_date")
        or match.get("datetime")
        or match.get("kickoff")
    )


def get_match_time(match):

    date_value = get_match_date(
        match
    )

    if not date_value:
        return "غير معروف"

    try:

        value = str(
            date_value
        )

        dt = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

        return dt.strftime(
            "%H:%M"
        )

    except Exception:

        # إذا كان النص يحتوي الوقت مباشرة
        if "T" in str(date_value):

            try:
                return str(
                    date_value
                ).split("T")[1][:5]

            except Exception:
                pass

        return "غير معروف"


def get_status(match):

    status = (
        match.get("status")
        or match.get("match_status")
        or ""
    )

    if isinstance(status, dict):

        status = (
            status.get("short")
            or status.get("name")
            or status.get("status")
            or ""
        )

    status = normalize_text(
        status
    )

    mapping = {
        "ns": "لم تبدأ",
        "scheduled": "لم تبدأ",
        "not started": "لم تبدأ",

        "live": "مباشر 🔴",
        "1h": "مباشر 🔴",
        "2h": "مباشر 🔴",

        "ht": "استراحة ⏸️",

        "ft": "انتهت ✅",
        "finished": "انتهت ✅",

        "pst": "مؤجلة",
        "postponed": "مؤجلة",

        "canc": "ملغاة",
        "cancelled": "ملغاة"
    }

    return mapping.get(
        status,
        status or "غير معروف"
    )


# =========================================================
# SCORE
# =========================================================

def get_scores(match):

    scores = (
        match.get("scores")
        or match.get("score")
        or {}
    )

    if not isinstance(scores, dict):
        return None, None

    home = (
        scores.get("home")
    )

    away = (
        scores.get("away")
    )

    # إذا كانت home/away عبارة عن dict
    if isinstance(home, dict):
        home = (
            home.get("score")
            or home.get("goals")
            or home.get("current")
        )

    if isinstance(away, dict):
        away = (
            away.get("score")
            or away.get("goals")
            or away.get("current")
        )

    # محاولة ثانية
    if home is None:
        home = match.get(
            "home_score"
        )

    if away is None:
        away = match.get(
            "away_score"
        )

    return home, away


# =========================================================
# SHOW MATCHES
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

    name = (
        "🇩🇿 Ligue 1"
        if league_type == "L1"
        else "🇩🇿 Ligue 2"
    )

    if not fixtures:

        send_message(
            chat_id,
            f"{name}\n\n"
            "❌ لا توجد مباريات متاحة اليوم.\n\n"
            "إذا كنت متأكدًا من وجود مباريات، "
            "راجع Logs في Render لمعرفة رد API."
        )

        return

    text = (
        f"{name}\n"
        f"📅 مباريات اليوم\n\n"
    )

    keyboard = []

    for match in fixtures:

        match_id = get_match_id(
            match
        )

        home_name = get_team_name(
            match,
            "home"
        )

        away_name = get_team_name(
            match,
            "away"
        )

        home_score, away_score = (
            get_scores(match)
        )

        status = get_status(
            match
        )

        time = get_match_time(
            match
        )

        if (
            home_score is not None
            and away_score is not None
        ):

            score_text = (
                f"⚽ {home_score} - "
                f"{away_score}"
            )

        else:

            score_text = (
                f"🕒 {time}"
            )

        text += (
            f"🏠 {home_name}\n"
            f"✈️ {away_name}\n"
            f"{score_text}\n"
            f"📌 {status}\n\n"
        )

        if match_id:

            keyboard.append([
                {
                    "text": (
                        f"🔎 تحليل "
                        f"{home_name} × {away_name}"
                    ),
                    "callback_data": (
                        f"analysis:{match_id}"
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
# GET MATCH DETAILS
# =========================================================

def get_match(match_id):

    cache_key = (
        f"match_{match_id}"
    )

    data = football_get(
        f"matches/{match_id}",
        cache_key=cache_key
    )

    if not data:
        return None

    raw = get_data(data)

    if isinstance(raw, dict):

        # أحيانًا response يحتوي match
        if isinstance(
            raw.get("match"),
            dict
        ):
            return raw["match"]

        return raw

    if isinstance(raw, list) and raw:
        return raw[0]

    return None


# =========================================================
# PROBABILITIES
# =========================================================

def get_probabilities(match_id):

    cache_key = (
        f"probabilities_{match_id}"
    )

    data = football_get(
        f"matches/{match_id}/probabilities",
        cache_key=cache_key
    )

    if not data:
        return {}

    raw = get_data(data)

    if not isinstance(raw, dict):
        return {}

    if isinstance(
        raw.get("probabilities"),
        dict
    ):
        return raw["probabilities"]

    return raw


# =========================================================
# STATS
# =========================================================

def get_match_stats(match_id):

    cache_key = (
        f"stats_{match_id}"
    )

    data = football_get(
        f"matches/{match_id}/stats",
        cache_key=cache_key
    )

    if not data:
        return {}

    raw = get_data(data)

    if not isinstance(raw, dict):
        return {}

    if isinstance(
        raw.get("stats"),
        dict
    ):
        return raw["stats"]

    return raw


# =========================================================
# EVENTS
# =========================================================

def get_match_events(match_id):

    cache_key = (
        f"events_{match_id}"
    )

    data = football_get(
        f"matches/{match_id}/events",
        cache_key=cache_key
    )

    if not data:
        return []

    raw = get_data(data)

    return as_list(raw)


# =========================================================
# EXTRACT PROBABILITY
# =========================================================

def parse_number(value):

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:

        return float(
            str(value)
            .replace("%", "")
            .strip()
        )

    except Exception:

        return None


def extract_winner_probabilities(probabilities):

    home = None
    draw = None
    away = None

    winner = probabilities.get(
        "match_winner"
    )

    if isinstance(winner, dict):

        home = parse_number(
            winner.get("home")
        )

        draw = parse_number(
            winner.get("draw")
        )

        away = parse_number(
            winner.get("away")
        )

    # احتمال وجود شكل آخر
    if home is None:
        home = parse_number(
            probabilities.get("home")
        )

    if draw is None:
        draw = parse_number(
            probabilities.get("draw")
        )

    if away is None:
        away = parse_number(
            probabilities.get("away")
        )

    return home, draw, away


# =========================================================
# FORM FROM TEAM MATCHES
# =========================================================

def get_team_recent_matches(team_id):

    if not team_id:
        return []

    cache_key = (
        f"team_matches_{team_id}"
    )

    data = football_get(
        f"teams/{team_id}/matches",
        {
            "limit": 5
        },
        cache_key
    )

    if not data:
        return []

    raw = get_data(data)

    return as_list(raw)


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

        status = get_status(
            match
        )

        if "انتهت" not in status:

            raw_status = normalize_text(
                match.get("status")
            )

            if raw_status not in [
                "ft",
                "finished"
            ]:
                continue

        home_id = get_team_id(
            match,
            "home"
        )

        away_id = get_team_id(
            match,
            "away"
        )

        hg, ag = get_scores(
            match
        )

        hg = parse_number(hg)
        ag = parse_number(ag)

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
# PROBABILITY FALLBACK
# =========================================================

def calculate_fallback_probabilities(
    home_form,
    away_form
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

        return 40.0, 30.0, 30.0

    home = (
        home_strength
        / total
        * 100
    )

    draw = (
        draw_strength
        / total
        * 100
    )

    away = (
        away_strength
        / total
        * 100
    )

    return home, draw, away


# =========================================================
# STATS HELPERS
# =========================================================

def find_stat(
    stats,
    names
):

    if not isinstance(stats, dict):
        return None

    for name in names:

        if name in stats:

            value = stats[name]

            if isinstance(value, dict):

                # home / away
                return value

            return value

    # البحث غير حساس لحالة الأحرف
    for key, value in stats.items():

        key_normalized = normalize_text(
            key
        )

        for name in names:

            if key_normalized == normalize_text(
                name
            ):
                return value

    return None


def extract_card_stats(stats):

    yellow = find_stat(
        stats,
        [
            "yellow_cards",
            "yellow",
            "cards_yellow"
        ]
    )

    red = find_stat(
        stats,
        [
            "red_cards",
            "red",
            "cards_red"
        ]
    )

    return yellow, red


def format_stat_pair(value):

    if isinstance(value, dict):

        home = (
            value.get("home")
            or value.get("host")
        )

        away = (
            value.get("away")
            or value.get("guest")
        )

        if home is not None or away is not None:

            return (
                f"{home if home is not None else '-'} "
                f"- "
                f"{away if away is not None else '-'}"
            )

    if value is not None:
        return str(value)

    return "غير متوفر"


# =========================================================
# EXPECTED GOALS
# =========================================================

def extract_xg(stats):

    xg = find_stat(
        stats,
        [
            "xg_prematch",
            "xg",
            "expected_goals"
        ]
    )

    if isinstance(xg, dict):

        home = parse_number(
            xg.get("home")
        )

        away = parse_number(
            xg.get("away")
        )

        total = parse_number(
            xg.get("total")
        )

        return home, away, total

    return None, None, None


# =========================================================
# BUILD ANALYSIS
# =========================================================

def analyze_match(match_id):

    match = get_match(
        match_id
    )

    if not match:
        return (
            "❌ لم أتمكن من العثور "
            "على بيانات المباراة."
        )

    home_name = get_team_name(
        match,
        "home"
    )

    away_name = get_team_name(
        match,
        "away"
    )

    home_id = get_team_id(
        match,
        "home"
    )

    away_id = get_team_id(
        match,
        "away"
    )

    league_info = (
        match.get("league")
        or {}
    )

    if isinstance(
        league_info,
        dict
    ):

        league_name = (
            league_info.get("league_name")
            or league_info.get("name")
            or "الدوري الجزائري"
        )

    else:

        league_name = "الدوري الجزائري"

    status = get_status(
        match
    )

    # =====================================================
    # FORM
    # =====================================================

    home_form = calculate_form(
        home_id
    )

    away_form = calculate_form(
        away_id
    )

    # =====================================================
    # PROBABILITIES
    # =====================================================

    probabilities = get_probabilities(
        match_id
    )

    home_prob, draw_prob, away_prob = (
        extract_winner_probabilities(
            probabilities
        )
    )

    if (
        home_prob is None
        or draw_prob is None
        or away_prob is None
    ):

        (
            home_prob,
            draw_prob,
            away_prob
        ) = calculate_fallback_probabilities(
            home_form,
            away_form
        )

        probability_source = (
            "📊 محسوبة من الفورمة الأخيرة"
        )

    else:

        probability_source = (
            "📊 من بيانات Footballdata"
        )

    # Normalize
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

    # =====================================================
    # STATS
    # =====================================================

    stats = get_match_stats(
        match_id
    )

    yellow_cards, red_cards = (
        extract_card_stats(stats)
    )

    yellow_text = format_stat_pair(
        yellow_cards
    )

    red_text = format_stat_pair(
        red_cards
    )

    # =====================================================
    # XG
    # =====================================================

    xg_home, xg_away, xg_total = (
        extract_xg(stats)
    )

    if xg_home is None:

        if home_form["played"] > 0:
            xg_home = (
                home_form["goals_for"]
                /
                home_form["played"]
            )
        else:
            xg_home = 0.0

    if xg_away is None:

        if away_form["played"] > 0:
            xg_away = (
                away_form["goals_for"]
                /
                away_form["played"]
            )
        else:
            xg_away = 0.0

    if xg_total is None:

        xg_total = (
            xg_home + xg_away
        )

    # =====================================================
    # PREDICTED SCORE
    # =====================================================

    predicted_home = max(
        0,
        round(xg_home)
    )

    predicted_away = max(
        0,
        round(xg_away)
    )

    predicted_score = (
        f"{predicted_home} - "
        f"{predicted_away}"
    )

    # =====================================================
    # WINNER
    # =====================================================

    probabilities_list = [
        (home_name, home_prob),
        ("التعادل", draw_prob),
        (away_name, away_prob)
    ]

    winner, highest = max(
        probabilities_list,
        key=lambda x: x[1]
    )

    if highest >= 70:
        confidence = "🟢 مرتفعة"

    elif highest >= 55:
        confidence = "🟡 متوسطة"

    else:
        confidence = "🟠 منخفضة"

    # =====================================================
    # FORM
    # =====================================================

    home_form_text = (
        f"{home_form['wins']} فوز | "
        f"{home_form['draws']} تعادل | "
        f"{home_form['losses']} خسارة | "
        f"{home_form['goals_for']} له | "
        f"{home_form['goals_against']} عليه"
    )

    away_form_text = (
        f"{away_form['wins']} فوز | "
        f"{away_form['draws']} تعادل | "
        f"{away_form['losses']} خسارة | "
        f"{away_form['goals_for']} له | "
        f"{away_form['goals_against']} عليه"
    )

    # =====================================================
    # CURRENT SCORE
    # =====================================================

    current_home, current_away = (
        get_scores(match)
    )

    current_score_text = ""

    if (
        current_home is not None
        and current_away is not None
    ):

        current_score_text = (
            "\n⚽ النتيجة الحالية: "
            f"{current_home} - "
            f"{current_away}\n"
        )

    # =====================================================
    # EXTRA DATA
    # =====================================================

    shots = find_stat(
        stats,
        [
            "shots"
        ]
    )

    possession = find_stat(
        stats,
        [
            "possession"
        ]
    )

    corners = find_stat(
        stats,
        [
            "corners"
        ]
    )

    shots_text = format_stat_pair(
        shots
    )

    possession_text = format_stat_pair(
        possession
    )

    corners_text = format_stat_pair(
        corners
    )

    # =====================================================
    # FINAL
    # =====================================================

    result = f"""
━━━━━━━━━━━━━━━━━━━━
🇩🇿 ⚽ تحليل المباراة
━━━━━━━━━━━━━━━━━━━━

🏆 البطولة:
{league_name}

🏠 {home_name}

🟢 احتمال الفوز:
{home_prob:.1f}%

📊 آخر المباريات:
{home_form_text}


🤝 احتمال التعادل:
{draw_prob:.1f}%


✈️ {away_name}

🔵 احتمال الفوز:
{away_prob:.1f}%

📊 آخر المباريات:
{away_form_text}


🏆 الأقرب للفوز:
{winner}

📈 مستوى الثقة:
{confidence}

⚽ الأهداف المتوقعة:
{ xg_home:.1f } - { xg_away:.1f }

🎯 النتيجة المحتملة:
{predicted_score}

📊 مجموع الأهداف المتوقع:
{ xg_total:.1f }

🟨 البطاقات الصفراء:
{yellow_text}

🟥 البطاقات الحمراء:
{red_text}

🚩 الركنيات:
{corners_text}

🎯 التسديدات:
{shots_text}

📊 الاستحواذ:
{possession_text}

📌 حالة المباراة:
{status}
{current_score_text}

{probability_source}

⚠️ التحليل إحصائي وليس ضمانًا لنتيجة المباراة.
━━━━━━━━━━━━━━━━━━━━
"""

    return result


# =========================================================
# CALLBACK
# =========================================================

def handle_callback(callback):

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

    if data.startswith(
        "analysis:"
    ):

        match_id = data.split(
            ":",
            1
        )[1]

        send_message(
            chat_id,
            "🤖 جاري تحليل المباراة...\n"
            "⏳ انتظر قليلًا..."
        )

        result = analyze_match(
            match_id
        )

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
        "is running with Footballdata.io!"
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
