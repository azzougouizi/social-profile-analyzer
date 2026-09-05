import os
import re
import math
import requests
from datetime import datetime
from flask import Flask, request
from bs4 import BeautifulSoup

# =========================================================
# إعدادات
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ACCESS_CODE = "1230"

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

authorized_users = set()

SOURCE_FIXTURES = "https://www.footmercato.net/algerie/ligue-1/calendrier/"
SOURCE_TABLE = "https://www.footmercato.net/algerie/ligue-1/classement/"


# =========================================================
# أسماء الفرق بالعربية
# =========================================================

TEAM_AR = {
    "ASO Chlef": "أولمبي الشلف",
    "Chlef": "أولمبي الشلف",

    "Belouizdad": "شباب بلوزداد",
    "CR Belouizdad": "شباب بلوزداد",

    "CS Constantine": "شباب قسنطينة",
    "Constantine": "شباب قسنطينة",

    "Témouchent": "شباب تموشنت",
    "CR Témouchent": "شباب تموشنت",

    "ES Sétif": "وفاق سطيف",
    "Sétif": "وفاق سطيف",

    "Ben Aknoun": "بن عكنون",
    "ES Ben Aknoun": "بن عكنون",

    "Biar": "شبيبة الأبيار",
    "JS El Biar": "شبيبة الأبيار",

    "Akbou": "أولمبي أقبو",
    "Olympique Akbou": "أولمبي أقبو",

    "Khenchela": "اتحاد خنشلة",
    "USM Khenchela": "اتحاد خنشلة",

    "USM Alger": "اتحاد العاصمة",
    "Kabylie": "شبيبة القبائل",
    "JS Kabylie": "شبيبة القبائل",

    "Rouisset": "مستقبل الرويسات",
    "MB Rouisset": "مستقبل الرويسات",

    "US Biskra": "اتحاد بسكرة",
    "Biskra": "اتحاد بسكرة",

    "Saoura": "شبيبة الساورة",
    "JS Saoura": "شبيبة الساورة",

    "MC Alger": "مولودية الجزائر",
    "MC Oran": "مولودية وهران",
}


def arabic_team(name):
    name = name.strip()

    for key, value in TEAM_AR.items():
        if key.lower() == name.lower():
            return value

    for key, value in TEAM_AR.items():
        if key.lower() in name.lower():
            return value

    return name


# =========================================================
# طلب HTTP
# =========================================================

def get_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/128.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# =========================================================
# Telegram
# =========================================================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=20
        )
    except Exception as e:
        print("Telegram error:", e)


def show_menu(chat_id):
    keyboard = {
        "keyboard": [
            ["📅 مباريات اليوم وتحليلها"],
            ["🏆 الفرق"],
            ["ℹ️ معلومات البوت"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🇩🇿⚽ اختر الخدمة:",
                "reply_markup": keyboard
            },
            timeout=20
        )
    except Exception as e:
        print("Keyboard error:", e)


# =========================================================
# تحويل التاريخ
# =========================================================

MONTHS_FR = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre"
}

DAYS_FR = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche"
}


# =========================================================
# استخراج كل مباريات الصفحة
# =========================================================

def get_all_fixtures():

    html = get_html(SOURCE_FIXTURES)

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n", strip=True)

    lines = [
        x.strip()
        for x in text.split("\n")
        if x.strip()
    ]

    fixtures = []

    current_date = None

    # -----------------------------------------
    # أسماء الفرق الحالية
    # -----------------------------------------

    team_names = list(TEAM_AR.keys())

    for i, line in enumerate(lines):

        lower = line.lower()

        # -----------------------------------------
        # البحث عن تاريخ مثل:
        # samedi 5 septembre 2026
        # -----------------------------------------

        date_match = re.search(
            r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
            r"\s+(\d{1,2})\s+"
            r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
            r"\s+(\d{4})",
            lower
        )

        if date_match:

            day = int(date_match.group(2))
            month_name = date_match.group(3)
            year = int(date_match.group(4))

            month_number = None

            for num, name in MONTHS_FR.items():
                if name == month_name:
                    month_number = num
                    break

            if month_number:
                current_date = datetime(
                    year,
                    month_number,
                    day
                ).date()

            continue

        if current_date is None:
            continue

        # -----------------------------------------
        # وقت المباراة
        # -----------------------------------------

        time_match = re.search(
            r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
            line
        )

        if not time_match:
            continue

        match_time = time_match.group(0)

        # -----------------------------------------
        # نحاول العثور على فريقين حول الوقت
        # -----------------------------------------

        nearby = lines[
            max(0, i - 5): min(len(lines), i + 3)
        ]

        found = []

        for item in nearby:

            for team in team_names:

                if team.lower() in item.lower():

                    if team not in found:
                        found.append(team)

        # -----------------------------------------
        # إذا وجدنا فريقين
        # -----------------------------------------

        if len(found) >= 2:

            home = found[-2]
            away = found[-1]

            fixture = {
                "date": current_date,
                "time": match_time,
                "home": home,
                "away": away
            }

            # منع التكرار
            duplicate = False

            for old in fixtures:

                if (
                    old["date"] == fixture["date"]
                    and old["time"] == fixture["time"]
                    and old["home"] == fixture["home"]
                    and old["away"] == fixture["away"]
                ):
                    duplicate = True
                    break

            if not duplicate:
                fixtures.append(fixture)

    print("📅 Fixtures found:", len(fixtures))

    return fixtures


