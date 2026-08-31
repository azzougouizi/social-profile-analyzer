import os
import requests
from flask import Flask, request

from questions import QUESTIONS, get_random_questions


app = Flask(__name__)


# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود في Environment Variables")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)


# =========================================================
# بيانات المستخدمين
# =========================================================

users = {}


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
            f"Telegram {method}: HTTP {response.status_code}"
        )

        if response.status_code != 200:
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


def send_message(chat_id, text, keyboard=None):

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
# إنشاء / تحديث بيانات المستخدم
# =========================================================

def get_user(chat_id):

    if chat_id not in users:

        users[chat_id] = {
            "step": "main",
            "language": None,
            "subject": None,
            "questions": [],
            "current": 0,
            "score": 0,
            "streak": 0,
            "best_streak": 0,
            "answered": False,
            "total_answered": 0,
            "correct_answers": 0,
            "last_percentage": 0,
            "last_score": 0,
            "last_total": 0
        }

    return users[chat_id]


# =========================================================
# بدء اختبار
# =========================================================

def start_quiz(chat_id, subject):

    user = get_user(chat_id)

    questions = get_random_questions(
        subject,
        10
    )

    if not questions:

        send_message(
            chat_id,
            f"❌ لا توجد أسئلة في مادة {subject} حاليًا."
        )

        return

    user["step"] = "quiz"
    user["subject"] = subject
    user["questions"] = questions
    user["current"] = 0
    user["score"] = 0
    user["streak"] = 0
    user["best_streak"] = 0
    user["answered"] = False

    send_message(
        chat_id,
        f"🚀 بدأ اختبار {subject}!\n\n"
        f"عدد الأسئلة: {len(questions)}\n\n"
        "ركز جيدًا واختر الإجابة الصحيحة.",
    )

    send_question(chat_id)


# =========================================================
# إرسال السؤال
# =========================================================

