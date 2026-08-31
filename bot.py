import os
import random
import sqlite3
import requests
from flask import Flask, request

from questions import QUESTIONS


app = Flask(__name__)


# =========================================================
# إعدادات
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود في Environment Variables")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

DB_FILE = "students.db"


# =========================================================
# قاعدة البيانات
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER PRIMARY KEY,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            stars INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def ensure_student(chat_id):

    conn = get_db()

    conn.execute("""
        INSERT OR IGNORE INTO students
        (chat_id, correct, wrong, total, best_streak, current_streak, stars)
        VALUES (?, 0, 0, 0, 0, 0, 0)
    """, (chat_id,))

    conn.commit()
    conn.close()


def get_student(chat_id):

    ensure_student(chat_id)

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM students
        WHERE chat_id = ?
    """, (chat_id,)).fetchone()

    conn.close()

    return row


def update_student(
    chat_id,
    correct=False
):

    ensure_student(chat_id)

    conn = get_db()

    if correct:

        conn.execute("""
            UPDATE students
            SET
                correct = correct + 1,
                total = total + 1,
                current_streak = current_streak + 1
            WHERE chat_id = ?
        """, (chat_id,))

    else:

        conn.execute("""
            UPDATE students
            SET
                wrong = wrong + 1,
                total = total + 1,
                current_streak = 0
            WHERE chat_id = ?
        """, (chat_id,))

    conn.execute("""
        UPDATE students
        SET best_streak =
            CASE
                WHEN current_streak > best_streak
                THEN current_streak
                ELSE best_streak
            END
        WHERE chat_id = ?
    """, (chat_id,))

    conn.commit()
    conn.close()


# =========================================================
# نظام النجوم
# =========================================================

def calculate_stars(correct):

    if correct >= 200:
        return 5

    if correct >= 150:
        return 4

    if correct >= 100:
        return 3

    if correct >= 60:
        return 2

    if correct >= 30:
        return 1

    return 0


def star_title(stars):

    titles = {
        0: "🌱 بداية الطريق",
        1: "⭐ طالب طموح",
        2: "⭐⭐ طالب مجتهد",
        3: "⭐⭐⭐ طالب متفوق",
        4: "⭐⭐⭐⭐ طالب متميز",
        5: "⭐⭐⭐⭐⭐ طالب قوي وذكي"
    }

    return titles.get(
        stars,
        "🌱 بداية الطريق"
    )


def next_star(correct):

    if correct < 30:
        return 30, 1

    if correct < 60:
        return 60, 2

    if correct < 100:
        return 100, 3

    if correct < 150:
        return 150, 4

    if correct < 200:
        return 200, 5

    return None, 5


def check_star_upgrade(chat_id):

    student = get_student(chat_id)

    old_stars = student["stars"]

    new_stars = calculate_stars(
        student["correct"]
    )

    if new_stars <= old_stars:
        return

    conn = get_db()

    conn.execute("""
        UPDATE students
        SET stars = ?
        WHERE chat_id = ?
    """, (
        new_stars,
        chat_id
    ))

    conn.commit()
    conn.close()

    title = star_title(
        new_stars
    )

    messages = {
        1:
            "🎉 مبروك!\n\n"
            "لقد وصلت إلى أول نجمة! ⭐\n"
            "أنت الآن: طالب طموح.\n\n"
            "🔥 البداية ممتازة، لا تتوقف!",

        2:
            "🎉 إنجاز رائع!\n\n"
            "⭐⭐ حصلت على نجمتين!\n"
            "أنت الآن: طالب مجتهد.\n\n"
            "🚀 واصل، النجمة الثالثة تنتظرك!",

        3:
            "🏆 مذهل!\n\n"
            "⭐⭐⭐ حصلت على ثلاث نجوم!\n"
            "أنت الآن: طالب متفوق.\n\n"
            "🧠 مستواك يرتفع، استمر!",

        4:
            "🔥 رائع جدًا!\n\n"
            "⭐⭐⭐⭐ وصلت إلى أربع نجوم!\n"
            "أنت الآن: طالب متميز.\n\n"
            "🎯 لم يبقَ إلا النجمة الخامسة!",

        5:
            "🏆🔥 إنجاز استثنائي!\n\n"
            "⭐⭐⭐⭐⭐\n"
            "أنت الآن: طالب قوي وذكي!\n\n"
            "🧠 200 إجابة صحيحة!\n"
            "لقد أثبتَّ أن الاستمرار يصنع النجاح.\n\n"
            "🎓 لا تتوقف حتى تحقق هدفك في البكالوريا!"
    }

    send_message(
        chat_id,
        messages.get(
            new_stars,
            f"🎉 مبروك!\n{title}"
        )
    )


# =========================================================
# حالة الاختبارات
# =========================================================

quiz_sessions = {}


# =========================================================
# Telegram API
# =========================================================

def telegram(method, data):

    if not TELEGRAM_API:
        return None

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=20
        )

        print(
            f"Telegram {method}: "
            f"HTTP {response.status_code}"
        )

        if not response.ok:

            print(
                "Telegram response:",
                response.text
            )

        return response.json()

    except Exception as error:

        print(
            "❌ Telegram error:",
            error
        )

        return None


def send_message(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram(
        "sendMessage",
        data
    )


def answer_callback(callback_id):

    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


def edit_message(
    chat_id,
    message_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram(
        "editMessageText",
        data
    )


# =========================================================
# القوائم
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            ["🧠 الفلسفة"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🇪🇸 الإسبانية"],
            ["📄 مواضيع البكالوريا"],
            ["📊 مستواي"],
            ["🏆 الإنجازات"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


def philosophy_keyboard():

    return {
        "keyboard": [
            ["📝 اختبار فلسفة"],
            ["💡 مفاهيم فلسفية"],
            ["👨‍🏫 الفلاسفة"],
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }


def language_keyboard():

    return {
        "keyboard": [
            ["📝 اختبار اللغة"],
            ["📚 كلمات مهمة"],
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }


def bac_keyboard():

    return {
        "keyboard": [
            ["📚 آداب وفلسفة"],
            ["🌍 لغات أجنبية"],
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# رسائل تحفيزية
# =========================================================

MOTIVATION = [
    "🔥 ممتاز! استمر، كل إجابة تقربك من هدفك.",
    "💪 لا تستسلم! الخطأ اليوم قد يصبح نقطة قوة غدًا.",
    "🧠 رائع! أنت تتعلم مع كل سؤال.",
    "🚀 استمر! النجاح نتيجة الاستمرارية.",
    "🎯 ركّز، تقدّمك واضح!",
    "🏆 بطل! سؤال آخر وقد تتجاوز مستواك السابق.",
    "📚 المعرفة تتراكم، لا تتوقف.",
    "🔥 هكذا نريدك! طموح ومستمر."
]


# =========================================================
# بدء الاختبار
# =========================================================

def start_quiz(
    chat_id,
    subject
):

    questions = QUESTIONS.get(
        subject,
        []
    )

    if not questions:

        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة حاليًا."
        )

        return

    count = min(
        10,
        len(questions)
    )

    selected = random.sample(
        questions,
        count
    )

    quiz_sessions[chat_id] = {
        "subject": subject,
        "questions": selected,
        "current": 0,
        "quiz_score": 0,
        "answered": False
    }

    send_message(
        chat_id,
        "🚀 بدأ الاختبار!\n\n"
        f"📚 المادة: {subject}\n"
        f"📝 عدد الأسئلة: {count}\n\n"
        "ركز جيدًا، وكل إجابة صحيحة تقربك من النجمة القادمة ⭐"
    )

    send_question(
        chat_id
    )


# =========================================================
# إرسال السؤال
# =========================================================

def send_question(chat_id):

    session = quiz_sessions.get(
        chat_id
    )

    if not session:
        return

    current = session["current"]
    questions = session["questions"]

    if current >= len(questions):

        finish_quiz(
            chat_id
        )

        return

    question = questions[current]

    keyboard = []

    for index, option in enumerate(
        question["options"]
    ):

        keyboard.append([
            {
                "text":
                    f"{chr(65 + index)} - {option}",

                "callback_data":
                    f"answer:{index}"
            }
        ])

    text = (
        f"📝 {session['subject']}\n\n"
        f"السؤال {current + 1} "
        f"/ {len(questions)}\n\n"
        f"❓ {question['q']}\n\n"
        "اختر الإجابة:"
    )

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# معالجة الإجابة
# =========================================================

def handle_answer(
    callback
):

    callback_id = callback.get(
        "id"
    )

    answer_callback(
        callback_id
    )

    message = callback.get(
        "message",
        {}
    )

    chat_id = message.get(
        "chat",
        {}
    ).get(
        "id"
    )

    message_id = message.get(
        "message_id"
    )

    data = callback.get(
        "data",
        ""
    )

    session = quiz_sessions.get(
        chat_id
    )

    if not session:
        send_message(
            chat_id,
            "⚠️ انتهى الاختبار. ابدأ اختبارًا جديدًا."
        )
        return

    if session["answered"]:

        return

    if not data.startswith(
        "answer:"
    ):

        return

    try:

        selected = int(
            data.split(":")[1]
        )

    except Exception:

        return

    question = session["questions"][
        session["current"]
    ]

    correct_answer = question[
        "answer"
    ]

    session["answered"] = True

    if selected == correct_answer:

        session["quiz_score"] += 1

        update_student(
            chat_id,
            correct=True
        )

        student = get_student(
            chat_id
        )

        streak = student[
            "current_streak"
        ]

        result = (
            "✅ إجابة صحيحة! 🎉\n\n"
            f"🔥 سلسلة الإجابات الصحيحة: {streak}\n\n"
            f"💡 الشرح:\n"
            f"{question['explanation']}\n\n"
            f"{random.choice(MOTIVATION)}"
        )

    else:

        update_student(
            chat_id,
            correct=False
        )

        correct_text = question[
            "options"
        ][correct_answer]

        result = (
            "❌ ليست الإجابة الصحيحة.\n\n"
            f"✅ الإجابة الصحيحة: "
            f"{correct_text}\n\n"
            f"💡 الشرح:\n"
            f"{question['explanation']}\n\n"
            "💪 لا تقلق، الخطأ جزء من التعلم!"
        )

    check_star_upgrade(
        chat_id
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "➡️ السؤال التالي",
                    "callback_data":
                        "next_question"
                }
            ]
        ]
    }

    edit_message(
        chat_id,
        message_id,
        result,
        keyboard
    )


# =========================================================
# السؤال التالي
# =========================================================

def handle_next(
    chat_id
):

    session = quiz_sessions.get(
        chat_id
    )

    if not session:
        return

    if not session["answered"]:
        return

    session["current"] += 1

    session["answered"] = False

    send_question(
        chat_id
    )


# =========================================================
# إنهاء الاختبار
# =========================================================

def finish_quiz(
    chat_id
):

    session = quiz_sessions.get(
        chat_id
    )

    if not session:
        return

    total = len(
        session["questions"]
    )

    score = session[
        "quiz_score"
    ]

    percentage = round(
        (score / total) * 100
    ) if total else 0

    student = get_student(
        chat_id
    )

    stars = calculate_stars(
        student["correct"]
    )

    title = star_title(
        stars
    )

    if percentage == 100:

        comment = (
            "🏆 نتيجة كاملة! مذهل!"
        )

    elif percentage >= 80:

        comment = (
            "🔥 نتيجة ممتازة!"
        )

    elif percentage >= 60:

        comment = (
            "👏 جيد جدًا، واصل التدريب!"
        )

    elif percentage >= 50:

        comment = (
            "💪 بداية جيدة، يمكنك الوصول للأفضل!"
        )

    else:

        comment = (
            "🌱 لا تستسلم، راجع الأخطاء وأعد المحاولة!"
        )

    next_target, next_stars = next_star(
        student["correct"]
    )

    if next_target:

        remaining = (
            next_target -
            student["correct"]
        )

        progress = (
            f"🎯 تبقى لك {remaining} "
            f"إجابة صحيحة للوصول إلى "
            f"{'⭐' * next_stars}"
        )

    else:

        progress = (
            "👑 وصلت إلى أعلى رتبة!"
        )

    send_message(
        chat_id,
        f"🏁 انتهى الاختبار!\n\n"
        f"📚 {session['subject']}\n"
        f"✅ صحيح في هذا الاختبار: {score}/{total}\n"
        f"📊 النتيجة: {percentage}%\n\n"
        f"{comment}\n\n"
        f"🏆 إجمالي إجاباتك الصحيحة: "
        f"{student['correct']}\n"
        f"{title}\n\n"
        f"{progress}\n\n"
        "🚀 اختبر نفسك مرة أخرى لتصبح أقوى!"
    )

    del quiz_sessions[
        chat_id
    ]


# =========================================================
# الفلاسفة
# =========================================================

def philosophers(
    chat_id
):

    send_message(
        chat_id,
        "👨‍🏫 أهم الفلاسفة:\n\n"
        "🏛️ سقراط\n"
        "🏛️ أفلاطون\n"
        "🏛️ أرسطو\n"
        "🧠 ديكارت\n"
        "⚖️ كانط\n"
        "🔥 نيتشه\n"
        "📚 ابن رشد\n"
        "📖 ابن خلدون\n\n"
        "💡 لا تحفظ الاسم فقط؛ حاول فهم الفكرة والحجة."
    )


# =========================================================
# المفاهيم
# =========================================================

def philosophy_concepts(
    chat_id
):

    send_message(
        chat_id,
        "💡 مفاهيم فلسفية مهمة:\n\n"
        "🧠 الوعي\n"
        "🔓 الحرية\n"
        "⚖️ الأخلاق\n"
        "🔎 الحقيقة\n"
        "📚 المعرفة\n"
        "🏛️ الدولة\n"
        "🗣️ اللغة\n"
        "🎨 الفن\n"
        "🔬 العلم\n\n"
        "🎯 ركّز على المشكلة + المواقف + الحجج."
    )


# =========================================================
# الكلمات
# =========================================================

def important_words(
    chat_id,
    language
):

    words = {

        "الفرنسية":
            "🇫🇷 كلمات مهمة:\n\n"
            "Environnement = البيئة\n"
            "Société = المجتمع\n"
            "Éducation = التربية\n"
            "Liberté = الحرية\n"
            "Droit = الحق\n"
            "Problème = مشكلة\n"
            "Solution = حل",

        "الإنجليزية":
            "🇬🇧 كلمات مهمة:\n\n"
            "Environment = البيئة\n"
            "Society = المجتمع\n"
            "Education = التعليم\n"
            "Freedom = الحرية\n"
            "Rights = الحقوق\n"
            "Problem = مشكلة\n"
            "Solution = حل",

        "الإسبانية":
            "🇪🇸 كلمات مهمة:\n\n"
            "Educación = التعليم\n"
            "Sociedad = المجتمع\n"
            "Libertad = الحرية\n"
            "Problema = مشكلة\n"
            "Solución = حل\n"
            "Medio ambiente = البيئة"
    }

    send_message(
        chat_id,
        words.get(
            language,
            "❌ لا توجد كلمات حاليًا."
        )
    )


# =========================================================
# المستوى
# =========================================================

def show_stats(
    chat_id
):

    student = get_student(
        chat_id
    )

    correct = student[
        "correct"
    ]

    wrong = student[
        "wrong"
    ]

    total = student[
        "total"
    ]

    stars = calculate_stars(
        correct
    )

    title = star_title(
        stars
    )

    if total:

        accuracy = round(
            correct / total * 100
        )

    else:

        accuracy = 0

    next_target, next_stars = next_star(
        correct
    )

    if next_target:

        remaining = (
            next_target - correct
        )

        next_text = (
            f"⭐ الهدف القادم: "
            f"{'⭐' * next_stars}\n"
            f"بقيت {remaining} إجابة صحيحة"
        )

    else:

        next_text = (
            "👑 وصلت إلى أعلى مستوى!"
        )

    send_message(
        chat_id,
        f"📊 إحصائياتك\n\n"
        f"🏆 الرتبة: {title}\n\n"
        f"✅ صحيحة: {correct}\n"
        f"❌ خاطئة: {wrong}\n"
        f"📝 مجموع الأسئلة: {total}\n"
        f"🎯 الدقة: {accuracy}%\n"
        f"🔥 أفضل سلسلة: "
        f"{student['best_streak']}\n\n"
        f"{next_text}\n\n"
        "🚀 استمر، كل سؤال يرفع مستواك!"
    )


# =========================================================
# الإنجازات
# =========================================================

def achievements(
    chat_id
):

    student = get_student(
        chat_id
    )

    correct = student[
        "correct"
    ]

    stars = calculate_stars(
        correct
    )

    achievements_list = []

    if correct >= 1:
        achievements_list.append(
            "✅ أول إجابة صحيحة"
        )

    if correct >= 30:
        achievements_list.append(
            "⭐ طالب طموح"
        )

    if correct >= 60:
        achievements_list.append(
            "⭐⭐ طالب مجتهد"
        )

    if correct >= 100:
        achievements_list.append(
            "⭐⭐⭐ طالب متفوق"
        )

    if correct >= 150:
        achievements_list.append(
            "⭐⭐⭐⭐ طالب متميز"
        )

    if correct >= 200:
        achievements_list.append(
            "⭐⭐⭐⭐⭐ طالب قوي وذكي"
        )

    if student["best_streak"] >= 5:
        achievements_list.append(
            "🔥 سلسلة 5 إجابات صحيحة"
        )

    if student["best_streak"] >= 10:
        achievements_list.append(
            "⚡ سلسلة 10 إجابات صحيحة"
        )

    if not achievements_list:

        achievements_list.append(
            "🔒 ابدأ الاختبارات لفتح إنجازاتك."
        )

    send_message(
        chat_id,
        "🏆 إنجازاتك\n\n"
        + "\n".join(
            achievements_list
        )
        + f"\n\n⭐ مجموع النجوم: {stars}"
    )


# =========================================================
# مواضيع البكالوريا
# =========================================================

def bac_topics(
    chat_id
):

    send_message(
        chat_id,
        "📄 مواضيع البكالوريا\n\n"
        "اختر شعبتك:",
        bac_keyboard()
    )


# =========================================================
# Flask
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return "🎓 BacMind DZ is running!"


@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    # =====================================================
    # Callback
    # =====================================================

    callback = data.get(
        "callback_query"
    )

    if callback:

        callback_data = callback.get(
            "data",
            ""
        )

        message = callback.get(
            "message",
            {}
        )

        chat_id = message.get(
            "chat",
            {}
        ).get(
            "id"
        )

        if callback_data == "next_question":

            answer_callback(
                callback.get("id")
            )

            handle_next(
                chat_id
            )

        elif callback_data.startswith(
            "answer:"
        ):

            handle_answer(
                callback
            )

        return "OK"


    # =====================================================
    # Message
    # =====================================================

    message = data.get(
        "message",
        {}
    )

    chat_id = message.get(
        "chat",
        {}
    ).get(
        "id"
    )

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:

        return "OK"


    ensure_student(
        chat_id
    )


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        send_message(
            chat_id,
            "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"
            "🧠 منصة تدريب مخصصة لطلاب:\n"
            "📚 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n\n"
            "اختبر نفسك، تابع مستواك، واجمع النجوم ⭐\n\n"
            "🎯 هدفنا أن تدخل البكالوريا بثقة.\n\n"
            "🚀 مستعد للانطلاق؟",
            main_keyboard()
        )

        return "OK"


    # =====================================================
    # الفلسفة
    # =====================================================

    if text == "🧠 الفلسفة":

        send_message(
            chat_id,
            "🧠 قسم الفلسفة:",
            philosophy_keyboard()
        )

        return "OK"


    if text == "📝 اختبار فلسفة":

        start_quiz(
            chat_id,
            "الفلسفة"
        )

        return "OK"


    if text == "💡 مفاهيم فلسفية":

        philosophy_concepts(
            chat_id
        )

        return "OK"


    if text == "👨‍🏫 الفلاسفة":

        philosophers(
            chat_id
        )

        return "OK"


    # =====================================================
    # الفرنسية
    # =====================================================

    if text == "🇫🇷 الفرنسية":

        send_message(
            chat_id,
            "🇫🇷 قسم الفرنسية:",
            language_keyboard()
        )

        return "OK"


    # =====================================================
    # الإنجليزية
    # =====================================================

    if text == "🇬🇧 الإنجليزية":

        send_message(
            chat_id,
            "🇬🇧 قسم الإنجليزية:",
            language_keyboard()
        )

        return "OK"


    # =====================================================
    # الإسبانية
    # =====================================================

    if text == "🇪🇸 الإسبانية":

        send_message(
            chat_id,
            "🇪🇸 قسم الإسبانية:",
            language_keyboard()
        )

        return "OK"


    # =====================================================
    # اختبار اللغة
    # =====================================================

    if text == "📝 اختبار اللغة":

        # نستخدم آخر لغة اختارها الطالب.
        # الافتراضي: الفرنسية.

        # نحفظ اللغة مؤقتًا في الجلسة البسيطة.
        # إذا لم تكن موجودة نبدأ بالفرنسية.

        subject = "الفرنسية"

        # يمكن للطالب بدء اختبار اللغة من قسم الفرنسية
        # أو الإنجليزية أو الإسبانية.
        #
        # لتجنب فقدان الاختيار، نرسل له قائمة صغيرة.

        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🇫🇷 الفرنسية",
                        "callback_data": "language:الفرنسية"
                    }
                ],
                [
                    {
                        "text": "🇬🇧 الإنجليزية",
                        "callback_data": "language:الإنجليزية"
                    }
                ],
                [
                    {
                        "text": "🇪🇸 الإسبانية",
                        "callback_data": "language:الإسبانية"
                    }
                ]
            ]
        }

        send_message(
            chat_id,
            "🌍 اختر اللغة التي تريد اختبار نفسك فيها:",
            keyboard
        )

        return "OK"


    # =====================================================
    # الكلمات
    # =====================================================

    if text == "📚 كلمات مهمة":

        send_message(
            chat_id,
            "📚 اختر اللغة من القائمة الرئيسية أولًا، "
            "ثم اضغط كلمات مهمة."
        )

        return "OK"


    # =====================================================
    # مواضيع البكالوريا
    # =====================================================

    if text == "📄 مواضيع البكالوريا":

        bac_topics(
            chat_id
        )

        return "OK"


    if text == "📚 آداب وفلسفة":

        send_message(
            chat_id,
            "📚 آداب وفلسفة\n\n"
            "سيتم تخصيص هذا القسم لاحقًا "
            "للمواضيع حسب السنوات والمواد."
        )

        return "OK"


    if text == "🌍 لغات أجنبية":

        send_message(
            chat_id,
            "🌍 لغات أجنبية\n\n"
            "سيتم تخصيص هذا القسم لاحقًا "
            "للمواضيع حسب السنوات واللغات."
        )

        return "OK"


    # =====================================================
    # المستوى
    # =====================================================

    if text == "📊 مستواي":

        show_stats(
            chat_id
        )

        return "OK"


    # =====================================================
    # الإنجازات
    # =====================================================

    if text == "🏆 الإنجازات":

        achievements(
            chat_id
        )

        return "OK"


    # =====================================================
    # المساعدة
    # =====================================================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة استخدام BacMind DZ:\n\n"
            "1️⃣ اختر المادة.\n"
            "2️⃣ ابدأ الاختبار.\n"
            "3️⃣ أجب عن الأسئلة.\n"
            "4️⃣ اقرأ الشرح بعد كل إجابة.\n"
            "5️⃣ تابع إحصائياتك.\n"
            "6️⃣ اجمع النجوم ⭐.\n\n"
            "🎯 30 إجابة صحيحة = ⭐\n"
            "🎯 60 = ⭐⭐\n"
            "🎯 100 = ⭐⭐⭐\n"
            "🎯 150 = ⭐⭐⭐⭐\n"
            "🎯 200 = ⭐⭐⭐⭐⭐\n\n"
            "🔥 استمر حتى تصل إلى القمة!"
        )

        return "OK"


    # =====================================================
    # العودة
    # =====================================================

    if text == "🔙 القائمة الرئيسية":

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_keyboard()
        )

        return "OK"


    # =====================================================
    # رسالة افتراضية
    # =====================================================

    send_message(
        chat_id,
        "🤔 لم أفهم الأمر.\n\n"
        "اضغط /start لفتح القائمة الرئيسية."
    )

    return "OK"


# =========================================================
# تشغيل التطبيق
# =========================================================

init_db()


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
