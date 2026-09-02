import os
import json
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# ⚙️ إعدادات البوت
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

DATA_FILE = "data.json"


# =========================================================
# 🔐 أكواد تفعيل الطلاب
#
# أضف أكواد الطلاب هنا
#
# False = الكود لم يُستعمل
# =========================================================

ACTIVATION_CODES = {

    "BAC-DZ-A1": False,
    "BAC-DZ-B2": False,
    "BAC-DZ-C3": False,
    "BAC-DZ-D4": False,
    "BAC-DZ-E5": False,
    "AzzouGouizi":False,

    # يمكنك إضافة المزيد:
    # "AHMED2026": False,
    # "STUDENT001": False,
}


# =========================================================
# 💾 تحميل وحفظ البيانات
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):

        return {
            "users": {},
            "codes": ACTIVATION_CODES.copy()
        }

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as file:

            data = json.load(file)

            # إضافة الأكواد الجديدة الموجودة في bot.py
            for code, used in ACTIVATION_CODES.items():

                if code not in data["codes"]:

                    data["codes"][code] = used

            return data

    except Exception:

        return {
            "users": {},
            "codes": ACTIVATION_CODES.copy()
        }


database = load_data()


def save_data():

    try:

        with open(DATA_FILE, "w", encoding="utf-8") as file:

            json.dump(
                database,
                file,
                ensure_ascii=False,
                indent=4
            )

    except Exception as error:

        print("Save Error:", error)


save_data()


# =========================================================
# 📚 بنك الأسئلة
# شعبة آداب وفلسفة
# =========================================================

