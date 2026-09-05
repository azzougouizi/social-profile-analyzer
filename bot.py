import os
import requests
from flask import Flask, request

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 كود الدخول الموحد
ACCESS_CODE = "1230"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)


# =========================================================
# TELEGRAM FUNCTIONS
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
            print("❌ Telegram Error:", result)

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
# USERS
# =========================================================

authorized_users = set()


# =========================================================
# MAIN KEYBOARD
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            ["🇩🇿 الدوري الجزائري"],
            ["📅 المباريات"],
            ["🏆 الفرق"],
            ["📊 تحليل مباراة"],
            ["ℹ️ معلومات البوت"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# OPENFOOTBALL
# =========================================================

GITHUB_API = "https://api.github.com/repos/openfootball/world/contents/africa/algeria"


def get_algeria_files():

    try:

        response = requests.get(
            GITHUB_API,
            timeout=20
        )

        if response.status_code != 200:

            print("❌ GitHub Error:", response.status_code)

            return []

        return response.json()

    except Exception as e:

        print("❌ Download Error:", e)

        return []


def get_file_content(download_url):

    try:

        response = requests.get(
            download_url,
            timeout=20
        )

        if response.status_code == 200:
            return response.text

    except Exception as e:

        print("❌ File Error:", e)

    return None


# =========================================================
# PARSE FOOTBALL.TXT
# =========================================================

def parse_matches(content):

    matches = []

    if not content:
        return matches

    lines = content.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # نبحث عن مباريات تحتوي على v
        if " v " in line:

            parts = line.split(" v ")

            if len(parts) != 2:
                continue

            home = parts[0].strip()

            away_part = parts[1].strip()

            # إزالة النتيجة إن وجدت
            away = away_part

            score = ""

            words = away_part.split()

            for i, word in enumerate(words):

                if "-" in word and any(
                    char.isdigit()
                    for char in word
                ):

                    away = " ".join(words[:i])

                    score = " ".join(words[i:])

                    break

            matches.append({
                "home": home,
                "away": away,
                "score": score
            })

    return matches


# =========================================================
# GET ALGERIAN DATA
# =========================================================

def get_algerian_matches():

    files = get_algeria_files()

    all_matches = []

    for file in files:

        name = file.get("name", "")

        # ملفات txt فقط
        if not name.endswith(".txt"):
            continue

        download_url = file.get("download_url")

        if not download_url:
            continue

        print("📥 Loading:", name)

        content = get_file_content(
            download_url
        )

        matches = parse_matches(content)

        all_matches.extend(matches)

    return all_matches


# =========================================================
# SHOW MATCHES
# =========================================================

def show_matches(chat_id):

    send_message(
        chat_id,
        "⏳ جاري تحميل بيانات الدوري الجزائري..."
    )

    matches = get_algerian_matches()

    if not matches:

        send_message(
            chat_id,
            "❌ لم يتم العثور على مباريات حاليًا.\n\n"
            "قد تكون بيانات المصدر غير متوفرة أو تغيرت."
        )

        return

    text = (
        "🇩🇿⚽ الدوري الجزائري\n"
        "━━━━━━━━━━━━━━━━\n\n"
    )

    # عرض آخر 20 مباراة فقط
    for match in matches[-20:]:

        home = match["home"]
        away = match["away"]
        score = match["score"]

        text += (
            f"🏠 {home}\n"
            f"✈️ {away}\n"
        )

        if score:
            text += f"⚽ {score}\n"

        text += "━━━━━━━━━━━━\n"

    # Telegram limit
    if len(text) > 4000:
        text = text[:4000]

    send_message(
        chat_id,
        text
    )


# =========================================================
# SHOW TEAMS
# =========================================================

def show_teams(chat_id):

    matches = get_algerian_matches()

    teams = set()

    for match in matches:

        teams.add(match["home"])
        teams.add(match["away"])

    if not teams:

        send_message(
            chat_id,
            "❌ لم يتم العثور على الفرق."
        )

        return

    teams = sorted(teams)

    text = (
        "🇩🇿🏆 فرق الدوري الجزائري\n"
        "━━━━━━━━━━━━━━━━\n\n"
    )

    for i, team in enumerate(teams, 1):

        text += f"{i}. ⚽ {team}\n"

    if len(text) > 4000:
        text = text[:4000]

    send_message(
        chat_id,
        text
    )


# =========================================================
# SIMPLE ANALYSIS
# =========================================================

def analyze_match(chat_id):

    matches = get_algerian_matches()

    if not matches:

        send_message(
            chat_id,
            "❌ لا توجد بيانات كافية للتحليل."
        )

        return

    text = (
        "📊⚽ تحليل الدوري الجزائري\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🤖 التحليل يعتمد على النتائج "
        "المتوفرة في قاعدة البيانات.\n\n"
        "📈 يمكنك استخدام بيانات المباريات "
        "لمقارنة الفرق ونتائجها السابقة.\n\n"
        "⚠️ هذا تحليل معلوماتي فقط "
        "ولا يضمن نتائج مستقبلية."
    )

    send_message(
        chat_id,
        text
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    update = request.get_json(
        silent=True
    ) or {}

    # -----------------------------------------------------
    # CALLBACK
    # -----------------------------------------------------

    callback = update.get("callback_query")

    if callback:

        answer_callback(callback.get("id"))

        return "OK"

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    message = update.get("message")

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

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    if text == "/start":

        if chat_id in authorized_users:

            send_message(
                chat_id,
                "🇩🇿⚽ مرحبًا بك مجددًا!\n\n"
                "اختر من القائمة:",
                main_keyboard()
            )

        else:

            send_message(
                chat_id,
                "🇩🇿⚽ مرحبًا بك في بوت "
                "كرة القدم الجزائرية\n\n"
                "🔐 أدخل كود الدخول:"
            )

        return "OK"

    # -----------------------------------------------------
    # ACCESS
    # -----------------------------------------------------

    if chat_id not in authorized_users:

        if text == ACCESS_CODE:

            authorized_users.add(chat_id)

            send_message(
                chat_id,
                "✅ تم الدخول بنجاح! 🎉\n\n"
                "🇩🇿⚽ مرحبًا بك في بوت "
                "الدوري الجزائري.",
                main_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ كود الدخول غير صحيح.\n\n"
                "🔐 أدخل الكود الصحيح:"
            )

        return "OK"

    # -----------------------------------------------------
    # LEAGUE
    # -----------------------------------------------------

    if text == "🇩🇿 الدوري الجزائري":

        show_matches(chat_id)

        return "OK"

    # -----------------------------------------------------
    # MATCHES
    # -----------------------------------------------------

    if text == "📅 المباريات":

        show_matches(chat_id)

        return "OK"

    # -----------------------------------------------------
    # TEAMS
    # -----------------------------------------------------

    if text == "🏆 الفرق":

        send_message(
            chat_id,
            "⏳ جاري تحميل الفرق..."
        )

        show_teams(chat_id)

        return "OK"

    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    if text == "📊 تحليل مباراة":

        send_message(
            chat_id,
            "⏳ جاري تحليل البيانات..."
        )

        analyze_match(chat_id)

        return "OK"

    # -----------------------------------------------------
    # INFO
    # -----------------------------------------------------

    if text == "ℹ️ معلومات البوت":

        send_message(
            chat_id,
            "🇩🇿⚽ بوت كرة القدم الجزائرية\n\n"
            "📊 يعرض بيانات متوفرة عن "
            "الدوري الجزائري.\n\n"
            "🔐 الدخول محمي بكود.\n\n"
            "🚫 لا يحتاج API Key."
        )

        return "OK"

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    send_message(
        chat_id,
        "اختر أحد الأزرار 👇",
        main_keyboard()
    )

    return "OK"


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "🇩🇿 Algeria Football Bot is running!"


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