# =========================================================
# مباريات اليوم
# =========================================================

def get_today_fixtures():

    today = datetime.now().date()

    fixtures = get_all_fixtures()

    today_matches = [
        x for x in fixtures
        if x["date"] == today
    ]

    return today_matches


# =========================================================
# جدول الترتيب الحالي
# =========================================================

def get_current_table():

    try:

        html = get_html(SOURCE_TABLE)

        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all("tr")

        teams = {}

        for row in rows:

            cells = row.find_all(
                ["td", "th"]
            )

            values = [
                cell.get_text(" ", strip=True)
                for cell in cells
            ]

            if len(values) < 5:
                continue

            row_text = " ".join(values)

            # نحاول معرفة الفريق
            team_found = None

            for team in TEAM_AR.keys():

                if team.lower() in row_text.lower():

                    team_found = team
                    break

            if not team_found:
                continue

            # نبحث عن أرقام الجدول
            numbers = []

            for value in values:

                if re.fullmatch(
                    r"-?\d+",
                    value
                ):
                    try:
                        numbers.append(int(value))
                    except:
                        pass

            # غالبًا:
            # Pts J DIF G N D BP BC
            if len(numbers) >= 8:

                # آخر ثمانية أرقام مفيدة
                nums = numbers[-8:]

                points = nums[0]
                played = nums[1]
                diff = nums[2]
                wins = nums[3]
                draws = nums[4]
                losses = nums[5]
                goals_for = nums[6]
                goals_against = nums[7]

                teams[team_found] = {
                    "points": points,
                    "played": played,
                    "wins": wins,
                    "draws": draws,
                    "losses": losses,
                    "gf": goals_for,
                    "ga": goals_against
                }

        print("📊 Teams in table:", len(teams))

        return teams

    except Exception as e:

        print("❌ Table error:", e)

        return {}


# =========================================================
# بيانات أساسية للموسم السابق
#
# تستخدم فقط عندما تكون بيانات الموسم الحالي قليلة جدًا.
# =========================================================

PREVIOUS_SEASON = {

    # الفرق الكبيرة
    "MC Alger": {
        "attack": 1.55,
        "defense": 0.65
    },

    "Belouizdad": {
        "attack": 1.45,
        "defense": 0.75
    },

    "Kabylie": {
        "attack": 1.40,
        "defense": 0.80
    },

    "USM Alger": {
        "attack": 1.35,
        "defense": 0.75
    },

    "ES Sétif": {
        "attack": 1.15,
        "defense": 0.95
    },

    "CS Constantine": {
        "attack": 1.25,
        "defense": 0.95
    },

    "ASO Chlef": {
        "attack": 1.05,
        "defense": 1.00
    },

    "MC Oran": {
        "attack": 1.00,
        "defense": 1.00
    },

    "Saoura": {
        "attack": 1.10,
        "defense": 1.00
    },

    "Khenchela": {
        "attack": 0.95,
        "defense": 1.05
    },

    "Biskra": {
        "attack": 0.95,
        "defense": 1.10
    },

    "Akbou": {
        "attack": 1.05,
        "defense": 1.00
    },

    "Ben Aknoun": {
        "attack": 1.00,
        "defense": 1.05
    },

    "Témouchent": {
        "attack": 0.90,
        "defense": 1.10
    },

    "Biar": {
        "attack": 0.85,
        "defense": 1.15
    },

    "Rouisset": {
        "attack": 0.90,
        "defense": 1.10
    }
}


# =========================================================
# احتمال Poisson
# =========================================================

def poisson_probability(lmbda, goals):

    return (
        math.exp(-lmbda)
        * (lmbda ** goals)
        / math.factorial(goals)
    )


# =========================================================
# قوة الفريق
# =========================================================