def send_question(chat_id):

    user = get_user(chat_id)

    questions = user.get(
        "questions",
        []
    )

    index = user.get(
        "current",
        0
    )

    if index >= len(questions):

        finish_quiz(chat_id)

        return

    question = questions[index]

    keyboard = []

    for i, option in enumerate(
        question.get("options", [])
    ):

        keyboard.append([
            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"quiz_{i}"
            }
        ])

    keyboard.append([
        {
            "text": "🏠 القائمة الرئيسية",
            "callback_data": "main"
        }
    ])

    send_message(
        chat_id,

        f"📚 المادة: {user['subject']}\n"
        f"📝 السؤال {index + 1} / {len(questions)}\n\n"
        f"❓ {question.get('q', '')}\n\n"
        "اختر الإجابة:",

        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# معالجة الإجابة
# =========================================================

def handle_quiz_answer(callback):

    callback_id = callback.get("id")

    answer_callback(callback_id)

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

    chat_id = chat.get("id")

    message_id = message.get(
        "message_id"
    )

    if not chat_id:
        return

    user = get_user(chat_id)

    if user.get("step") != "quiz":
        return

    if user.get("answered"):
        return

    if not data.startswith("quiz_"):
        return

    try:

        selected = int(
            data.replace(
                "quiz_",
                ""
            )
        )

    except ValueError:

        return

    questions = user.get(
        "questions",
        []
    )

    index = user.get(
        "current",
        0
    )

    if index >= len(questions):
        return

    question = questions[index]

    correct = question.get(
        "answer"
    )

    options = question.get(
        "options",
        []
    )

    if not isinstance(correct, int):
        return

    if selected < 0 or selected >= len(options):
        return

    user["answered"] = True

    user["total_answered"] += 1

    if selected == correct:

        user["score"] += 1
        user["correct_answers"] += 1
        user["streak"] += 1

        if user["streak"] > user["best_streak"]:

            user["best_streak"] = user["streak"]

        result = (
            "✅ إجابة صحيحة!\n\n"
            f"🔥 السلسلة الحالية: "
            f"{user['streak']}"
        )

    else:

        user["streak"] = 0

        correct_text = options[correct]

        result = (
            "❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة:\n"
            f"{correct_text}"
        )

    explanation = question.get(
        "explanation",
        ""
    )

    if explanation:

        result += (
            "\n\n"
            "💡 الشرح:\n"
            f"{explanation}"
        )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "➡️ السؤال التالي",
                    "callback_data": "next"
                }
            ],
            [
                {
                    "text": "🏠 القائمة الرئيسية",
                    "callback_data": "main"
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

def handle_next(chat_id):

    user = get_user(chat_id)

    if user.get("step") != "quiz":
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


# =========================================================
# إنهاء الاختبار
# =========================================================

def finish_quiz(chat_id):

    user = get_user(chat_id)

    questions = user.get(
        "questions",
        []
    )

    total = len(questions)
    score = user.get(
        "score",
        0
    )

    if total == 0:
        return

    percentage = round(
        score / total * 100
    )

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage
    user["step"] = "main"

    if percentage >= 90:

        level = "🏆 أسطوري"

    elif percentage >= 75:

        level = "🔥 ممتاز"

    elif percentage >= 60:

        level = "👏 جيد جدًا"

    elif percentage >= 50:

        level = "👍 مقبول"

    else:

        level = "💪 تحتاج إلى مراجعة"

    send_message(
        chat_id,

        "🎉 انتهى الاختبار!\n\n"

        f"📚 المادة: {user['subject']}\n"
        f"✅ الصحيح: {score}\n"
        f"❌ الخطأ: {total - score}\n"
        f"📊 النتيجة: {percentage}%\n"
        f"🏅 المستوى: {level}\n"
        f"🔥 أفضل سلسلة: "
        f"{user['best_streak']}\n\n"

        "💪 لا تتوقف!\n"
        "كل سؤال تخطئ فيه اليوم هو فرصة "
        "لتصبح أقوى غدًا.",

        main_keyboard()
    )


# =========================================================
# الفلاسفة
# =========================================================

def philosophers(chat_id):

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

        "💡 نصيحة:\n"
        "لا تحفظ اسم الفيلسوف فقط، "
        "بل اربطه بالموقف والحجة والمفهوم."
    )


# =========================================================
# المفاهيم الفلسفية
# =========================================================

def philosophy_concepts(chat_id):

    send_message(
        chat_id,

        "💡 مفاهيم مهمة للبكالوريا:\n\n"

        "🧠 الوعي\n"
        "🔓 الحرية\n"
        "⚖️ الأخلاق\n"
        "🔎 الحقيقة\n"
        "📚 المعرفة\n"
        "🏛️ الدولة\n"
        "🗣️ اللغة\n"
        "🎨 الفن\n"
        "🔬 العلم\n\n"

        "🎯 عند مراجعة أي مفهوم حاول دراسة:\n"
        "1️⃣ التعريف\n"
        "2️⃣ المشكلة\n"
        "3️⃣ المواقف\n"
        "4️⃣ الحجج\n"
        "5️⃣ النقد\n"
        "6️⃣ التركيب"
    )


# =========================================================
# الكلمات
# =========================================================

def important_words(chat_id, language):

    words = {

        "الفرنسية":
            "🇫🇷 كلمات فرنسية مهمة:\n\n"
            "Environnement = البيئة\n"
            "Société = المجتمع\n"
            "Éducation = التعليم\n"
            "Liberté = الحرية\n"
            "Droit = الحق\n"
            "Problème = مشكلة\n"
            "Solution = حل",

        "الإنجليزية":
            "🇬🇧 كلمات إنجليزية مهمة:\n\n"
            "Environment = البيئة\n"
            "Society = المجتمع\n"
            "Education = التعليم\n"
            "Freedom = الحرية\n"
            "Rights = الحقوق\n"
            "Problem = مشكلة\n"
            "Solution = حل",

        "الإسبانية":
            "🇪🇸 كلمات إسبانية مهمة:\n\n"
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
# الإحصائيات
# =========================================================

def show_stats(chat_id):

    user = get_user(chat_id)

    total_answered = user.get(
        "total_answered",
        0
    )

    correct = user.get(
        "correct_answers",
        0
    )

    if total_answered == 0:

        send_message(
            chat_id,

            "📊 مستواك\n\n"
            "لم تجب عن أي سؤال بعد.\n\n"
            "🚀 ابدأ أول اختبار حتى يبدأ "
            "البوت في حساب تقدمك."
        )

        return

    accuracy = round(
        correct / total_answered * 100
    )

    send_message(
        chat_id,

        "📊 إحصائياتك\n\n"

        f"📝 الأسئلة المجاب عنها: "
        f"{total_answered}\n"

        f"✅ الإجابات الصحيحة: "
        f"{correct}\n"

        f"🎯 نسبة النجاح: "
        f"{accuracy}%\n"

        f"🔥 أفضل سلسلة: "
        f"{user.get('best_streak', 0)}\n\n"

        f"📚 آخر اختبار: "
        f"{user.get('last_percentage', 0)}%\n\n"

        "💪 استمر، مستواك يتحسن مع كل سؤال!"
    )


# =========================================================
# الإنجازات
# =========================================================

def achievements(chat_id):

    user = get_user(chat_id)

    total = user.get(
        "total_answered",
        0
    )

    correct = user.get(
        "correct_answers",
        0
    )

    streak = user.get(
        "best_streak",
        0
    )

    badges = []

    if total >= 10:
        badges.append("🥉 بدأ طريق النجاح — 10 أسئلة")

    if total >= 30:
        badges.append("🌟 طالب طموح — 30 سؤال")

    if total >= 60:
        badges.append("⭐⭐ طالب مجتهد — 60 سؤال")

    if total >= 100:
        badges.append("⭐⭐⭐ طالب متميز — 100 سؤال")

    if total >= 150:
        badges.append("⭐⭐⭐⭐ طالب قوي — 150 سؤال")

    if total >= 200:
        badges.append("⭐⭐⭐⭐⭐ طالب قوي وذكي — 200 سؤال")

    if streak >= 5:
        badges.append("🔥 سلسلة 5 إجابات صحيحة")

    if streak >= 10:
        badges.append("🚀 سلسلة 10 إجابات صحيحة")

    if not badges:

        badges.append(
            "🔒 لم تحصل على شارة بعد.\n"
            "أجب عن المزيد من الأسئلة لفتح الإنجازات."
        )

    send_message(
        chat_id,

        "🏆 إنجازاتك\n\n"
        + "\n".join(badges)
        + "\n\n"
        f"📝 مجموع الأسئلة: {total}\n"
        f"✅ الصحيح: {correct}"
    )


# =========================================================
# مواضيع البكالوريا
# =========================================================

def bac_topics(chat_id):

    send_message(
        chat_id,

        "📄 مواضيع البكالوريا\n\n"
        "اختر شعبتك:",

        bac_keyboard()
    )


# =========================================================
# المساعدة
# =========================================================

def help_message(chat_id):

    send_message(
        chat_id,

        "ℹ️ كيف تستخدم BacMind DZ؟\n\n"

        "1️⃣ اختر المادة.\n"
        "2️⃣ ابدأ الاختبار.\n"
        "3️⃣ اختر إجابتك.\n"
        "4️⃣ اقرأ الشرح.\n"
        "5️⃣ انتقل للسؤال التالي.\n"
        "6️⃣ راقب مستواك وإنجازاتك.\n\n"

        "🎯 هدفك ليس الإجابة الصحيحة فقط.\n"
        "هدفك أن تفهم لماذا كانت الإجابة صحيحة.\n\n"

        "🔥 كل سؤال يقربك خطوة من البكالوريا."
    )


# =========================================================
# Flask
# =========================================================

@app.route("/", methods=["GET"])
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
    # Callback Query
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

        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        if not chat_id:
            return "OK"

        if callback_data == "next":

            answer_callback(
                callback.get("id")
            )

            handle_next(
                chat_id
            )

        elif callback_data == "main":

            answer_callback(
                callback.get("id")
            )

            user = get_user(chat_id)

            user["step"] = "main"

            send_message(
                chat_id,
                "🏠 القائمة الرئيسية:",
                main_keyboard()
            )

        elif callback_data.startswith("quiz_"):

            handle_quiz_answer(
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

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:
        return "OK"


    user = get_user(chat_id)


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        users[chat_id] = {
            "step": "main",
            "language": None,
            "subject": None,
            "questions": [],
            "current": 0,
            "score": 0,
            "streak": 0,
            "best_streak": 0,
            "answered": False,
            "total_answered": 0,
            "correct_answers": 0,
            "last_percentage": 0,
            "last_score": 0,
            "last_total": 0
        }

        send_message(
            chat_id,

            "🎓 أهلاً بك في BacMind DZ 🇩🇿\n\n"

            "🧠 البوت المخصص لطلاب:\n"
            "📚 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n\n"

            "🚀 اختبر نفسك.\n"
            "💡 افهم أخطاءك.\n"
            "🏆 اجمع إنجازاتك.\n"
            "🔥 وطوّر مستواك يومًا بعد يوم.",

            main_keyboard()
        )

        return "OK"


    # =====================================================
    # الفلسفة
    # =====================================================

    if text == "🧠 الفلسفة":

        user["step"] = "philosophy"

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

        user["language"] = "الفرنسية"
        user["step"] = "language"

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

        user["language"] = "الإنجليزية"
        user["step"] = "language"

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

        user["language"] = "الإسبانية"
        user["step"] = "language"

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

        language = user.get(
            "language"
        )

        if language not in QUESTIONS:

            send_message(
                chat_id,
                "❌ اختر اللغة أولاً من القائمة الرئيسية."
            )

            return "OK"

        start_quiz(
            chat_id,
            language
        )

        return "OK"


    # =====================================================
    # الكلمات
    # =====================================================

    if text == "📚 كلمات مهمة":

        language = user.get(
            "language"
        )

        if not language:

            send_message(
                chat_id,
                "❌ اختر اللغة أولاً."
            )

            return "OK"

        important_words(
            chat_id,
            language
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

            "📚 شعبة آداب وفلسفة\n\n"

            "📄 قسم المواضيع سيتم ربطه لاحقًا "
            "بقاعدة مواضيع البكالوريا حسب السنة والمادة."
        )

        return "OK"


    if text == "🌍 لغات أجنبية":

        send_message(
            chat_id,

            "🌍 شعبة لغات أجنبية\n\n"

            "📄 قسم المواضيع سيتم ربطه لاحقًا "
            "بقاعدة مواضيع البكالوريا حسب السنة واللغة."
        )

        return "OK"


    # =====================================================
    # الإحصائيات
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

        help_message(
            chat_id
        )

        return "OK"


    # =====================================================
    # القائمة الرئيسية
    # =====================================================

    if text == "🔙 القائمة الرئيسية":

        user["step"] = "main"

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
        "❓ لم أفهم الأمر.\n\n"
        "اضغط /start لفتح القائمة الرئيسية."
    )

    return "OK"


# =========================================================
# تشغيل التطبيق
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
