import os
import math
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, request


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

TZ = ZoneInfo("Africa/Algiers")


# =========================================================
# SOFASCORE
# =========================================================

SOFA_BASE = "https://www.sofascore.com/api/v1"

# Algerian Ligue 1
ALGERIA_TOURNAMENT_ID = 841

# Premier League
ENGLAND_TOURNAMENT_ID = 17


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# =========================================================
# TEAM NAME TRANSLATION
# =========================================================

TEAM_NAMES = {

    # -------------------------
    # Algeria
    # -------------------------

    "Chlef": "أولمبي الشلف",
    "ASO Chlef": "أولمبي الشلف",

    "Belouizdad": "شباب بلوزداد",
    "CR Belouizdad": "شباب بلوزداد",

    "Temouchent": "شباب تموشنت",
    "CR Temouchent": "شباب تموشنت",

    "Constantine": "شباب قسنطينة",
    "CS Constantine": "شباب قسنطينة",

    "Kabylie": "شبيبة القبائل",
    "JS Kabylie": "شبيبة القبائل",

    "Saoura": "شبيبة الساورة",
    "JS Saoura": "شبيبة الساورة",

    "Rouissat": "مستقبل الرويسات",
    "MB Rouissat": "مستقبل الرويسات",

    "MC Alger": "مولودية الجزائر",

    "Oran": "مولودية وهران",
    "MC Oran": "مولودية وهران",

    "Biskra": "اتحاد بسكرة",
    "US Biskra": "اتحاد بسكرة",

    "USM Alger": "اتحاد العاصمة",

    "Khenchela": "اتحاد خنشلة",
    "USM Khenchela": "اتحاد خنشلة",

    "Sétif": "وفاق سطيف",
    "ES Sétif": "وفاق سطيف",

    "Ben Aknoun": "نجم بن عكنون",
    "ES Ben Aknoun": "نجم بن عكنون",

    "El Biar": "شبيبة الأبيار",
    "Biar": "شبيبة الأبيار",

    "Olympique Akbou": "أولمبي أقبو",
    "Akbou": "أولمبي أقبو",

    # -------------------------
    # England
    # -------------------------

    "Manchester City": "مانشستر سيتي",
    "Manchester United": "مانشستر يونايتد",
    "Liverpool": "ليفربول",
    "Arsenal": "أرسنال",
    "Chelsea": "تشيلسي",
    "Tottenham": "توتنهام",
    "Tottenham Hotspur": "توتنهام",
    "Newcastle": "نيوكاسل",
    "Newcastle United": "نيوكاسل",
    "Aston Villa": "أستون فيلا",
    "Everton": "إيفرتون",
    "Fulham": "فولهام",
    "Crystal Palace": "كريستال بالاس",
    "Brighton": "برايتون",
    "Brighton & Hove Albion": "برايتون",
    "Brentford": "برينتفورد",
    "Sunderland": "سندرلاند",
    "Leeds": "ليدز يونايتد",
    "Leeds United": "ليدز يونايتد",
    "Bournemouth": "بورنموث",
    "AFC Bournemouth": "بورنموث",
    "Nottingham Forest": "نوتنغهام فورست",
    "Coventry": "كوفنتري",
    "Coventry City": "كوفنتري",
    "Hull": "هال سيتي",
    "Hull City": "هال سيتي",
    "Ipswich": "إيبسويتش",
    "Ipswich Town": "إيبسويتش",
}


def team_name(name):

    if not name:
        return "غير معروف"

    return TEAM_NAMES.get(
        name,
        name
    )


# =========================================================
# TIME
# =========================================================

def now_algeria():

    return datetime.now(TZ)


def today_string():

    return now_algeria().strftime("%Y-%m-%d")


# =========================================================
# SOFASCORE REQUEST
# =========================================================

def sofa_get(endpoint):

    url = SOFA_BASE + endpoint

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if response.status_code != 200:

            print(
                "Sofascore HTTP:",
                response.status_code,
                endpoint
            )

            return None

        return response.json()

    except Exception as e:

        print(
            "Sofascore ERROR:",
            endpoint,
            e
        )

        return None


# =========================================================
# TODAY EVENTS
# =========================================================