def get_team_strength(team, table):

    # -----------------------------------------
    # بيانات الموسم الحالي
    # -----------------------------------------

    current = None

    for key, data in table.items():

        if (
            key.lower() == team.lower()
            or key.lower() in team.lower()
            or team.lower() in key.lower()
        ):
            current = data
            break

    # -----------------------------------------
    # بيانات الموسم السابق
    # -----------------------------------------

    previous = None

    for key, data in PREVIOUS_SEASON.items():

        if (
            key.lower() == team.lower()
            or key.lower() in team.lower()
            or team.lower() in key.lower()
        ):
            previous = data
            break

    # -----------------------------------------
    # إذا لا توجد أي بيانات
    # -----------------------------------------

    if not current and not previous:

        return {
            "attack": 1.00,
            "defense": 1.00
        }

    # -----------------------------------------
    # موسم جديد:
    # نعطي الحالي وزنًا أكبر كلما زاد عدد المباريات
    # -----------------------------------------

    if current:

        played = current["played"]

        if played >= 5:

            attack = max(
                0.45,
                current["gf"] / played
            )

            defense = max(
                0.45,
                current["ga"] / played
            )

            return {
                "attack": attack,
                "defense": defense
            }

        elif played > 0:

            current_attack = current["gf"] / played
            current_defense = current["ga"] / played

            if previous:

                weight_current = min(
                    0.60,
                    played * 0.15
                )

                weight_previous = (
                    1 - weight_current
                )

                attack = (
                    current_attack * weight_current
                    + previous["attack"] * weight_previous
                )

                defense = (
                    current_defense * weight_current
                    + previous["defense"] * weight_previous
                )

                return {
                    "attack": max(0.55, attack),
                    "defense": max(0.55, defense)
                }

    if previous:

        return previous

    return {
        "attack": 1.00,
        "defense": 1.00
    }


# =========================================================
# حساب المباراة
# =========================================================

