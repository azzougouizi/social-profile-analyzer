import os
import random
import sqlite3

from flask import Flask, request
import requests


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 كود الدخول الموحد لجميع التلاميذ
ACCESS_CODE = "BAC2026"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "students.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER PRIMARY KEY,
            access_granted INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


init_db()


def get_student(chat_id):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE chat_id = ?",
        (chat_id,)
    )

    student = cursor.fetchone()

    conn.close()

    return student


def create_student(chat_id):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO students
        (chat_id, access_granted, score, correct, wrong)
        VALUES (?, 0, 0, 0, 0)
    """, (chat_id,))

    conn.commit()
    conn.close()


def grant_access(chat_id):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE students
        SET access_granted = 1
        WHERE chat_id = ?
    """, (chat_id,))

    conn.commit()
    conn.close()


def update_score(chat_id, correct):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if correct:

        cursor.execute("""
            UPDATE students
            SET score = score + 10,
                correct = correct + 1
            WHERE chat_id = ?
        """, (chat_id,))

    else:

        cursor.execute("""
            UPDATE students
            SET wrong = wrong + 1
            WHERE chat_id = ?
        """, (chat_id,))

    conn.commit()
    conn.close()


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
# KEYBOARD
# =========================================================

def main_keyboard():

    return {
        "keyboard": [

            ["🎲 سؤال عشوائي"],

            ["📅 أسئلة التواريخ"],

            ["🇩🇿 تاريخ الجزائر"],

            ["🌍 التاريخ العالمي"],

            ["📝 اختبار 10 أسئلة"],

            ["📊 نتائجي"]

        ],

        "resize_keyboard": True
    }


# =========================================================
# QUESTIONS DATABASE
# يمكنك إضافة مئات الأسئلة هنا
# =========================================================

QUESTIONS = [

    {
        "category": "dates",

        "question":
        "في أي سنة اندلعت الثورة التحريرية الجزائرية؟",

        "options": [
            "1954",
            "1962",
            "1945",
            "1830"
        ],

        "correct": 0
    },

    {
        "category": "dates",

        "question":
        "في أي سنة استقلت الجزائر؟",

        "options": [
            "1954",
            "1962",
            "1965",
            "1945"
        ],

        "correct": 1
    },

    {
        "category": "algeria",

        "question":
        "من هو قائد المنطقة التاريخية الأولى أثناء الثورة التحريرية؟",

        "options": [
            "مصطفى بن بولعيد",
            "ديدوش مراد",
            "العربي بن مهيدي",
            "كريم بلقاسم"
        ],

        "correct": 0
    },

    {
        "category": "algeria",

        "question":
        "في أي تاريخ اندلعت الثورة التحريرية الجزائرية؟",

        "options": [
            "1 نوفمبر 1954",
            "5 جويلية 1962",
            "8 ماي 1945",
            "19 مارس 1962"
        ],

        "correct": 0
    },

    {
        "category": "world",

        "question":
        "ما هي المنظمة الدولية التي تأسست سنة 1945؟",

        "options": [
            "حلف الناتو",
            "الأمم المتحدة",
            "حلف وارسو",
            "الاتحاد الأوروبي"
        ],

        "correct": 1
    },

    {
        "category": "world",

        "question":
        "في أي سنة تأسس حلف شمال الأطلسي؟",

        "options": [
            "1945",
            "1949",
            "1955",
            "1961"
        ],

        "correct": 1
    },

    {
        "category": "world",

        "question":
        "في أي سنة تأسس حلف وارسو؟",

        "options": [
            "1949",
            "1955",
            "1962",
            "1945"
        ],

        "correct": 1
    },

    {
        "category": "dates",

        "question":
        "في أي سنة وقعت أحداث 8 ماي في الجزائر؟",

        "options": [
            "1939",
            "1945",
            "1954",
            "1962"
        ],

        "correct": 1
    },

    {
        "category": "world",

        "question":
        "من هو أول رئيس للولايات المتحدة الأمريكية بعد الحرب العالمية الثانية؟",

        "options": [
            "فرانكلين روزفلت",
            "هاري ترومان",
            "جون كينيدي",
            "ريتشارد نيكسون"
        ],

        "correct": 1
    },

    {
        "category": "algeria",

        "question":
        "ما هو التنظيم السياسي الذي قاد الثورة التحريرية الجزائرية؟",

        "options": [
            "حزب الشعب الجزائري",
            "جبهة التحرير الوطني",
            "نجم شمال إفريقيا",
            "جمعية العلماء المسلمين"
        ],

        "correct": 1
    },

    {
        "category": "dates",

        "question":
        "في أي سنة تم توقيع اتفاقيات إيفيان؟",

        "options": [
            "1958",
            "1960",
            "1962",
            "1965"
        ],

        "correct": 2
    },

    {
        "category": "algeria",

        "question":
        "من هو أحد مفجري الثورة التحريرية الجزائرية؟",

        "options": [
            "مصطفى بن بولعيد",
            "هواري بومدين",
            "أحمد بن بلة",
            "فرحات عباس"
        ],

        "correct": 0
    }

]


# =========================================================
# SEND QUESTION
# =========================================================