def get_today_events():

    date = today_string()

    data = sofa_get(
        f"/sport/football/scheduled-events/{date}"
    )

    if not data:

        return []

    events = data.get(
        "events",
        []
    )

    return events


# =========================================================
# FILTER LEAGUES
# =========================================================

def get_league_matches(league):

    if league == "algeria":

        tournament_id = ALGERIA_TOURNAMENT_ID

    elif league == "england":

        tournament_id = ENGLAND_TOURNAMENT_ID

    else:

        return []

    events = get_today_events()

    matches = []

    for event in events:

        tournament = event.get(
            "tournament",
            {}
        )

        unique = tournament.get(
            "uniqueTournament",
            {}
        )

        event_tournament_id = unique.get(
            "id"
        )

        if event_tournament_id != tournament_id:
            continue

        home = event.get(
            "homeTeam",
            {}
        )

        away = event.get(
            "awayTeam",
            {}
        )

        home_id = home.get("id")
        away_id = away.get("id")

        if not home_id or not away_id:
            continue

        timestamp = event.get(
            "startTimestamp"
        )

        if timestamp:

            dt = datetime.fromtimestamp(
                timestamp,
                TZ
            )

            date = dt.strftime(
                "%Y-%m-%d"
            )

            time = dt.strftime(
                "%H:%M"
            )

        else:

            date = today_string()
            time = "غير محدد"

        matches.append({

            "event_id": event.get("id"),

            "league": (
                "🇩🇿 الدوري الجزائري"
                if league == "algeria"
                else
                "🏴 الدوري الإنجليزي الممتاز"
            ),

            "home": team_name(
                home.get("name")
            ),

            "away": team_name(
                away.get("name")
            ),

            "home_original": home.get(
                "name"
            ),

            "away_original": away.get(
                "name"
            ),

            "home_id": home_id,
            "away_id": away_id,

            "date": date,
            "time": time,

            "status": event.get(
                "status",
                {}
            ),

            "event": event,
        })

    # Remove duplicates
    unique_matches = {}

    for match in matches:

        unique_matches[
            match["event_id"]
        ] = match

    return list(
        unique_matches.values()
    )


# =========================================================
# EVENT DETAILS
# =========================================================

def get_event_details(event_id):

    return sofa_get(
        f"/event/{event_id}"
    )


# =========================================================
# LINEUPS
# =========================================================

def get_lineups(event_id):

    data = sofa_get(
        f"/event/{event_id}/lineups"
    )

    if not data:

        return None

    return data


# =========================================================
# PLAYER NAME
# =========================================================

def player_name(player):

    if not player:
        return "غير معروف"

    return (
        player.get("name")
        or player.get("shortName")
        or "غير معروف"
    )


# =========================================================
# FORMAT PLAYER
# =========================================================

def format_player(item):

    player = item.get(
        "player",
        {}
    )

    name = player_name(player)

    shirt = item.get(
        "shirtNumber"
    )

    if shirt:

        return f"{shirt} - {name}"

    return name


# =========================================================
# FORMATION
# =========================================================

def formation_text(team_data):

    formation = team_data.get(
        "formation"
    )

    if formation:

        return str(
            formation
        )

    return "غير محددة"


# =========================================================
# OFFICIAL LINEUP CHECK
# =========================================================

def lineup_is_official(lineups):

    if not lineups:

        return False

    home = lineups.get(
        "home"
    )

    away = lineups.get(
        "away"
    )

    if not home or not away:

        return False

    home_players = home.get(
        "players",
        []
    )

    away_players = away.get(
        "players",
        []
    )

    # Usually the official lineup contains
    # starting XI with statistics/status.
    #
    # We don't invent it if source has no players.

    return (
        len(home_players) > 0
        and
        len(away_players) > 0
    )


# =========================================================
# LINEUP MESSAGE
# =========================================================

