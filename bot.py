import os
import re
import math
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from flask import Flask, request

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

PORT = int(os.getenv("PORT", "10000"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

ALGIERS_TZ = ZoneInfo("Africa/Algiers")

app = Flask(__name__)

# =========================================================
# SOURCES
# =========================================================

L1_URL = "https://www.footmercato.net/algerie/ligue-1/calendrier/"

L2_URL = (
    "https://competition.dz/chrono/"
    "ligue-2-les-calendriers-des-groupes-centre-est-et-centre-ouest-devoiles.html"
)

# =========================================================
# TEAM ALIASES
# =========================================================

ALIASES = {
    "es setif": "ES Sétif",
    "es sétif": "ES Sétif",

    "ben aknoun": "Ben Aknoun",

    "usm alger": "USM Alger",
    "usma": "USM Alger",

    "mc alger": "MC Alger",
    "mca": "MC Alger",

    "mc oran": "MC Oran",
    "mco": "MC Oran",

    "cr belouizdad": "CR Belouizdad",
    "crb": "CR Belouizdad",

    "js kabylie": "JS Kabylie",
    "jsk": "JS Kabylie",

    "cs constantine": "CS Constantine",
    "csc": "CS Constantine",

    "aso chlef": "ASO Chlef",
    "aso": "ASO Chlef",

    "us biskra": "US Biskra",
    "usb": "US Biskra",

    "js saoura": "JS Saoura",
    "jss": "JS Saoura",

    "khenchela": "Khenchela",
    "usmk": "Khenchela",

    "mb rouisset": "MB Rouisset",

    "olympique akbou": "Olympique Akbou",
    "akbou": "Olympique Akbou",

    "js el biar": "JS El Biar",
    "el biar": "JS El Biar",

    "cr temouchent": "CR Témouchent",
    "cr témouchent": "CR Témouchent",

    # L2
    "as khroub": "AS Khroub",
    "usm annaba": "USM Annaba",
    "nc magra": "NC Magra",
    "us chaouia": "US Chaouia",
    "nrb beni oulban": "NRB Beni Oulbane",
    "nrb beni oulbane": "NRB Beni Oulbane",
    "nrb teleghma": "NRB Télaghma",
    "nrb télaghma": "NRB Télaghma",
    "msp batna": "MSP Batna",
    "ca batna": "CA Batna",
    "js azazga": "JS Azazga",
    "jsm skikda": "JSM Skikda",
    "irb nezla": "IRB Nezla",
    "js jijel": "JS Jijel",
    "crb beni thour": "CRB Beni Thour",
    "mo bejaia": "MO Béjaïa",
    "mo béjaïa": "MO Béjaïa",
    "mo constantine": "MO Constantine",

    "mc saida": "MC Saïda",
    "mc saïda": "MC Saïda",
    "wa mostaganem": "WA Mostaganem",
    "usm el harrach": "USM El Harrach",
    "asm oran": "ASM Oran",
    "wa tlemcen": "WA Tlemcen",
    "jsm tiaret": "JSM Tiaret",
    "na hussein dey": "NA Hussein Dey",
    "js taghit": "JS Taghit",
    "esm kolea": "ESM Koléa",
    "esm koléa": "ESM Koléa",
    "rc kouba": "RC Kouba",
    "gc mascara": "GC Mascara",
    "rc arba": "RC Arbaâ",
    "rc arbaâ": "RC Arbaâ",
    "irbsm benali": "IRBSM Benali",
    "mc el bayadh": "MC El Bayadh",
    "es mostaganem": "ES Mostaganem",
    "usm blida": "USM Blida",
}

# =========================================================
# MODEL STRENGTH
# =========================================================

L1_STRENGTH = {
    "MC Alger": 82,
    "JS Saoura": 77,
    "CR Belouizdad": 76,
    "MC Oran": 73,
    "JS Kabylie": 72,
    "Olympique Akbou": 71,
    "Khenchela": 69,
    "Ben Aknoun": 68,
    "CS Constantine": 68,
    "USM Alger": 67,
    "ES Sétif": 67,
    "MB Rouisset": 64,
    "ASO Chlef": 62,
    "Paradou AC": 58,
    "CR Témouchent": 56,
    "JS El Biar": 55,
    "US Biskra": 66,
}

L2_STRENGTH = {
    "JS El Biar": 80,
    "USM El Harrach": 76,
    "CR Témouchent": 74,
    "RC Kouba": 74,
    "ASM Oran": 73,
    "NA Hussein Dey": 68,
    "WA Tlemcen": 66,
    "JSM Tiaret": 65,
    "ESM Koléa": 63,
    "WA Mostaganem": 62,
    "MC Saïda": 61,
    "GC Mascara": 59,
    "RC Arbaâ": 57,
    "USM Blida": 56,

    "AS Khroub": 63,
    "USM Annaba": 69,
    "NC Magra": 67,
    "US Chaouia": 73,
    "NRB Beni Oulbane": 64,
    "NRB Télaghma": 64,
    "MSP Batna": 65,
    "CA Batna": 73,
    "JS Azazga": 64,
    "JSM Skikda": 62,
    "IRB Nezla": 61,
    "JS Jijel": 70,
    "CRB Beni Thour": 60,
    "MO Béjaïa": 73,
    "MO Constantine": 62,
    "Paradou AC": 65,
}

# =========================================================
# L2 TEAMS
# =========================================================

L2_MATCHES = [
    ("AS Khroub", "Paradou AC"),
    ("USM Annaba", "NC Magra"),
    ("US Chaouia", "NRB Beni Oulbane"),
    ("NRB Télaghma", "MSP Batna"),
    ("CA Batna", "JS Azazga"),
    ("JSM Skikda", "IRB Nezla"),
    ("JS Jijel", "CRB Beni Thour"),
    ("MO Béjaïa", "MO Constantine"),

    ("MC Saïda", "WA Mostaganem"),
    ("USM El Harrach", "ASM Oran"),
    ("WA Tlemcen", "JSM Tiaret"),
    ("NA Hussein Dey", "JS Taghit"),
    ("ESM Koléa", "RC Kouba"),
    ("GC Mascara", "RC Arbaâ"),
    ("IRBSM Benali", "MC El Bayadh"),
    ("ES Mostaganem", "USM Blida"),
]

# =========================================================
# CACHE
# =========================================================

MATCH_CACHE = {}

# =========================================================
# TEXT HELPERS
# =========================================================

def normalize_text(value):
    value = value or ""

    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.lower()

    value = value.replace("’", "'")
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def canonical_team(name):
    key = normalize_text(name)

    return ALIASES.get(key, name.strip())


def clean_line(line):
    line = line.replace("\xa0", " ")
    line = re.sub(r"\s+", " ", line)

    return line.strip()


# =========================================================
# TELEGRAM
# =========================================================

def telegram_request(method, payload=None):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=payload or {},
            timeout=20
        )

        print(
            "Telegram:",
            method,
            response.status_code
        )

        return response.json()

    except Exception as e:

        print(
            "Telegram error:",
            repr(e)
        )

        return {}


def send_message(chat_id, text, keyboard=None):

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    return telegram_request(
        "sendMessage",
        payload
    )


def edit_message(
    chat_id,
    message_id,
    text,
    keyboard=None
):

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    return telegram_request(
        "editMessageText",
        payload
    )


def answer_callback(callback_id):

    return telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# KEYBOARD
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            [
                {
                    "text": "🇩🇿 Ligue 1"
                }
            ],
            [
                {
                    "text": "🇩🇿 Ligue 2"
                }
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


# =========================================================
# WEB
# =========================================================

def fetch_page(url):

    try:

        print(
            "Fetching:",
            url
        )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(
            "HTTP:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        return response.text

    except Exception as e:

        print(
            "Fetch error:",
            repr(e)
        )

        return None


def extract_lines(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        tag.decompose()

    text = soup.get_text("\n")

    lines = []

    for line in text.splitlines():

        line = clean_line(line)

        if line:
            lines.append(line)

    return lines


# =========================================================
# L1
# =========================================================

MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
    "décembre": 12,
}


def parse_date_line(line):

    normalized = normalize_text(line)

    pattern = (
        r"(?:lundi|mardi|mercredi|jeudi|"
        r"vendredi|samedi|dimanche)"
        r"\s+"
        r"(\d{1,2})"
        r"\s+"
        r"([a-zéûôîà]+)"
        r"\s+"
        r"(\d{4})"
    )

    match = re.search(
        pattern,
        normalized
    )

    if not match:
        return None

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))

    month = MONTHS.get(
        month_name
    )

    if not month:
        return None

    try:

        return datetime(
            year,
            month,
            day,
            tzinfo=ALGIERS_TZ
        ).date()

    except Exception:

        return None


def parse_l1_today():

    html = fetch_page(
        L1_URL
    )

    if not html:
        return []

    lines = extract_lines(
        html
    )

    today = datetime.now(
        ALGIERS_TZ
    ).date()

    known_teams = list(
        L1_STRENGTH.keys()
    )

    matches = []

    current_date = None

    for line in lines:

        parsed_date = parse_date_line(
            line
        )

        if parsed_date:

            current_date = parsed_date

            continue

        if current_date != today:
            continue

        time_match = re.search(
            r"\b(\d{1,2}:\d{2})\b",
            line
        )

        if not time_match:
            continue

        match_time = time_match.group(1)

        teams_text = re.sub(
            r"\b\d{1,2}:\d{2}\b",
            "",
            line
        ).strip()

        found = []

        normalized_line = normalize_text(
            teams_text
        )

        for team in known_teams:

            key = normalize_text(
                team
            )

            if key in normalized_line:

                found.append(
                    (
                        len(key),
                        team
                    )
                )

        if len(found) < 2:
            continue

        found.sort(
            reverse=True
        )

        home = found[0][1]
        away = found[1][1]

        if home == away:
            continue

        matches.append(
            {
                "league": "Ligue 1",
                "home": home,
                "away": away,
                "time": match_time,
            }
        )

    unique = []

    seen = set()

    for match in matches:

        key = (
            match["home"],
            match["away"],
            match["time"],
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(match)

    print(
        "L1 matches:",
        unique
    )

    return unique


# =========================================================
# L2
# =========================================================

def get_l2_matches():

    html = fetch_page(
        L2_URL
    )

    if not html:
        return []

    lines = extract_lines(
        html
    )

    today = datetime.now(
        ALGIERS_TZ
    ).date()

    # Ligue 2 2026/27 opening date.
    # This is only used to identify the round.
    season_start = datetime(
        2026,
        9,
        4,
        tzinfo=ALGIERS_TZ
    ).date()

    if today < season_start:
        return []

    days = (
        today -
        season_start
    ).days

    round_number = (
        days // 7
    ) + 1

    if round_number < 1:
        return []

    if round_number > 30:
        return []

    print(
        "L2 round:",
        round_number
    )

    # Try to find the round in the article.
    round_regex = re.compile(
        rf"^{round_number}"
        rf"(?:re|e|eme|ème)"
        rf"\s+journ[ée]e$",
        re.IGNORECASE
    )

    start_index = None

    for i, line in enumerate(lines):

        normalized = normalize_text(
            line
        )

        if round_regex.search(
            normalized
        ):

            start_index = i

            break

    # If the article structure cannot be parsed,
    # use the published team pairs for round 1.
    if start_index is None:

        if round_number == 1:

            return [
                {
                    "league": "Ligue 2",
                    "home": home,
                    "away": away,
                    "time": "حسب البرنامج",
                }

                for home, away
                in L2_MATCHES
            ]

        return []

    section = lines[
        start_index:
    ]

    # Stop at the next round.
    next_round_pattern = re.compile(
        r"^\d+"
        r"(?:re|e|eme|ème)"
        r"\s+journ[ée]e$",
        re.IGNORECASE
    )

    for i, line in enumerate(
        section[1:],
        start=1
    ):

        if next_round_pattern.search(
            normalize_text(line)
        ):

            section = section[:i]

            break

    section_text = normalize_text(
        " ".join(section)
    )

    matches = []

    for home, away in L2_MATCHES:

        home_found = (
            normalize_text(home)
            in section_text
        )

        away_found = (
            normalize_text(away)
            in section_text
        )

        if home_found and away_found:

            matches.append(
                {
                    "league": "Ligue 2",
                    "home": home,
                    "away": away,
                    "time": "حسب البرنامج",
                }
            )

    print(
        "L2 matches:",
        matches
    )

    return matches


# =========================================================
# MATCHES
# =========================================================

def get_matches(league):

    if league == "Ligue 1":
        return parse_l1_today()

    if league == "Ligue 2":
        return get_l2_matches()

    return []


# =========================================================
# PREDICTION
# =========================================================

def get_strength(team, league):

    if league == "Ligue 1":
        table = L1_STRENGTH
    else:
        table = L2_STRENGTH

    return table.get(
        team,
        60
    )


def poisson_probability(
    lam,
    goals
):

    return (
        math.exp(-lam)
        *
        (lam ** goals)
        /
        math.factorial(goals)
    )


def calculate_prediction(
    home,
    away,
    league
):

    home_strength = get_strength(
        home,
        league
    )

    away_strength = get_strength(
        away,
        league
    )

    difference = (
        home_strength -
        away_strength
    )

    # Model baseline
    home_xg = (
        1.15 +
        difference / 45
    )

    away_xg = (
        0.85 -
        difference / 90
    )

    home_xg = max(
        0.20,
        min(
            home_xg,
            2.70
        )
    )

    away_xg = max(
        0.15,
        min(
            away_xg,
            2.30
        )
    )

    home_win = 0
    draw = 0
    away_win = 0

    best_score = (
        0,
        0
    )

    best_probability = 0

    for hg in range(7):

        for ag in range(7):

            probability = (
                poisson_probability(
                    home_xg,
                    hg
                )
                *
                poisson_probability(
                    away_xg,
                    ag
                )
            )

            if hg > ag:
                home_win += probability

            elif hg == ag:
                draw += probability

            else:
                away_win += probability

            if probability > best_probability:

                best_probability = probability

                best_score = (
                    hg,
                    ag
                )

    total = (
        home_win +
        draw +
        away_win
    )

    home_pct = round(
        home_win /
        total *
        100
    )

    draw_pct = round(
        draw /
        total *
        100
    )

    away_pct = (
        100 -
        home_pct -
        draw_pct
    )

    if (
        home_pct >= draw_pct
        and
        home_pct >= away_pct
    ):

        winner = home
        winner_icon = "🏠"

    elif (
        away_pct >= home_pct
        and
        away_pct >= draw_pct
    ):

        winner = away
        winner_icon = "✈️"

    else:

        winner = "تعادل"
        winner_icon = "🤝"

    total_xg = (
        home_xg +
        away_xg
    )

    btts = (
        1 -
        math.exp(-home_xg)
    ) * (
        1 -
        math.exp(-away_xg)
    )

    under_25 = 0

    for hg in range(3):

        for ag in range(3 - hg):

            under_25 += (
                poisson_probability(
                    home_xg,
                    hg
                )
                *
                poisson_probability(
                    away_xg,
                    ag
                )
            )

    over_25 = 1 - under_25

    cards = 3.4

    if abs(difference) > 15:
        cards += 0.3

    if total_xg < 1.8:
        cards += 0.2

    return {
        "winner": winner,
        "winner_icon": winner_icon,

        "home_pct": home_pct,
        "draw_pct": draw_pct,
        "away_pct": away_pct,

        "home_xg": round(
            home_xg,
            2
        ),

        "away_xg": round(
            away_xg,
            2
        ),

        "total_xg": round(
            total_xg,
            2
        ),

        "score": (
            f"{best_score[0]}"
            f" - "
            f"{best_score[1]}"
        ),

        "btts": round(
            btts * 100
        ),

        "over25": round(
            over_25 * 100
        ),

        "cards": round(
            cards,
            1
        ),

        "home_strength": home_strength,
        "away_strength": away_strength,
    }


# =========================================================
# ANALYSIS
# =========================================================

def build_analysis(match):

    league = match["league"]

    home = match["home"]

    away = match["away"]

    time = match.get(
        "time",
        "غير محدد"
    )

    prediction = calculate_prediction(
        home,
        away,
        league
    )

    return (
        "🔎 <b>تحليل المباراة</b>\n\n"

        f"🏆 البطولة: <b>{league}</b>\n"
        f"⚽ <b>{home} × {away}</b>\n"
        f"🕒 الوقت: <b>{time}</b>\n\n"

        "━━━━━━━━━━━━━━\n"

        "🏆 <b>التوقع الرئيسي</b>\n"
        f"{prediction['winner_icon']} "
        f"<b>{prediction['winner']}</b>\n\n"

        "📊 <b>احتمالات 1X2</b>\n"
        f"🏠 {home}: "
        f"<b>{prediction['home_pct']}%</b>\n"
        f"🤝 التعادل: "
        f"<b>{prediction['draw_pct']}%</b>\n"
        f"✈️ {away}: "
        f"<b>{prediction['away_pct']}%</b>\n\n"

        "⚽ <b>الأهداف المتوقعة</b>\n"
        f"🏠 {home}: "
        f"{prediction['home_xg']}\n"
        f"✈️ {away}: "
        f"{prediction['away_xg']}\n"
        f"📈 المجموع: "
        f"{prediction['total_xg']}\n\n"

        "🎯 <b>النتيجة الأقرب:</b> "
        f"<b>{prediction['score']}</b>\n\n"

        "🥅 <b>الفريقان يسجلان:</b> "
        f"{prediction['btts']}%\n"

        "⚽ <b>أكثر من 2.5 هدف:</b> "
        f"{prediction['over25']}%\n"

        "🟨 <b>البطاقات المتوقعة:</b> "
        f"حوالي {prediction['cards']}\n\n"

        "📈 <b>قوة الفريقين في النموذج</b>\n"
        f"🏠 {home}: "
        f"{prediction['home_strength']}/100\n"
        f"✈️ {away}: "
        f"{prediction['away_strength']}/100\n\n"

        "━━━━━━━━━━━━━━\n"

        "ℹ️ <i>التوقع حسابي وليس ضمانًا "
        "للنتيجة. البطاقات تقديرية وليست "
        "إحصائية مباشرة.</i>"
    )


# =========================================================
# INLINE BUTTONS
# =========================================================

def matches_keyboard(matches):

    rows = []

    for index, match in enumerate(
        matches
    ):

        rows.append(
            [
                {
                    "text": (
                        f"🔎 تحليل "
                        f"{match['home']} "
                        f"× "
                        f"{match['away']}"
                    ),
                    "callback_data": (
                        f"ANALYZE|{index}"
                    ),
                }
            ]
        )

    return {
        "inline_keyboard": rows
    }


# =========================================================
# CACHE
# =========================================================

def save_matches(
    chat_id,
    matches
):

    MATCH_CACHE[
        str(chat_id)
    ] = matches


def cached_match(
    chat_id,
    index
):

    matches = MATCH_CACHE.get(
        str(chat_id),
        []
    )

    try:

        return matches[
            int(index)
        ]

    except Exception:

        return None


# =========================================================
# SEND LEAGUE
# =========================================================

def show_league(
    chat_id,
    league
):

    send_message(
        chat_id,
        "⏳ جاري البحث عن مباريات "
        f"<b>{league}</b>...",
    )

    matches = get_matches(
        league
    )

    save_matches(
        chat_id,
        matches
    )

    if not matches:

        send_message(
            chat_id,
            f"⚠️ لا توجد مباريات "
            f"<b>{league}</b> متاحة حاليًا.\n\n"
            "قد يكون السبب عدم وجود مباريات "
            "اليوم أو تغير تنسيق المصدر.",
            main_keyboard()
        )

        return

    text = (
        f"🇩🇿 <b>{league}</b>\n\n"
        "⚽ <b>المباريات المتاحة:</b>\n\n"
    )

    for match in matches:

        text += (
            f"⚽ {match['home']} "
            f"× "
            f"{match['away']}\n"
            f"🕒 {match['time']}\n\n"
        )

    text += (
        "👇 <b>اختر مباراة للحصول على التحليل:</b>"
    )

    send_message(
        chat_id,
        text,
        matches_keyboard(
            matches
        )
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    update = request.get_json(
        silent=True
    ) or {}

    print(
        "Telegram update received"
    )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    message = update.get(
        "message"
    )

    if message:

        chat_id = message[
            "chat"
        ][
            "id"
        ]

        text = message.get(
            "text",
            ""
        ).strip()

        print(
            "Message:",
            text
        )

        if text == "/start":

            send_message(
                chat_id,

                "⚽ <b>مرحبًا بك</b>\n\n"
                "🇩🇿 بوت تحليل كرة القدم الجزائرية\n\n"
                "اختر البطولة:",
                
                main_keyboard()
            )

            return "OK"

        if text in (
            "🇩🇿 Ligue 1",
            "Ligue 1"
        ):

            show_league(
                chat_id,
                "Ligue 1"
            )

            return "OK"

        if text in (
            "🇩🇿 Ligue 2",
            "Ligue 2"
        ):

            show_league(
                chat_id,
                "Ligue 2"
            )

            return "OK"

        return "OK"

    # -----------------------------------------------------
    # CALLBACK
    # -----------------------------------------------------

    callback = update.get(
        "callback_query"
    )

    if callback:

        callback_id = callback[
            "id"
        ]

        answer_callback(
            callback_id
        )

        data = callback.get(
            "data",
            ""
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

        message_id = message.get(
            "message_id"
        )

        if data.startswith(
            "ANALYZE|"
        ):

            index = data.split(
                "|",
                1
            )[1]

            match = cached_match(
                chat_id,
                index
            )

            if not match:

                edit_message(
                    chat_id,
                    message_id,

                    "⚠️ انتهت صلاحية القائمة.\n"
                    "اضغط على الدوري من جديد."
                )

                return "OK"

            analysis = build_analysis(
                match
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": (
                                "⬅️ رجوع للمباريات"
                            ),
                            "callback_data": "BACK",
                        }
                    ]
                ]
            }

            edit_message(
                chat_id,
                message_id,
                analysis,
                keyboard
            )

            return "OK"

        if data == "BACK":

            matches = MATCH_CACHE.get(
                str(chat_id),
                []
            )

            if not matches:

                edit_message(
                    chat_id,
                    message_id,
                    "⚠️ لا توجد قائمة محفوظة."
                )

                return "OK"

            league = matches[
                0
            ][
                "league"
            ]

            text = (
                f"🇩🇿 <b>{league}</b>\n\n"
                "⚽ <b>المباريات:</b>\n\n"
            )

            for match in matches:

                text += (
                    f"⚽ {match['home']} "
                    f"× "
                    f"{match['away']}\n"
                    f"🕒 {match['time']}\n\n"
                )

            text += (
                "👇 <b>اختر مباراة:</b>"
            )

            edit_message(
                chat_id,
                message_id,
                text,
                matches_keyboard(
                    matches
                )
            )

            return "OK"

    return "OK"


# =========================================================
# SECOND ROUTE
# Compatibility with old webhook
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def old_webhook():

    return telegram_webhook()


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return (
        "⚽ Algeria Football Bot "
        "is running."
    )


@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return "OK"


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print(
        "================================="
    )

    print(
        "⚽ ALGERIA FOOTBALL BOT"
    )

    print(
        "🇩🇿 Ligue 1 + Ligue 2"
    )

    print(
        "🚫 No football API"
    )

    print(
        "🚫 No OpenAI"
    )

    print(
        "📡 Webhook: /telegram/webhook"
    )

    print(
        f"🚀 Port: {PORT}"
    )

    print(
        "================================="
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