def send_question(chat_id, category=None):

    questions = QUESTIONS

    if category:

        questions = [
            q for q in QUESTIONS
            if q["category"] == category
        ]

    if not questions:

        send_message(
            chat_id,
            "❌ لا توجد أسئلة في هذا القسم حاليًا."
        )

        return

    question_id = random.randint(
        100000,
        999999
    )

    question = random.choice(
        questions
    )

    text = (
        "━━━━━━━━━━━━━━━━━━\n"
        "📚 سؤال تاريخ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"❓ {question['question']}\n\n"
    )

    keyboard = []

    letters = ["A", "B", "C", "D"]

    for index, option in enumerate(
        question["options"]
    ):

        text += (
            f"{letters[index]}) {option}\n"
        )

        keyboard.append([

            {
                "text":
                f"{letters[index]}️⃣ {option}",

                "callback_data":
                f"answer:{question_id}:{index}:{question['correct']}"
            }

        ])

    # حفظ السؤال مؤقتًا في الذاكرة
    ACTIVE_QUESTIONS[question_id] = question

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# ACTIVE QUESTIONS
# =========================================================

ACTIVE_QUESTIONS = {}


# =========================================================
# RESULTS
# =========================================================

def show_results(chat_id):

    student = get_student(chat_id)

    if not student:

        return

    score = student[2]
    correct = student[3]
    wrong = student[4]

    total = correct + wrong

    if total > 0:

        percentage = (
            correct / total * 100
        )

    else:

        percentage = 0

    text = f"""
━━━━━━━━━━━━━━━━━━
📊 نتائجك
━━━━━━━━━━━━━━━━━━

⭐ النقاط: {score}

✅ إجابات صحيحة: {correct}

❌ إجابات خاطئة: {wrong}

📈 نسبة النجاح:
{percentage:.1f}%

━━━━━━━━━━━━━━━━━━
"""

    send_message(
        chat_id,
        text
    )


# =========================================================
# CALLBACK HANDLER
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

    answer_callback(callback_id)

    # =====================================================
    # ANSWER
    # =====================================================

    if data.startswith("answer:"):

        parts = data.split(":")

        question_id = int(parts[1])

        selected = int(parts[2])

        correct_answer = int(parts[3])

        if selected == correct_answer:

            update_score(
                chat_id,
                True
            )

            send_message(
                chat_id,
                "✅ إجابة صحيحة! 🎉\n\n"
                "⭐ ربحت 10 نقاط."
            )

        else:

            update_score(
                chat_id,
                False
            )

            question = ACTIVE_QUESTIONS.get(
                question_id
            )

            correct_text = ""

            if question:

                correct_text = (
                    question["options"]
                    [correct_answer]
                )

            send_message(
                chat_id,
                "❌ إجابة خاطئة.\n\n"
                f"✅ الإجابة الصحيحة هي:\n"
                f"{correct_text}"
            )

        # حذف السؤال
        ACTIVE_QUESTIONS.pop(
            question_id,
            None
        )

        return "OK"

    return "OK"


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

    # إنشاء المستخدم
    create_student(chat_id)

    student = get_student(chat_id)

    access_granted = student[1]

    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        if access_granted:

            send_message(
                chat_id,
                "🇩🇿📚 مرحبًا بك مجددًا!\n\n"
                "اختر نوع الأسئلة:",
                main_keyboard()
            )

        else:

            send_message(
                chat_id,
                "🇩🇿📚 مرحبًا بك في بوت\n"
                "تاريخ البكالوريا الجزائرية\n\n"
                "🔐 أدخل كود الدخول:"
            )

        return "OK"

    # =====================================================
    # ACCESS CODE
    # =====================================================

    if not access_granted:

        if text == ACCESS_CODE:

            grant_access(chat_id)

            send_message(
                chat_id,
                "✅ تم الدخول بنجاح! 🎉\n\n"
                "📚 مرحبًا بك في بوت تاريخ "
                "البكالوريا الجزائرية 🇩🇿\n\n"
                "اختر القسم:",
                main_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ كود الدخول غير صحيح.\n\n"
                "🔐 حاول مرة أخرى:"
            )

        return "OK"

    # =====================================================
    # RANDOM QUESTION
    # =====================================================

    if text == "🎲 سؤال عشوائي":

        send_question(chat_id)

        return "OK"

    # =====================================================
    # DATES
    # =====================================================

    if text == "📅 أسئلة التواريخ":

        send_question(
            chat_id,
            "dates"
        )

        return "OK"

    # =====================================================
    # ALGERIA
    # =====================================================

    if text == "🇩🇿 تاريخ الجزائر":

        send_question(
            chat_id,
            "algeria"
        )

        return "OK"

    # =====================================================
    # WORLD
    # =====================================================

    if text == "🌍 التاريخ العالمي":

        send_question(
            chat_id,
            "world"
        )

        return "OK"

    # =====================================================
    # EXAM
    # =====================================================

    if text == "📝 اختبار 10 أسئلة":

        send_message(
            chat_id,
            "📝 سيتم إرسال أسئلة عشوائية.\n\n"
            "ابدأ بالسؤال الأول 👇"
        )

        send_question(chat_id)

        return "OK"

    # =====================================================
    # RESULTS
    # =====================================================

    if text == "📊 نتائجي":

        show_results(chat_id)

        return "OK"

    # =====================================================
    # UNKNOWN
    # =====================================================

    send_message(
        chat_id,
        "اختر أحد الأزرار من القائمة 👇",
        main_keyboard()
    )

    return "OK"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return (
        "🇩🇿 History BAC Bot is running!"
    )


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