def format_lineup(
    match,
    mode
):

    lineups = get_lineups(
        match["event_id"]
    )

    home = match["home"]
    away = match["away"]

    # -----------------------------------------------------
    # No lineup
    # -----------------------------------------------------

    if not lineups:

        if mode == "predicted":

            return (
                f"🧩 <b>التشكيلة المحتملة</b>\n\n"
                f"⚽ {home} × {away}\n\n"
                "⚠️ لا توجد تشكيلة متوقعة متاحة "
                "حاليًا من المصدر."
            )

        return (
            f"✅ <b>التشكيلة الأساسية</b>\n\n"
            f"⚽ {home} × {away}\n\n"
            "⏳ لم يتم الإعلان عن التشكيلة "
            "الأساسية بعد."
        )

    home_data = lineups.get(
        "home",
        {}
    )

    away_data = lineups.get(
        "away",
        {}
    )

    # -----------------------------------------------------
    # Official
    # -----------------------------------------------------

    if mode == "official":

        if not lineup_is_official(
            lineups
        ):

            return (
                f"⏳ <b>التشكيلة الأساسية</b>\n\n"
                f"⚽ {home} × {away}\n\n"
                "لم يتم الإعلان عن التشكيلة "
                "الأساسية رسميًا بعد."
            )

    title = (
        "🧩 التشكيلة المحتملة"
        if mode == "predicted"
        else
        "✅ التشكيلة الأساسية"
    )

    text = []

    text.append(
        f"<b>{title}</b>"
    )

    text.append(
        f"⚽ {home} × {away}"
    )

    text.append("")

    # =====================================================
    # HOME
    # =====================================================

    text.append(
        f"🏠 <b>{home}</b>"
    )

    text.append(
        f"📐 الخطة: "
        f"{formation_text(home_data)}"
    )

    home_players = home_data.get(
        "players",
        []
    )

    starters = []
    substitutes = []

    for item in home_players:

        # SofaScore uses sub flag
        sub = item.get(
            "substitute",
            False
        )

        if sub:

            substitutes.append(
                format_player(item)
            )

        else:

            starters.append(
                format_player(item)
            )

    if starters:

        text.append("")
        text.append("🔹 <b>الأساسيون</b>")

        for player in starters[:11]:

            text.append(
                f"• {player}"
            )

    if mode == "official" and substitutes:

        text.append("")
        text.append("🔄 <b>البدلاء</b>")

        for player in substitutes:

            text.append(
                f"• {player}"
            )

    # =====================================================
    # AWAY
    # =====================================================

    text.append("")
    text.append(
        f"✈️ <b>{away}</b>"
    )

    text.append(
        f"📐 الخطة: "
        f"{formation_text(away_data)}"
    )

    away_players = away_data.get(
        "players",
        []
    )

    starters = []
    substitutes = []

    for item in away_players:

        sub = item.get(
            "substitute",
            False
        )

        if sub:

            substitutes.append(
                format_player(item)
            )

        else:

            starters.append(
                format_player(item)
            )

    if starters:

        text.append("")
        text.append("🔹 <b>الأساسيون</b>")

        for player in starters[:11]:

            text.append(
                f"• {player}"
            )

    if mode == "official" and substitutes:

        text.append("")
        text.append("🔄 <b>البدلاء</b>")

        for player in substitutes:

            text.append(
                f"• {player}"
            )

    text.append("")

    if mode == "predicted":

        text.append(
            "ℹ️ هذه تشكيلة متوقعة وليست رسمية."
        )

    else:

        text.append(
            "✅ التشكيلة مأخوذة من بيانات "
            "المباراة بعد إعلانها."
        )

    return "\n".join(text)


# =========================================================
# MATCH KEYBOARD
# =========================================================

def match_keyboard(event_id):

    return {

        "inline_keyboard": [

            [
                {
                    "text": "📊 التحليل",
                    "callback_data":
                    f"analysis:{event_id}"
                }
            ],

            [
                {
                    "text": "🧩 التشكيلة المحتملة",
                    "callback_data":
                    f"predicted:{event_id}"
                }
            ],

            [
                {
                    "text": "✅ التشكيلة الأساسية",
                    "callback_data":
                    f"official:{event_id}"
                }
            ],

        ]

    }


# =========================================================
# MATCH ANALYSIS
# =========================================================

def poisson(k, lam):

    return (
        math.exp(-lam)
        *
        lam ** k
        /
        math.factorial(k)
    )