QUESTIONS = {

    # -----------------------------------------------------
    # 🧠 الفلسفة
    # -----------------------------------------------------

    "🧠 الفلسفة": [

        {
            "q": "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            "options": ["أفلاطون", "ديكارت", "أرسطو", "كانط"],
            "answer": 1
        },

        {
            "q": "من صاحب نظرية المثل؟",
            "options": ["أفلاطون", "ديكارت", "نيتشه", "كانط"],
            "answer": 0
        },

        {
            "q": "ما المقصود بالمنطق؟",
            "options": [
                "علم التفكير الصحيح",
                "علم التاريخ",
                "علم الاقتصاد",
                "علم الجغرافيا"
            ],
            "answer": 0
        },

        {
            "q": "من الفيلسوف المرتبط بالشك المنهجي؟",
            "options": [
                "أرسطو",
                "ديكارت",
                "سقراط",
                "هيغل"
            ],
            "answer": 1
        },

        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": [
                "أفلاطون",
                "كانط",
                "ديكارت",
                "سقراط"
            ],
            "answer": 0
        },

        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": [
                "سقراط",
                "أرسطو",
                "كانط",
                "ماركس"
            ],
            "answer": 1
        },

        {
            "q": "الفلسفة تعني أساسًا:",
            "options": [
                "حب الحكمة",
                "حفظ المعلومات",
                "دراسة الرياضة",
                "دراسة النباتات"
            ],
            "answer": 0
        },

        {
            "q": "من ربط الأخلاق بالواجب؟",
            "options": [
                "كانط",
                "نيتشه",
                "أفلاطون",
                "ماركس"
            ],
            "answer": 0
        },

        {
            "q": "الحقيقة في التصور الكلاسيكي تعني:",
            "options": [
                "مطابقة الفكر للواقع",
                "الرأي الشخصي",
                "الخيال",
                "الإشاعة"
            ],
            "answer": 0
        },

        {
            "q": "ما الهدف من التفكير النقدي؟",
            "options": [
                "تحليل الأفكار والأدلة",
                "رفض كل شيء",
                "الحفظ فقط",
                "عدم السؤال"
            ],
            "answer": 0
        }
    ],


    # -----------------------------------------------------
    # 🇩🇿 اللغة العربية
    # -----------------------------------------------------

    "🇩🇿 اللغة العربية": [

        {
            "q": "ما نوع كلمة «كتب»؟",
            "options": [
                "فعل ماضٍ",
                "اسم",
                "حرف",
                "فعل أمر"
            ],
            "answer": 0
        },

        {
            "q": "جمع كلمة «كتاب» هو:",
            "options": [
                "كتب",
                "كاتبات",
                "كتابان",
                "مكتوب"
            ],
            "answer": 0
        },

        {
            "q": "الفاعل يكون غالبًا:",
            "options": [
                "مرفوعًا",
                "منصوبًا",
                "مجرورًا",
                "مجزومًا"
            ],
            "answer": 0
        },

        {
            "q": "ما ضد كلمة النجاح؟",
            "options": [
                "الفشل",
                "التفوق",
                "العلم",
                "العمل"
            ],
            "answer": 0
        },

        {
            "q": "الجملة الاسمية تبدأ بـ:",
            "options": [
                "اسم",
                "فعل",
                "حرف",
                "فعل أمر"
            ],
            "answer": 0
        },

        {
            "q": "المبتدأ يكون:",
            "options": [
                "مرفوعًا",
                "منصوبًا",
                "مجرورًا",
                "مجزومًا"
            ],
            "answer": 0
        },

        {
            "q": "الفعل المضارع يدل غالبًا على:",
            "options": [
                "الحاضر أو المستقبل",
                "الماضي فقط",
                "الأمر فقط",
                "الاسم"
            ],
            "answer": 0
        },

        {
            "q": "ما نوع كلمة «في»؟",
            "options": [
                "حرف جر",
                "اسم",
                "فعل",
                "صفة"
            ],
            "answer": 0
        },

        {
            "q": "ما المقصود بالبلاغة؟",
            "options": [
                "حسن التعبير والتأثير",
                "الحساب",
                "الجغرافيا",
                "الرياضة"
            ],
            "answer": 0
        },

        {
            "q": "الخبر في الجملة الاسمية يكون غالبًا:",
            "options": [
                "مرفوعًا",
                "مجزومًا",
                "مجرورًا دائمًا",
                "فعل أمر"
            ],
            "answer": 0
        }
    ],


    # -----------------------------------------------------
    # 🇫🇷 الفرنسية
    # -----------------------------------------------------

    "🇫🇷 الفرنسية": [

        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": [
                "triste",
                "content",
                "fatigué",
                "malade"
            ],
            "answer": 1
        },

        {
            "q": "Complétez : Je ___ au lycée.",
            "options": [
                "vais",
                "va",
                "allez",
                "allons"
            ],
            "answer": 0
        },

        {
            "q": "Le contraire de « difficile » est :",
            "options": [
                "facile",
                "long",
                "fort",
                "ancien"
            ],
            "answer": 0
        },

        {
            "q": "Le pluriel de « cheval » est :",
            "options": [
                "chevaux",
                "chevals",
                "chevales",
                "chevaus"
            ],
            "answer": 0
        },

        {
            "q": "« J'ai étudié » est au :",
            "options": [
                "passé composé",
                "présent",
                "futur",
                "imparfait"
            ],
            "answer": 0
        },

        {
            "q": "Complétez : Nous ___ nos devoirs.",
            "options": [
                "faisons",
                "fait",
                "faites",
                "faire"
            ],
            "answer": 0
        },

        {
            "q": "Quel mot est un adjectif ?",
            "options": [
                "intelligent",
                "courir",
                "maison",
                "rapidement"
            ],
            "answer": 0
        },

        {
            "q": "Le féminin de « acteur » est :",
            "options": [
                "actrice",
                "acteuse",
                "acteur",
                "acteurs"
            ],
            "answer": 0
        },

        {
            "q": "Le contraire de « ancien » est :",
            "options": [
                "moderne",
                "vieux",
                "historique",
                "passé"
            ],
            "answer": 0
        },

        {
            "q": "« Merci » signifie :",
            "options": [
                "شكرا",
                "مرحبا",
                "وداعًا",
                "نعم"
            ],
            "answer": 0
        }
    ],


    # -----------------------------------------------------
    # 🇬🇧 الإنجليزية
    # -----------------------------------------------------

    "🇬🇧 الإنجليزية": [

        {
            "q": "She ___ English every day.",
            "options": [
                "studies",
                "study",
                "studying",
                "studied"
            ],
            "answer": 0
        },

        {
            "q": "What is the past tense of go?",
            "options": [
                "went",
                "goed",
                "gone",
                "going"
            ],
            "answer": 0
        },

        {
            "q": "Choose: I ___ a student.",
            "options": [
                "am",
                "is",
                "are",
                "be"
            ],
            "answer": 0
        },

        {
            "q": "What is the opposite of easy?",
            "options": [
                "hard",
                "simple",
                "small",
                "short"
            ],
            "answer": 0
        },

        {
            "q": "They ___ playing now.",
            "options": [
                "are",
                "is",
                "am",
                "be"
            ],
            "answer": 0
        },

        {
            "q": "What does environment mean?",
            "options": [
                "البيئة",
                "الرياضة",
                "التاريخ",
                "الاقتصاد"
            ],
            "answer": 0
        },

        {
            "q": "I have lived here ___ 2020.",
            "options": [
                "since",
                "for",
                "at",
                "on"
            ],
            "answer": 0
        },

        {
            "q": "The comparative of good is:",
            "options": [
                "better",
                "gooder",
                "best",
                "more good"
            ],
            "answer": 0
        },

        {
            "q": "Choose the correct sentence:",
            "options": [
                "He doesn't like football.",
                "He don't like football.",
                "He doesn't likes football.",
                "He not like football."
            ],
            "answer": 0
        },

        {
            "q": "The past participle of write is:",
            "options": [
                "written",
                "wrote",
                "writes",
                "writing"
            ],
            "answer": 0
        }
    ]
}