def calculate_match(home, away, table):

    home_strength = get_team_strength(
        home,
        table
    )

    away_strength = get_team_strength(
        away,
        table
    )

    # -----------------------------------------------------
    # متوسط الدوري الجزائري التقريبي
    # -----------------------------------------------------

    league_average = 1.15

    # -----------------------------------------------------
    # قوة الهجوم × ضعف دفاع الخصم
    # -----------------------------------------------------

    home_lambda = (
        league_average
        * home_strength["attack"]
        / max(0.65, away_strength["defense"])
    )

    away_lambda = (
        league_average
        * away_strength["attack"]
        / max(0.65, home_strength["defense"])
    )

    # أفضلية الأرض
    home_lambda *= 1.08

    # حدود منطقية
    home_lambda = max(
        0.25,
        min(home_lambda, 3.50)
    )

    away_lambda = max(
        0.20,
        min(away_lambda, 3.00)
    )

    # -----------------------------------------------------
    # مصفوفة النتائج 0-0 إلى 6-6
    # -----------------------------------------------------

    matrix = {}

    home_win = 0
    draw = 0
    away_win = 0

    for h in range(7):

        for a in range(7):

            p = (
                poisson_probability(
                    home_lambda,
                    h
                )
                *
                poisson_probability(
                    away_lambda,
                    a
                )
            )

            matrix[(h, a)] = p

            if h > a:
                home_win += p

            elif h == a:
                draw += p

            else:
                away_win += p

    total = home_win + draw + away_win

    home_win /= total
    draw /= total
    away_win /= total

    # -----------------------------------------------------
    # احتمالات مجموع الأهداف
    # -----------------------------------------------------

    goal_lines = {}

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5
    ]:

        under = 0

        for (h, a), p in matrix.items():

            if h + a <= int(line):

                under += p

        under /= total

        over = 1 - under

        goal_lines[line] = {
            "over": over,
            "under": under
        }

    # -----------------------------------------------------
    # أكثر النتائج احتمالًا
    # -----------------------------------------------------

    top_scores = sorted(
        matrix.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    # -----------------------------------------------------
    # BTTS
    # -----------------------------------------------------

    btts_yes = 0

    for (h, a), p in matrix.items():

        if h >= 1 and a >= 1:
            btts_yes += p

    btts_yes /= total

    btts_no = 1 - btts_yes

    # -----------------------------------------------------
    # مجموع الأهداف المتوقع
    # -----------------------------------------------------

    expected_goals = (
        home_lambda
        + away_lambda
    )

    return {
        "home_lambda": home_lambda,
        "away_lambda": away_lambda,
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "goal_lines": goal_lines,
        "btts_yes": btts_yes,
        "btts_no": btts_no,
        "expected_goals": expected_goals,
        "top_scores": top_scores
    }


# =========================================================
# تحويل النسبة
# =========================================================

def pct(value):

    return round(
        value * 100
    )


# =========================================================
# اختيار التوقع الأقوى
# =========================================================

def strongest_result(analysis, home, away):

    options = [
        (
            analysis["home_win"],
            f"فوز {arabic_team(home)}"
        ),
        (
            analysis["draw"],
            "التعادل"
        ),
        (
            analysis["away_win"],
            f"فوز {arabic_team(away)}"
        )
    ]

    options.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return options[0]


# =========================================================
# إنشاء تحليل المباراة
# =========================================================

def format_analysis(match, analysis):

    home = arabic_team(
        match["home"]
    )

    away = arabic_team(
        match["away"]
    )

    best_result = strongest_result(
        analysis,
        match["home"],
        match["away"]
    )

    # -----------------------------------------------------
    # أفضل نتيجة صحيحة
    # -----------------------------------------------------

    score = analysis["top_scores"][0][0]

    score_probability = analysis["top_scores"][0][1]

    # -----------------------------------------------------
    # خطوط الأهداف
    # -----------------------------------------------------

    lines = analysis["goal_lines"]

    text = (
        f"⚽ <b>{home}</b> 🆚 <b>{away}</b>\n"
        f"🕐 {match['time']}\n\n"

        f"📊 <b>تحليل المباراة</b>\n\n"

        f"🏠 فوز {home}: "
        f"<b>{pct(analysis['home_win'])}%</b>\n"

        f"🤝 التعادل: "
        f"<b>{pct(analysis['draw'])}%</b>\n"

        f"🚩 فوز {away}: "
        f"<b>{pct(analysis['away_win'])}%</b>\n\n"

        f"🎯 <b>أقوى احتمال:</b>\n"
        f"{best_result[1]} "
        f"({pct(best_result[0])}%)\n\n"

        f"🥅 <b>إجمالي الأهداف المتوقع:</b> "
        f"<b>{analysis['expected_goals']:.2f}</b>\n\n"

        f"📈 <b>خطوط الأهداف:</b>\n"

        f"0.5+ : <b>{pct(lines[0.5]['over'])}%</b>\n"
        f"1.5+ : <b>{pct(lines[1.5]['over'])}%</b>\n"
        f"2.5+ : <b>{pct(lines[2.5]['over'])}%</b>\n"
        f"3.5+ : <b>{pct(lines[3.5]['over'])}%</b>\n"
        f"4.5+ : <b>{pct(lines[4.5]['over'])}%</b>\n"
        f"5.5+ : <b>{pct(lines[5.5]['over'])}%</b>\n\n"

        f"📉 <b>أقل من:</b>\n"

        f"0.5 : <b>{pct(lines[0.5]['under'])}%</b>\n"
        f"1.5 : <b>{pct(lines[1.5]['under'])}%</b>\n"
        f"2.5 : <b>{pct(lines[2.5]['under'])}%</b>\n"
        f"3.5 : <b>{pct(lines[3.5]['under'])}%</b>\n"
        f"4.5 : <b>{pct(lines[4.5]['under'])}%</b>\n"
        f"5.5 : <b>{pct(lines[5.5]['under'])}%</b>\n\n"

        f"🔄 <b>يسجل الفريقان:</b>\n"
        f"نعم: <b>{pct(analysis['btts_yes'])}%</b>\n"
        f"لا: <b>{pct(analysis['btts_no'])}%</b>\n\n"

        f"🔢 <b>أكثر النتائج احتمالًا:</b>\n"
    )

    for score_pair, probability in analysis["top_scores"]:

        h, a = score_pair

        text += (
            f"{h} - {a} : "
            f"<b>{pct(probability)}%</b>\n"
        )

    text += (
        "\n⚠️ <i>التحليل إحصائي تقديري مبني على "
        "بيانات النتائج المتاحة ونموذج احتمالي، "
        "وليس ضمانًا للنتيجة.</i>"
    )

    return text


# =========================================================
# عرض مباريات اليوم
# =========================================================

def show_today_matches(chat_id):

    try:

        matches = get_today_fixtures()

        if not matches:

            now = datetime.now()

            send_message(
                chat_id,
                f"📅 <b>مباريات اليوم</b>\n\n"
                f"📆 {now.strftime('%d/%m/%Y')}\n\n"
                f"⚽ لا توجد مباريات للدوري الجزائري "
                f"مسجلة اليوم حاليًا."
            )

            return

        table = get_current_table()

        now = datetime.now()

        header = (
            f"🇩🇿 <b>مباريات الدوري الجزائري اليوم</b>\n"
            f"📆 {now.strftime('%d/%m/%Y')}\n\n"
        )

        send_message(
            chat_id,
            header
        )

        for index, match in enumerate(
            matches,
            1
        ):

            print(
                "🔎 تحليل:",
                match["home"],
                match["away"]
            )

            analysis = calculate_match(
                match["home"],
                match["away"],
                table
            )

            message = (
                f"━━━━━━━━━━━━━━\n"
                f"<b>المباراة {index}</b>\n\n"
                +
                format_analysis(
                    match,
                    analysis
                )
            )

            send_message(
                chat_id,
                message
            )

    except Exception as e:

        print(
            "❌ Today matches error:",
            e
        )

        send_message(
            chat_id,
            "❌ حدث خطأ أثناء جلب مباريات اليوم وتحليلها.\n"
            "حاول مرة أخرى بعد قليل."
        )


# =========================================================
# الفرق
# =========================================================

def show_teams(chat_id):

    teams = [
        "مولودية الجزائر",
        "شباب بلوزداد",
        "شبيبة القبائل",
        "اتحاد العاصمة",
        "وفاق سطيف",
        "شباب قسنطينة",
        "مولودية وهران",
        "شبيبة الساورة",
        "أولمبي الشلف",
        "اتحاد خنشلة",
        "اتحاد بسكرة",
        "أولمبي أقبو",
        "بن عكنون",
        "شباب تموشنت",
        "شبيبة الأبيار",
        "مستقبل الرويسات"
    ]

    text = (
        "🇩🇿 <b>أندية الدوري الجزائري</b>\n\n"
    )

    for team in teams:
        text += f"⚽ {team}\n"

    send_message(
        chat_id,
        text
    )


# =========================================================
# معلومات
# =========================================================

def show_info(chat_id):

    text = """
ℹ️ <b>معلومات البوت</b>

🇩🇿 بوت الدوري الجزائري

📅 <b>مباريات اليوم وتحليلها</b>

عند الضغط على الزر، البوت:
• يحدد تاريخ اليوم تلقائيًا
• يجلب مباريات اليوم
• يعرض كل مباراة منفصلة
• يحسب احتمال الفوز والتعادل
• يحسب إجمالي الأهداف المتوقع
• يحسب 0.5+ إلى 5.5+
• يحسب أقل من 0.5 إلى 5.5
• يحسب احتمال تسجيل الفريقين
• يعرض أكثر النتائج احتمالًا

🔐 كود الدخول: 1230

🌐 لا يحتاج إلى Football API Key.

⚠️ النتائج احتمالات إحصائية وليست ضمانًا.
"""

    send_message(
        chat_id,
        text
    )


# =========================================================
# Webhook
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    try:

        data = request.get_json(
            force=True
        )

        message = data.get(
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

        if not chat_id:
            return "OK", 200

        text = message.get(
            "text",
            ""
        ).strip()

        # -----------------------------------------
        # التحقق من الدخول
        # -----------------------------------------

        if chat_id not in authorized_users:

            if text == ACCESS_CODE:

                authorized_users.add(
                    chat_id
                )

                send_message(
                    chat_id,
                    "✅ <b>تم الدخول بنجاح</b>\n\n"
                    "🇩🇿 مرحبًا بك في بوت الدوري الجزائري ⚽"
                )

                show_menu(chat_id)

            else:

                send_message(
                    chat_id,
                    "🔐 <b>أرسل كود الدخول:</b>"
                )

            return "OK", 200

        # -----------------------------------------
        # Start
        # -----------------------------------------

        if text == "/start":

            show_menu(chat_id)

        # -----------------------------------------
        # مباريات اليوم
        # -----------------------------------------

        elif text == "📅 مباريات اليوم وتحليلها":

            show_today_matches(
                chat_id
            )

        # -----------------------------------------
        # الفرق
        # -----------------------------------------

        elif text == "🏆 الفرق":

            show_teams(
                chat_id
            )

        # -----------------------------------------
        # المعلومات
        # -----------------------------------------

        elif text == "ℹ️ معلومات البوت":

            show_info(
                chat_id
            )

        else:

            send_message(
                chat_id,
                "اختر الخدمة من القائمة 👇"
            )

        return "OK", 200

    except Exception as e:

        print(
            "❌ Webhook error:",
            e
        )

        return "OK", 200


# =========================================================
# Routes
# =========================================================

@app.route("/")
def home():
    return "Algerian Football Bot 🇩🇿⚽"


@app.route("/health")
def health():
    return "OK"


# =========================================================
# تشغيل
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