def probability_over(
    total_lambda,
    line
):

    maximum_under = int(
        math.floor(line)
    )

    under = 0.0

    for goals in range(
        maximum_under + 1
    ):

        under += poisson(
            goals,
            total_lambda
        )

    return max(
        0.0,
        min(
            1.0,
            1.0 - under
        )
    )


def calculate_analysis(match):

    home = match["home"]
    away = match["away"]

    # ---------------------------------------------
    # Base strength
    # ---------------------------------------------

    # These are intentionally modest defaults.
    # Later we can replace them with automatic
    # last-5 / last-10 match statistics.

    strength = {

        "مانشستر سيتي": 1.35,
        "أرسنال": 1.30,
        "ليفربول": 1.30,
        "تشيلسي": 1.15,
        "مانشستر يونايتد": 1.10,

        "شباب بلوزداد": 1.20,
        "مولودية الجزائر": 1.20,
        "شبيبة القبائل": 1.10,
        "اتحاد العاصمة": 1.10,

        "أولمبي الشلف": 0.95,
        "شباب قسنطينة": 1.00,
        "شباب تموشنت": 0.85,

    }

    hs = strength.get(
        home,
        1.0
    )

    aws = strength.get(
        away,
        1.0
    )

    if "الجزائري" in match["league"]:

        base = 1.05
        home_advantage = 1.15

    else:

        base = 1.35
        home_advantage = 1.18

    home_lambda = (
        base
        * hs
        * home_advantage
        / max(
            0.75,
            aws
        )
    )

    away_lambda = (
        base
        * aws
        / max(
            0.80,
            hs
        )
    )

    home_lambda = max(
        0.20,
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

    home_win = 0
    draw = 0
    away_win = 0

    scores = []

    for h in range(9):

        for a in range(9):

            p = (
                poisson(
                    h,
                    home_lambda
                )
                *
                poisson(
                    a,
                    away_lambda
                )
            )

            scores.append(
                (h, a, p)
            )

            if h > a:

                home_win += p

            elif h == a:

                draw += p

            else:

                away_win += p

    scores.sort(
        key=lambda x: x[2],
        reverse=True
    )

    total = (
        home_lambda
        +
        away_lambda
    )

    return {

        "home_lambda":
            home_lambda,

        "away_lambda":
            away_lambda,

        "home_win":
            home_win,

        "draw":
            draw,

        "away_win":
            away_win,

        "total":
            total,

        "scores":
            scores[:5],
    }


def pct(x):

    return f"{x * 100:.1f}%"


def format_analysis(match):

    a = calculate_analysis(
        match
    )

    home = match["home"]
    away = match["away"]

    text = []

    text.append(
        f"⚽ <b>{home} × {away}</b>"
    )

    text.append(
        f"🏆 {match['league']}"
    )

    text.append(
        f"🕐 {match['time']}"
    )

    text.append("")

    text.append(
        "📊 <b>احتمالات المباراة</b>"
    )

    text.append(
        f"🏠 {home}: "
        f"<b>{pct(a['home_win'])}</b>"
    )

    text.append(
        f"🤝 التعادل: "
        f"<b>{pct(a['draw'])}</b>"
    )

    text.append(
        f"✈️ {away}: "
        f"<b>{pct(a['away_win'])}</b>"
    )

    text.append("")

    text.append(
        f"🎯 الأهداف المتوقعة: "
        f"<b>{a['total']:.2f}</b>"
    )

    text.append("")

    text.append(
        "📈 <b>Over / Under</b>"
    )

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5
    ]:

        over = probability_over(
            a["total"],
            line
        )

        under = 1 - over

        text.append(
            f"Over {line}: "
            f"<b>{pct(over)}</b> "
            f"| Under {line}: "
            f"<b>{pct(under)}</b>"
        )

    text.append("")

    text.append(
        "🎯 <b>النتائج الأكثر احتمالًا</b>"
    )

    for h, aw, p in a["scores"]:

        text.append(
            f"{h} - {aw}: "
            f"<b>{pct(p)}</b>"
        )

    text.append("")

    text.append(
        "⚠️ التحليل احتمالي وليس ضمانًا."
    )

    return "\n".join(text)


# =========================================================
# TELEGRAM
# =========================================================