# =========================================================
# 📱 Telegram Functions
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

        return response.json()

    except Exception as error:

        print("Telegram Error:", error)

        return None


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def edit_message(chat_id, message_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = keyboard

    return telegram("editMessageText", data)


def answer_callback(callback_id):

    telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# 🎓 قائمة اختيار الشعبة
# =========================================================

def branch_keyboard():

    return {

        "keyboard": [

            ["🧠 آداب وفلسفة"]

        ],

        "resize_keyboard": True
    }


# =========================================================
# 📚 قائمة المواد
# =========================================================

def subjects_keyboard(chat_id):

    user = database["users"].get(
        str(chat_id),
        {}
    )

    completed = user.get(
        "completed_subjects",
        {}
    )

    buttons = []

    for subject in QUESTIONS:

        if subject in completed:

            buttons.append([
                f"✅ {subject}"
            ])

        else:

            buttons.append([
                subject
            ])

    # يظهر زر المعدل بعد إنهاء جميع المواد
    if len(completed) == len(QUESTIONS):

        buttons.append([
            "📊 أظهر لي معدلي"
        ])

    buttons.append([
        "🔄 إعادة الاختبارات"
    ])

    return {

        "keyboard": buttons,

        "resize_keyboard": True
    }


# =========================================================
# 🔐 تفعيل الحساب
# =========================================================

def activate_account(chat_id, code):

    code = code.strip().upper()

    user_id = str(chat_id)

    codes = database["codes"]

    # الكود غير موجود
    if code not in codes:

        send_message(
            chat_id,
            "❌ كود التفعيل غير صحيح.\n\n"
            "🔐 حاول مرة أخرى."
        )

        return

    # الكود مستعمل
    if codes[code]:

        send_message(
            chat_id,
            "❌ هذا الكود تم استعماله مسبقًا."
        )

        return

    # تفعيل الكود
    codes[code] = True

    database["users"][user_id] = {

        "activated": True,

        "activation_code": code,

        "branch": None,

        "completed_subjects": {}
    }

    save_data()

    send_message(
        chat_id,
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ تم تفعيل حسابك بنجاح!\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"
        "📝 أجب عن 10 أسئلة في كل مادة.\n"
        "📊 وبعدها اكتشف معدلك.\n\n"
        "👇 اختر شعبتك:",
        branch_keyboard()
    )


# =========================================================
# 📝 بدء اختبار مادة
# =========================================================

def start_subject(chat_id, subject):

    user = database["users"][str(chat_id)]

    completed = user.get(
        "completed_subjects",
        {}
    )

    if subject in completed:

        send_message(
            chat_id,
            "✅ لقد أكملت هذه المادة بالفعل."
        )

        return

    selected = random.sample(
        QUESTIONS[subject],
        min(10, len(QUESTIONS[subject]))
    )

    user["quiz"] = {

        "subject": subject,

        "questions": selected,

        "current": 0,

        "score": 0
    }

    save_data()

    send_question(chat_id)


# =========================================================
# ❓ إرسال السؤال
# =========================================================

def send_question(chat_id):

    user = database["users"][str(chat_id)]

    quiz = user.get("quiz")

    if not quiz:

        return

    index = quiz["current"]

    if index >= len(quiz["questions"]):

        finish_subject(chat_id)

        return

    question = quiz["questions"][index]

    keyboard = []

    for i, option in enumerate(question["options"]):

        keyboard.append([

            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"answer_{i}"
            }

        ])

    send_message(
        chat_id,
        f"🎓 {quiz['subject']}\n\n"
        f"📝 السؤال {index + 1}/10\n\n"
        f"❓ {question['q']}",

        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# ✅ معالجة الإجابة
# =========================================================

def handle_answer(callback):

    chat_id = callback["message"]["chat"]["id"]

    answer_callback(callback["id"])

    user = database["users"].get(
        str(chat_id)
    )

    if not user:

        return

    quiz = user.get("quiz")

    if not quiz:

        return

    selected = int(
        callback["data"].replace(
            "answer_",
            ""
        )
    )

    question = quiz["questions"][
        quiz["current"]
    ]

    correct = question["answer"]

    if selected == correct:

        quiz["score"] += 1

        result = "✅ إجابة صحيحة! 🎉"

    else:

        result = (
            "❌ إجابة خاطئة!\n\n"
            "✅ الإجابة الصحيحة:\n"
            f"{question['options'][correct]}"
        )

    quiz["current"] += 1

    save_data()

    keyboard = {

        "inline_keyboard": [

            [

                {
                    "text": "➡️ السؤال التالي",
                    "callback_data": "next"
                }

            ]

        ]

    }

    edit_message(
        chat_id,

        callback["message"]["message_id"],

        result,

        keyboard
    )


# =========================================================
# ➡️ السؤال التالي
# =========================================================

def next_question(callback):

    chat_id = callback["message"]["chat"]["id"]

    answer_callback(callback["id"])

    send_question(chat_id)


# =========================================================
# 🎉 إنهاء اختبار المادة
# =========================================================

def finish_subject(chat_id):

    user = database["users"][str(chat_id)]

    quiz = user["quiz"]

    subject = quiz["subject"]

    score = quiz["score"]

    # كل إجابة صحيحة = نقطتان
    grade = score * 2

    user.setdefault(
        "completed_subjects",
        {}
    )

    user["completed_subjects"][subject] = grade

    user.pop("quiz", None)

    save_data()

    send_message(
        chat_id,
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎉 انتهيت من {subject}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ الصحيح: {score}/10\n"
        f"📊 معدلك: {grade}/20\n\n"
        "📚 اختر المادة التالية 👇",

        subjects_keyboard(chat_id)
    )


# =========================================================
# 📊 إظهار المعدل
# =========================================================

def show_average(chat_id):

    user = database["users"].get(
        str(chat_id)
    )

    if not user:

        return

    completed = user.get(
        "completed_subjects",
        {}
    )

    if len(completed) < len(QUESTIONS):

        remaining = (
            len(QUESTIONS)
            - len(completed)
        )

        send_message(
            chat_id,
            f"⚠️ لم تكمل جميع المواد.\n\n"
            f"📚 بقيت لك {remaining} مادة."
        )

        return

    grades = list(
        completed.values()
    )

    average = (
        sum(grades)
        / len(grades)
    )

    percentage = round(
        average / 20 * 100,
        1
    )

    if average >= 16:

        level = "🏆 ممتاز جدًا"

    elif average >= 14:

        level = "🔥 جيد جدًا"

    elif average >= 10:

        level = "✅ ناجح"

    else:

        level = "💪 تحتاج إلى تدريب أكثر"

    result = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🎓 نتيجتك الدراسية\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for subject, grade in completed.items():

        result += (
            f"{subject}: "
            f"{grade}/20\n"
        )

    result += (
        "\n━━━━━━━━━━━━━━━━━━\n\n"

        f"📊 معدلك العام: "
        f"{average:.2f}/20\n"

        f"📈 نسبة النجاح: "
        f"{percentage}%\n"

        f"🏆 تقييمك: "
        f"{level}\n\n"

        "🚀 استمر في التدريب والتطور!"
    )

    send_message(
        chat_id,
        result
    )


# =========================================================
# 🔄 إعادة الاختبارات
# =========================================================

def reset_tests(chat_id):

    user = database["users"].get(
        str(chat_id)
    )

    if not user:

        return

    user["completed_subjects"] = {}

    user.pop("quiz", None)

    save_data()

    send_message(
        chat_id,
        "🔄 تم إعادة جميع الاختبارات!\n\n"
        "🎓 يمكنك البدء من جديد.",

        subjects_keyboard(chat_id)
    )


# =========================================================
# 🌐 Flask
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "🎓 BacMind DZ يعمل بنجاح!"


@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    data = request.get_json(
        silent=True
    ) or {}


    # =====================================================
    # Inline Buttons
    # =====================================================

    callback = data.get("callback_query")

    if callback:

        callback_data = callback.get(
            "data",
            ""
        )

        if callback_data.startswith("answer_"):

            handle_answer(callback)

        elif callback_data == "next":

            next_question(callback)

        return "OK"


    # =====================================================
    # Messages
    # =====================================================

    message = data.get("message", {})

    chat_id = message.get(
        "chat",
        {}
    ).get("id")

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:

        return "OK"


    user_id = str(chat_id)


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        # إذا كان الحساب مفعلًا
        if (
            user_id in database["users"]
            and database["users"][user_id].get(
                "activated"
            )
        ):

            user = database["users"][user_id]

            if user.get("branch"):

                send_message(
                    chat_id,
                    "🎓 مرحبًا بعودتك!\n\n"
                    "📚 اختر المادة التي تريدها:",
                    subjects_keyboard(chat_id)
                )

            else:

                send_message(
                    chat_id,
                    "🎓 مرحبًا بعودتك!\n\n"
                    "👇 اختر شعبتك:",
                    branch_keyboard()
                )

        # حساب جديد
        else:

            send_message(
                chat_id,
                "━━━━━━━━━━━━━━━━━━\n"
                "🔐 مرحبًا بك في BacMind DZ\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "للدخول إلى المنصة أرسل:\n\n"
                "🔑 كود التفعيل الخاص بك"
            )

        return "OK"


    # =====================================================
    # 🔐 التحقق من الحساب
    # =====================================================

    if (
        user_id not in database["users"]
        or not database["users"][user_id].get(
            "activated"
        )
    ):

        activate_account(
            chat_id,
            text
        )

        return "OK"


    # =====================================================
    # 🎓 اختيار الشعبة
    # =====================================================

    if text == "🧠 آداب وفلسفة":

        database["users"][user_id][
            "branch"
        ] = "آداب وفلسفة"

        save_data()

        send_message(
            chat_id,
            "🎓 تم اختيار شعبة آداب وفلسفة!\n\n"
            "📚 اختر المادة التي تريد اختبار نفسك فيها:\n\n"
            "📝 كل مادة تحتوي على 10 أسئلة.",

            subjects_keyboard(chat_id)
        )

        return "OK"


    # =====================================================
    # 📚 اختيار مادة
    # =====================================================

    if text in QUESTIONS:

        start_subject(
            chat_id,
            text
        )

        return "OK"


    # =====================================================
    # 📊 المعدل
    # =====================================================

    if text == "📊 أظهر لي معدلي":

        show_average(chat_id)

        return "OK"


    # =====================================================
    # 🔄 إعادة
    # =====================================================

    if text == "🔄 إعادة الاختبارات":

        reset_tests(chat_id)

        return "OK"


    # =====================================================
    # 🤖 رسالة افتراضية
    # =====================================================

    send_message(
        chat_id,
        "🤖 استخدم الأزرار الموجودة في القائمة."
    )

    return "OK"


# =========================================================
# 🚀 تشغيل التطبيق
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
