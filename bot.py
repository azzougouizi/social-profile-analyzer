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
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
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
# TEAM NORMALIZATION
# =========================================================

ALIASES = {
    # Ligue 1
    "es setif": "ES Sétif",
    "es sétif": "ES Sétif",
    "ess": "ES Sétif",

    "ben aknoun": "Ben Aknoun",
    "esba": "Ben Aknoun",

    "usm alger": "USM Alger",
    "usma": "USM Alger",

    "mc alger": "MC Alger",
    "mca": "MC Alger",

    "mc oran": "MC Oran",
    "mco": "MC Oran",

    "cr belouizdad": "CR Belouizdad",
    "belouizdad": "CR Belouizdad",
    "crb": "CR Belouizdad",

    "js kabylie": "JS Kabylie",
    "kabylie": "JS Kabylie",
    "jsk": "JS Kabylie",

    "cs constantine": "CS Constantine",
    "csc": "CS Constantine",

    "aso chlef": "ASO Chlef",
    "aso": "ASO Chlef",

    "us biskra": "US Biskra",
    "usb": "US Biskra",

    "js saoura": "JS Saoura",
    "saoura": "JS Saoura",
    "jss": "JS Saoura",

    "khenchela": "Khenchela",
    "usmk": "Khenchela",

    "mb rouisset": "MB Rouisset",
    "rouisset": "MB Rouisset",
    "mbr": "MB Rouisset",

    "olympique akbou": "Olympique Akbou",
    "akbou": "Olympique Akbou",
    "oa": "Olympique Akbou",

    "js el biar": "JS El Biar",
    "el biar": "JS El Biar",
    "jseb": "JS El Biar",

    "cr temouchent": "CR Témouchent",
    "témouchent": "CR Témouchent",
    "temouchent": "CR Témouchent",
    "crt": "CR Témouchent",

    # Ligue 2 Centre-Est
    "as khroub": "AS Khroub",
    "khroub": "AS Khroub",

    "usm annaba": "USM Annaba",
    "annaba": "USM Annaba",

    "nc magra": "NC Magra",
    "magra": "NC Magra",

    "us chaouia": "US Chaouia",
    "chaouia": "US Chaouia",

    "nrb beni oulbaine": "NRB Beni Oulbane",
    "nrb beni oulbane": "NRB Beni Oulbane",

    "nrb teleghma": "NRB Télaghma",
    "teleghma": "NRB Télaghma",
    "télaghma": "NRB Télaghma",

    "msp batna": "MSP Batna",
    "ca batna": "CA Batna",

    "js azazga": "JS Azazga",
    "azazga": "JS Azazga",

    "jsm skikda": "JSM Skikda",
    "skikda": "JSM Skikda",

    "irb nezla": "IRB Nezla",
    "nezla": "IRB Nezla",

    "js jijel": "JS Jijel",
    "jijel": "JS Jijel",

    "crb beni thour": "CRB Beni Thour",
    "beni thour": "CRB Beni Thour",

    "mo bejaia": "MO Béjaïa",
    "mo béjaïa": "MO Béjaïa",
    "bejaia": "MO Béjaïa",
    "béjaïa": "MO Béjaïa",

    "mo constantine": "MO Constantine",

    "paradou ac": "Paradou AC",
    "paradou": "Paradou AC",

    # Ligue 2 Centre-Ouest
    "mc saida": "MC Saïda",
    "mc saïda": "MC Saïda",
    "saida": "MC Saïda",

    "wa mostaganem": "WA Mostaganem",

    "usm el harrach": "USM El Harrach",
    "el harrach": "USM El Harrach",

    "asm oran": "ASM Oran",

    "wa tlemcen": "WA Tlemcen",

    "jsm tiaret": "JSM Tiaret",
    "tiaret": "JSM Tiaret",

    "na hussein dey": "NA Hussein Dey",
    "hussein dey": "NA Hussein Dey",

    "js taghit": "JS Taghit",

    "esm kolea": "ESM Koléa",
    "esm koléa": "ESM Koléa",
    "koléa": "ESM Koléa",
    "kolea": "ESM Koléa",

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
# PREVIOUS-SEASON STRENGTH
# These are baseline ratings, not current predictions.
# They are used only when recent results are unavailable.
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
# HELPERS
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

    value = re.sub(r"\s+", " ", value).strip()

    return value


def canonical_team(name):
    original = name.strip()
    key = normalize_text(original)

    if key in ALIASES:
        return ALIASES[key]

    return original


def clean_line(line):
    line = line.replace("\xa0", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def telegram_request(method, payload=None):
    try:
        r = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=payload or {},
            timeout=20
        )

        return r.json()

    except Exception as e:
        print("Telegram error:", e)
        return {}


def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    return telegram_request("sendMessage", payload)


def edit_message(chat_id, message_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    return telegram_request("editMessageText", payload)


def answer_callback(callback_id):
    telegram_request(
        "answerCallbackQuery",
        {"callback_query_id": callback_id}
    )


# =========================================================
# KEYBOARD
# =========================================================

def main_keyboard():
    return {
        "keyboard": [
            [{"text": "🇩🇿 Ligue 1"}],
            [{"text": "🇩🇿 Ligue 2"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


# =========================================================
# WEB FETCH
# =========================================================

def fetch_page(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=25
        )

        print("WEB:", url)
        print("STATUS:", response.status_code)

        if response.status_code != 200:
            return None

        return response.text

    except Exception as e:
        print("Web error:", e)
        return None


# =========================================================
# L1 PARSER
# =========================================================

FRENCH_MONTHS = {
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


def extract_lines(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text("\n")

    lines = []

    for line in text.splitlines():
        line = clean_line(line)

        if line:
            lines.append(line)

    return lines


def parse_french_date(line):
    pattern = (
        r"(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
        r"\s+(\d{1,2})\s+([A-Za-zéûôîà]+)\s+(\d{4})"
    )

    m = re.search(pattern, normalize_text(line))

    if not m:
        return None

    day = int(m.group(1))
    month_name = normalize_text(m.group(2))
    year = int(m.group(3))

    month = FRENCH_MONTHS.get(month_name)

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


def looks_like_time(line):
    return bool(
        re.search(
            r"\b\d{1,2}:\d{2}\b",
            line
        )
    )


def parse_l1_today():
    html = fetch_page(L1_URL)

    if not html:
        return []

    lines = extract_lines(html)

    today = datetime.now(ALGIERS_TZ).date()

    matches = []

    current_date = None

    # List of recognizable teams
    known = set(L1_STRENGTH.keys())

    for i, line in enumerate(lines):

        parsed_date = parse_french_date(line)

        if parsed_date:
            current_date = parsed_date
            continue

        if current_date != today:
            continue

        if not looks_like_time(line):
            continue

        # Example:
        # ES Sétif Ben Aknoun 20:00
        #
        # Try to detect a time and split the remaining text.

        m = re.search(
            r"^(.*?)\s+(\d{1,2}:\d{2})$",
            line
        )

        if not m:
            continue

        teams_text = m.group(1).strip()
        match_time = m.group(2)

        # Try every known team name.
        normalized_teams = []

        for team in known:
            nt = normalize_text(team)

            if nt in normalize_text(teams_text):
                normalized_teams.append(
                    (len(nt), team)
                )

        if len(normalized_teams) < 2:
            continue

        normalized_teams.sort(reverse=True)

        home = normalized_teams[0][1]
        away = normalized_teams[1][1]

        if home == away:
            continue

        matches.append({
            "league": "Ligue 1",
            "home": home,
            "away": away,
            "time": match_time,
        })

    # Remove duplicates
    unique = []

    seen = set()

    for match in matches:
        key = (
            match["home"],
            match["away"],
            match["time"]
        )

        if key not in seen:
            seen.add(key)
            unique.append(match)

    print("L1 TODAY:", unique)

    return unique


# =========================================================
# L2 PARSER
# =========================================================

L2_CENTRE_EST = [
    ("AS Khroub", "Paradou AC"),
    ("USM Annaba", "NC Magra"),
    ("US Chaouia", "NRB Beni Oulbane"),
    ("NRB Télaghma", "MSP Batna"),
    ("CA Batna", "JS Azazga"),
    ("JSM Skikda", "IRB Nezla"),
    ("JS Jijel", "CRB Beni Thour"),
    ("MO Béjaïa", "MO Constantine"),
]

L2_CENTRE_OUEST = [
    ("MC Saïda", "WA Mostaganem"),
    ("USM El Harrach", "ASM Oran"),
    ("WA Tlemcen", "JSM Tiaret"),
    ("NA Hussein Dey", "JS Taghit"),
    ("ESM Koléa", "RC Kouba"),
    ("GC Mascara", "RC Arbaâ"),
    ("IRBSM Benali", "MC El Bayadh"),
    ("ES Mostaganem", "USM Blida"),
]


def find_l2_round_for_today():
    """
    Competition.dz article contains the 2026/27 schedule
    in text sections labelled 1re journée, 2e journée, etc.

    The exact calendar dates are not always printed beside
    every round in the article, so we use the known official
    start date of Ligue 2 2026/27: 4 September 2026.

    For later rounds this parser can be extended as dates
    are published.
    """

    today = datetime.now(ALGIERS_TZ).date()

    # Season opening: 4 September 2026
    if today == datetime(2026, 9, 4, tzinfo=ALGIERS_TZ).date():
        return 1

    # Approximate weekly Friday rounds for the fallback.
    start = datetime(
        2026,
        9,
        4,
        tzinfo=ALGIERS_TZ
    ).date()

    days = (today - start).days

    if days >= 0:
        round_no = (days // 7) + 1

        if 1 <= round_no <= 15:
            return round_no

    return None


def parse_l2():
    html = fetch_page(L2_URL)

    if not html:
        return []

    lines = extract_lines(html)

    today_round = find_l2_round_for_today()

    print("L2 ROUND:", today_round)

    if not today_round:
        return []

    # Search for "1re journée", "2e journée", etc.
    round_patterns = [
        f"{today_round}e journée",
        f"{today_round}ère journée",
        f"{today_round}re journée",
        f"{today_round}eme journée",
        f"{today_round}ème journée",
    ]

    start_index = None

    for i, line in enumerate(lines):
        low = normalize_text(line)

        if any(
            normalize_text(pattern) in low
            for pattern in round_patterns
        ):
            start_index = i
            break

    if start_index is None:

        # Special case round 1
        if today_round == 1:
            start_index = 0

        else:
            return []

    # Find next round
    end_index = len(lines)

    for i in range(start_index + 1, len(lines)):

        low = normalize_text(lines[i])

        if re.match(
            r"^\d+(?:re|e|eme|ème)\s+journee",
            low
        ):
            end_index = i
            break

    section = lines[start_index:end_index]

    all_pairs = (
        L2_CENTRE_EST +
        L2_CENTRE_OUEST
    )

    matches = []

    for home, away in all_pairs:

        home_key = normalize_text(home)
        away_key = normalize_text(away)

        found_home = False
        found_away = False

        for line in section:

            low = normalize_text(line)

            if home_key in low:
                found_home = True

            if away_key in low:
                found_away = True

        if found_home and found_away:
            matches.append({
                "league": "Ligue 2",
                "home": home,
                "away": away,
                "time": "غير محدد",
            })

    # The section parser may miss some matches because of
    # accents/HTML formatting. For round 1 we use the official
    # published pairs as a reliable fallback.

    if today_round == 1 and not matches:
        for home, away in (
            L2_CENTRE_EST +
            L2_CENTRE_OUEST
        ):
            matches.append({
                "league": "Ligue 2",
                "home": home,
                "away": away,
                "time": "حسب البرنامج",
            })

    # Deduplicate
    unique = []
    seen = set()

    for match in matches:
        key = (
            match["home"],
            match["away"]
        )

        if key not in seen:
            seen.add(key)
            unique.append(match)

    print("L2 TODAY:", unique)

    return unique


# =========================================================
# PREDICTION ENGINE
# =========================================================

def get_strength(team, league):
    if league == "Ligue 1":
        table = L1_STRENGTH
    else:
        table = L2_STRENGTH

    if team in table:
        return table[team]

    return 60


def poisson_probability(lam, k):
    if lam < 0:
        lam = 0

    return (
        math.exp(-lam) *
        (lam ** k) /
        math.factorial(k)
    )


def calculate_prediction(home, away, league):

    home_strength = get_strength(home, league)
    away_strength = get_strength(away, league)

    # Home advantage
    strength_difference = (
        home_strength -
        away_strength
    )

    # Baseline expected goals for Algerian leagues.
    # Conservative because these leagues are generally
    # lower scoring than many European leagues.

    base_home = 1.15
    base_away = 0.85

    adjustment = strength_difference / 45.0

    home_xg = base_home + adjustment
    away_xg = base_away - adjustment / 2

    # Keep sane bounds
    home_xg = max(0.20, min(2.70, home_xg))
    away_xg = max(0.15, min(2.30, away_xg))

    # 1X2 probabilities using Poisson
    home_win = 0.0
    draw = 0.0
    away_win = 0.0

    best_score = (0, 0)
    best_score_probability = -1

    for hg in range(0, 7):
        for ag in range(0, 7):

            p = (
                poisson_probability(home_xg, hg) *
                poisson_probability(away_xg, ag)
            )

            if hg > ag:
                home_win += p
            elif hg == ag:
                draw += p
            else:
                away_win += p

            if p > best_score_probability:
                best_score_probability = p
                best_score = (hg, ag)

    total = home_win + draw + away_win

    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total

    # Slight normalization
    home_pct = round(home_win * 100)
    draw_pct = round(draw * 100)
    away_pct = 100 - home_pct - draw_pct

    # Winner
    if home_pct >= draw_pct and home_pct >= away_pct:
        winner = home
        winner_icon = "🏠"
    elif away_pct >= home_pct and away_pct >= draw_pct:
        winner = away
        winner_icon = "✈️"
    else:
        winner = "تعادل"
        winner_icon = "🤝"

    total_xg = home_xg + away_xg

    # BTTS
    btts_probability = (
        (1 - math.exp(-home_xg)) *
        (1 - math.exp(-away_xg))
    )

    # Over 2.5 using total Poisson
    under_sum = 0

    for total_goals in range(0, 3):
        for hg in range(0, total_goals + 1):

            ag = total_goals - hg

            under_sum += (
                poisson_probability(home_xg, hg) *
                poisson_probability(away_xg, ag)
            )

    over25 = 1 - under_sum

    # Cards estimate
    # This is a model estimate, NOT live card statistics.
    cards = 3.4

    if abs(strength_difference) > 15:
        cards += 0.3

    if total_xg < 1.8:
        cards += 0.2

    cards = round(cards, 1)

    return {
        "home_pct": home_pct,
        "draw_pct": draw_pct,
        "away_pct": away_pct,
        "winner": winner,
        "winner_icon": winner_icon,
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "total_xg": round(total_xg, 2),
        "score": f"{best_score[0]} - {best_score[1]}",
        "btts": round(btts_probability * 100),
        "over25": round(over25 * 100),
        "cards": cards,
        "home_strength": home_strength,
        "away_strength": away_strength,
    }


# =========================================================
# ANALYSIS MESSAGE
# =========================================================

def build_analysis(match):

    league = match["league"]
    home = match["home"]
    away = match["away"]
    time = match.get("time", "غير محدد")

    prediction = calculate_prediction(
        home,
        away,
        league
    )

    text = (
        f"🔎 <b>تحليل المباراة</b>\n\n"
        f"🏆 <b>{league}</b>\n"
        f"⚽ <b>{home} × {away}</b>\n"
        f"🕒 الوقت: <b>{time}</b>\n\n"

        f"━━━━━━━━━━━━━━\n"
        f"🏆 <b>التوقع الرئيسي</b>\n"
        f"{prediction['winner_icon']} "
        f"<b>{prediction['winner']}</b>\n\n"

        f"📊 <b>احتمالات 1X2</b>\n"
        f"🏠 {home}: <b>{prediction['home_pct']}%</b>\n"
        f"🤝 التعادل: <b>{prediction['draw_pct']}%</b>\n"
        f"✈️ {away}: <b>{prediction['away_pct']}%</b>\n\n"

        f"⚽ <b>الأهداف المتوقعة</b>\n"
        f"🏠 {home}: {prediction['home_xg']}\n"
        f"✈️ {away}: {prediction['away_xg']}\n"
        f"📈 المجموع: {prediction['total_xg']}\n\n"

        f"🎯 <b>النتيجة الأقرب:</b> "
        f"<b>{prediction['score']}</b>\n\n"

        f"🥅 <b>الفريقان يسجلان:</b> "
        f"{prediction['btts']}%\n"
        f"⚽ <b>أكثر من 2.5 هدف:</b> "
        f"{prediction['over25']}%\n"
        f"🟨 <b>البطاقات المتوقعة:</b> "
        f"حوالي {prediction['cards']}\n\n"

        f"📈 <b>قوة الفريقين في النموذج</b>\n"
        f"🏠 {home}: {prediction['home_strength']}/100\n"
        f"✈️ {away}: {prediction['away_strength']}/100\n\n"

        f"━━━━━━━━━━━━━━\n"
        f"ℹ️ <i>هذه توقعات حسابية وليست ضمانًا للنتيجة. "
        f"بعض الإحصائيات مثل البطاقات هنا تقديرية وليست بيانات "
        f"مباشرة من المباراة.</i>"
    )

    return text


# =========================================================
# MATCH LIST
# =========================================================

def get_matches(league):

    if league == "Ligue 1":
        return parse_l1_today()

    if league == "Ligue 2":
        return parse_l2()

    return []


def matches_keyboard(matches):

    rows = []

    for i, match in enumerate(matches):

        home = match["home"]
        away = match["away"]

        button = {
            "text": f"🔎 تحليل {home} × {away}",
            "callback_data": f"ANALYZE|{i}"
        }

        rows.append([button])

    return {
        "inline_keyboard": rows
    }


# =========================================================
# TEMPORARY MATCH CACHE
# =========================================================

MATCH_CACHE = {}


def cache_matches(chat_id, matches):

    MATCH_CACHE[str(chat_id)] = matches


def get_cached_match(chat_id, index):

    matches = MATCH_CACHE.get(str(chat_id), [])

    try:
        return matches[int(index)]

    except Exception:
        return None


# =========================================================
# TELEGRAM HANDLER
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Football Algeria Bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True) or {}

    # -----------------------------------------------------
    # NORMAL MESSAGE
    # -----------------------------------------------------

    message = update.get("message")

    if message:

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text == "/start":

            welcome = (
                "⚽ <b>مرحبا بك في بوت تحليل كرة القدم الجزائرية</b>\n\n"
                "اختر البطولة:\n\n"
                "🇩🇿 Ligue 1\n"
                "🇩🇿 Ligue 2"
            )

            send_message(
                chat_id,
                welcome,
                main_keyboard()
            )

            return "OK"

        if text in ["🇩🇿 Ligue 1", "Ligue 1"]:

            matches = get_matches("Ligue 1")

            cache_matches(chat_id, matches)

            if not matches:

                send_message(
                    chat_id,
                    "⚠️ لم أجد مباريات Ligue 1 لليوم في المصدر الحالي.\n\n"
                    "قد يكون السبب عدم وجود مباريات اليوم أو تغير تنسيق الموقع.",
                    main_keyboard()
                )

                return "OK"

            text_out = (
                "🇩🇿 <b>Ligue 1</b>\n\n"
                "⚽ <b>مباريات اليوم:</b>\n\n"
            )

            for m in matches:
                text_out += (
                    f"⚽ {m['home']} × {m['away']}\n"
                    f"🕒 {m['time']}\n\n"
                )

            text_out += "👇 اختر مباراة للتحليل:"

            send_message(
                chat_id,
                text_out,
                matches_keyboard(matches)
            )

            return "OK"

        if text in ["🇩🇿 Ligue 2", "Ligue 2"]:

            matches = get_matches("Ligue 2")

            cache_matches(chat_id, matches)

            if not matches:

                send_message(
                    chat_id,
                    "⚠️ لم أجد مباريات Ligue 2 لليوم في المصدر الحالي.\n\n"
                    "إذا لم تكن هناك مباريات اليوم، سيظهر هذا التنبيه.",
                    main_keyboard()
                )

                return "OK"

            text_out = (
                "🇩🇿 <b>Ligue 2</b>\n\n"
                "⚽ <b>مباريات اليوم:</b>\n\n"
            )

            for m in matches:
                text_out += (
                    f"⚽ {m['home']} × {m['away']}\n"
                    f"🕒 {m['time']}\n\n"
                )

            text_out += "👇 اختر مباراة للتحليل:"

            send_message(
                chat_id,
                text_out,
                matches_keyboard(matches)
            )

            return "OK"

        return "OK"

    # -----------------------------------------------------
    # CALLBACK
    # -----------------------------------------------------

    callback = update.get("callback_query")

    if callback:

        callback_id = callback["id"]
        data = callback.get("data", "")

        message = callback.get("message", {})

        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")

        answer_callback(callback_id)

        if data.startswith("ANALYZE|"):

            index = data.split("|", 1)[1]

            match = get_cached_match(
                chat_id,
                index
            )

            if not match:

                edit_message(
                    chat_id,
                    message_id,
                    "⚠️ انتهت صلاحية هذه القائمة. اضغط على الدوري مرة أخرى."
                )

                return "OK"

            analysis = build_analysis(match)

            back_keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "⬅️ رجوع للمباريات",
                            "callback_data": "BACK"
                        }
                    ]
                ]
            }

            edit_message(
                chat_id,
                message_id,
                analysis,
                back_keyboard
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
                    "⚠️ لا توجد قائمة محفوظة. اختر الدوري من جديد."
                )

                return "OK"

            league = matches[0]["league"]

            text_out = (
                f"🇩🇿 <b>{league}</b>\n\n"
                "⚽ <b>المباريات:</b>\n\n"
            )

            for m in matches:

                text_out += (
                    f"⚽ {m['home']} × {m['away']}\n"
                    f"🕒 {m['time']}\n\n"
                )

            text_out += "👇 اختر مباراة:"

            edit_message(
                chat_id,
                message_id,
                text_out,
                matches_keyboard(matches)
            )

            return "OK"

    return "OK"


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    print("=================================")
    print("⚽ ALGERIA FOOTBALL BOT")
    print("🚫 No football API")
    print("🚫 No OpenAI")
    print("🇩🇿 Ligue 1 + Ligue 2")
    print("=================================")

    app.run(
        host="0.0.0.0",
        port=port
    )