def send_message(
    chat_id,
    text,
    reply_markup=None
):

    data = {

        "chat_id":
            chat_id,

        "text":
            text,

        "parse_mode":
            "HTML",

        "disable_web_page_preview":
            True,
    }

    if reply_markup:

        data[
            "reply_markup"
        ] = reply_markup

    try:

        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=data,
            timeout=20
        )

    except Exception as e:

        print(
            "Telegram send error:",
            e
        )


def answer_callback(
    callback_id
):

    try:

        requests.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={
                "callback_query_id":
                    callback_id
            },
            timeout=10
        )

    except Exception as e:

        print(
            "Callback error:",
            e
        )


# =========================================================
# MATCH MENU
# =========================================================

def send_matches(
    chat_id,
    league
):

    matches = get_league_matches(
        league
    )

    if not matches:

        send_message(
            chat_id,

            "⚠️ لا توجد مباريات متاحة "
            f"لهذه البطولة اليوم "
            f"({today_string()}).",

            main_keyboard()
        )

        return

    title = (
        "🇩🇿 مباريات الجزائر اليوم"
        if league == "algeria"
        else
        "🏴 مباريات إنجلترا اليوم"
    )

    send_message(
        chat_id,

        f"<b>{title}</b>\n"
        f"📅 {today_string()}\n\n"
        f"تم العثور على "
        f"<b>{len(matches)}</b> مباراة."
    )

    for match in matches:

        message = (
            f"⚽ <b>{match['home']} × "
            f"{match['away']}</b>\n\n"
            f"🕐 {match['time']}\n"
            f"🏆 {match['league']}\n\n"
            "اختر ما تريد:"
        )

        send_message(
            chat_id,
            message,
            match_keyboard(
                match["event_id"]
            )
        )


# =========================================================
# MAIN KEYBOARD
# =========================================================

def main_keyboard():

    return {

        "keyboard": [

            [
                {
                    "text":
                    "🇩🇿 مباريات الجزائر اليوم"
                }
            ],

            [
                {
                    "text":
                    "🏴 مباريات إنجلترا اليوم"
                }
            ],

            [
                {
                    "text":
                    "ℹ️ معلومات البوت"
                }
            ]

        ],

        "resize_keyboard":
            True
    }


# =========================================================
# FIND EVENT BY ID
# =========================================================

def find_event(event_id):

    events = get_today_events()

    for event in events:

        if event.get("id") == event_id:

            home = event.get(
                "homeTeam",
                {}
            )

            away = event.get(
                "awayTeam",
                {}
            )

            timestamp = event.get(
                "startTimestamp"
            )

            if timestamp:

                dt = datetime.fromtimestamp(
                    timestamp,
                    TZ
                )

                time = dt.strftime(
                    "%H:%M"
                )

                date = dt.strftime(
                    "%Y-%m-%d"
                )

            else:

                time = "غير محدد"
                date = today_string()

            tournament = event.get(
                "tournament",
                {}
            )

            unique = tournament.get(
                "uniqueTournament",
                {}
            )

            tournament_id = unique.get(
                "id"
            )

            if tournament_id == ALGERIA_TOURNAMENT_ID:

                league = "🇩🇿 الدوري الجزائري"

            elif tournament_id == ENGLAND_TOURNAMENT_ID:

                league = "🏴 الدوري الإنجليزي الممتاز"

            else:

                league = "الدوري"

            return {

                "event_id":
                    event_id,

                "league":
                    league,

                "home":
                    team_name(
                        home.get("name")
                    ),

                "away":
                    team_name(
                        away.get("name")
                    ),

                "time":
                    time,

                "date":
                    date,
            }

    return None


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    try:

        update = request.get_json(
            silent=True
        )

        if not update:

            return "ok"

        # =================================================
        # CALLBACK BUTTON
        # =================================================

        callback = update.get(
            "callback_query"
        )

        if callback:

            callback_id = callback.get(
                "id"
            )

            data = callback.get(
                "data",
                ""
            )

            message = callback.get(
                "message",
                {}
            )

            chat = message.get(
                "chat",
                {}
            )

            chat_id = chat.get(
                "id"
            )

            answer_callback(
                callback_id
            )

            if not chat_id:

                return "ok"

            try:

                mode, event_id = data.split(
                    ":",
                    1
                )

                event_id = int(
                    event_id
                )

            except:

                return "ok"

            match = find_event(
                event_id
            )

            if not match:

                send_message(
                    chat_id,
                    "⚠️ لم أجد بيانات المباراة."
                )

                return "ok"

            # ---------------------------------------------
            # ANALYSIS
            # ---------------------------------------------

            if mode == "analysis":

                send_message(
                    chat_id,
                    format_analysis(
                        match
                    ),
                    match_keyboard(
                        event_id
                    )
                )

                return "ok"

            # ---------------------------------------------
            # PREDICTED LINEUP
            # ---------------------------------------------

            if mode == "predicted":

                send_message(
                    chat_id,
                    format_lineup(
                        match,
                        "predicted"
                    ),
                    match_keyboard(
                        event_id
                    )
                )

                return "ok"

            # ---------------------------------------------
            # OFFICIAL LINEUP
            # ---------------------------------------------

            if mode == "official":

                send_message(
                    chat_id,
                    format_lineup(
                        match,
                        "official"
                    ),
                    match_keyboard(
                        event_id
                    )
                )

                return "ok"

            return "ok"

        # =================================================
        # NORMAL MESSAGE
        # =================================================

        message = update.get(
            "message"
        )

        if not message:

            return "ok"

        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        text = (
            message.get(
                "text",
                ""
            )
            .strip()
        )

        if not chat_id:

            return "ok"

        # =================================================
        # START
        # =================================================

        if text == "/start":

            send_message(
                chat_id,

                "⚽ <b>مرحبًا بك</b>\n\n"
                "اختر البطولة:",
                main_keyboard()
            )

            return "ok"

        # =================================================
        # ACCESS
        # =================================================

        if text == ACCESS_CODE:

            send_message(
                chat_id,

                "✅ تم قبول الكود.\n\n"
                "اختر البطولة:",
                main_keyboard()
            )

            return "ok"

        # =================================================
        # ALGERIA
        # =================================================

        if text == "🇩🇿 مباريات الجزائر اليوم":

            send_matches(
                chat_id,
                "algeria"
            )

            return "ok"

        # =================================================
        # ENGLAND
        # =================================================

        if text == "🏴 مباريات إنجلترا اليوم":

            send_matches(
                chat_id,
                "england"
            )

            return "ok"

        # =================================================
        # INFO
        # =================================================

        if text == "ℹ️ معلومات البوت":

            send_message(
                chat_id,

                "ℹ️ <b>معلومات البوت</b>\n\n"

                "🇩🇿 الدوري الجزائري\n"
                "🏴 الدوري الإنجليزي الممتاز\n\n"

                "📅 مباريات اليوم تلقائيًا\n"
                "📊 تحليل احتمالي\n"
                "🧩 التشكيلة المحتملة\n"
                "✅ التشكيلة الأساسية عند إعلانها\n\n"

                "⚠️ التشكيلات المحتملة ليست رسمية "
                "وقد تتغير قبل بداية المباراة.",

                main_keyboard()
            )

            return "ok"

        # =================================================
        # DEFAULT
        # =================================================

        send_message(
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
# HEALTH
# =========================================================

@app.route("/")
def home():

    return (
        "Football Analysis Bot OK | "
        f"{today_string()}"
    )


# =========================================================
# DEBUG
# =========================================================

@app.route("/debug")
def debug():

    events = get_today_events()

    output = []

    for event in events:

        tournament = event.get(
            "tournament",
            {}
        )

        unique = tournament.get(
            "uniqueTournament",
            {}
        )

        tid = unique.get(
            "id"
        )

        if tid not in [
            ALGERIA_TOURNAMENT_ID,
            ENGLAND_TOURNAMENT_ID
        ]:

            continue

        home = event.get(
            "homeTeam",
            {}
        )

        away = event.get(
            "awayTeam",
            {}
        )

        output.append({

            "event_id":
                event.get("id"),

            "tournament_id":
                tid,

            "home":
                home.get("name"),

            "away":
                away.get("name"),

            "startTimestamp":
                event.get(
                    "startTimestamp"
                )
        })

    return {
        "date":
            today_string(),

        "matches":
            output
    }


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
