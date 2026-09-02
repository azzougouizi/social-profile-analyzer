import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# إعدادات Telegram
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# تخزين بيانات الطلاب مؤقتًا
users = {}


# =========================================================
# بنك الأسئلة — آداب وفلسفة
# =========================================================

QUESTIONS = {

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
            "options": ["أرسطو", "ديكارت", "سقراط", "هيغل"],
            "answer": 1
        },
        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": ["أفلاطون", "كانط", "ديكارت", "سقراط"],
            "answer": 0
        },
        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": ["سقراط", "أرسطو", "كانط", "ماركس"],
            "answer": 1
        },
        {
            "q": "الفلسفة تعني أساسًا:",
            "options": [
                "حب الحكمة",
                "حفظ المعلومات",
                "دراسة الطبيعة فقط",
                "دراسة الرياضة"
            ],
            "answer": 0
        },
        {
            "q": "من ربط الأخلاق بالواجب؟",
            "options": ["كانط", "نيتشه", "أفلاطون", "ماركس"],
            "answer": 0
        },
        {
            "q": "ما المقصود بالحقيقة في التصور الكلاسيكي؟",
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

    "🇩🇿 اللغة العربية": [
        {
            "q": "ما نوع كلمة «كتب»؟",
            "options": ["فعل ماضٍ", "اسم", "حرف", "فعل أمر"],
            "answer": 0
        },
        {
            "q": "جمع كلمة «كتاب» هو:",
            "options": ["كتب", "كاتبات", "مكتوب", "كتابان"],
            "answer": 0
        },
        {
            "q": "الفاعل يكون غالبًا:",
            "options": ["مرفوعًا", "منصوبًا", "مجرورًا", "مجزومًا"],
            "answer": 0
        },
        {
            "q": "ما ضد كلمة «النجاح»؟",
            "options": ["الفشل", "التفوق", "العمل", "العلم"],
            "answer": 0
        },
        {
            "q": "الجملة الاسمية تبدأ بـ:",
            "options": ["اسم", "فعل", "حرف جر", "ضمير فقط"],
            "answer": 0
        },
        {
            "q": "المبتدأ يكون:",
            "options": ["مرفوعًا", "منصوبًا", "مجرورًا", "مجزومًا"],
            "answer": 0
        },
        {
            "q": "الفعل المضارع يدل غالبًا على:",
            "options": ["الحاضر أو المستقبل", "الماضي فقط", "الأمر فقط", "الاسم"],
            "answer": 0
        },
        {
            "q": "ما نوع كلمة «في»؟",
            "options": ["حرف جر", "اسم", "فعل", "صفة"],
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
            "q": "الخبر في الجملة الاسمية يكون:",
            "options": ["مرفوعًا", "مجزومًا", "مجرورًا دائمًا", "فعل أمر"],
            "answer": 0
        }
    ],

    "🇫🇷 الفرنسية": [
        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": ["triste", "content", "fatigué", "malade"],
            "answer": 1
        },
        {
            "q": "Complétez : Je ___ au lycée.",
            "options": ["vais", "va", "allez", "allons"],
            "answer": 0
        },
        {
            "q": "Le contraire de « difficile » est :",
            "options": ["facile", "long", "fort", "ancien"],
            "answer": 0
        },
        {
            "q": "Le pluriel de « cheval » est :",
            "options": ["chevaux", "chevals", "chevales", "chevaus"],
            "answer": 0
        },
        {
            "q": "« J'ai étudié » est au :",
            "options": ["passé composé", "présent", "futur", "imparfait"],
            "answer": 0
        },
        {
            "q": "Nous ___ nos devoirs.",
            "options": ["faisons", "fait", "faites", "faire"],
            "answer": 0
        },
        {
            "q": "Quel mot est un adjectif ?",
            "options": ["intelligent", "courir", "maison", "rapidement"],
            "answer": 0
        },
        {
            "q": "Le féminin de « acteur » est :",
            "options": ["actrice", "acteuse", "acteurs", "acteur"],
            "answer": 0
        },
        {
            "q": "Quel est le contraire de « ancien » ?",
            "options": ["moderne", "vieux", "historique", "passé"],
            "answer": 0
        },
        {
            "q": "« Merci » signifie :",
            "options": ["شكرا", "مرحبا", "وداعًا", "نعم"],
            "answer": 0
        }
    ],

    "🇬🇧 الإنجليزية": [
        {
            "q": "She ___ English every day.",
            "options": ["studies", "study", "studying", "studied"],
            "answer": 0
        },
        {
            "q": "What is the past tense of go?",
            "options": ["went", "goed", "gone", "going"],
            "answer": 0
        },
        {
            "q": "Choose: I ___ a student.",
            "options": ["am", "is", "are", "be"],
            "answer": 0
        },
        {
            "q": "What is the opposite of easy?",
            "options": ["hard", "simple", "small", "short"],
            "answer": 0
        },
        {
            "q": "They ___ playing now.",
            "options": ["are", "is", "am", "be"],
            "answer": 0
        },
        {
            "q": "What does environment mean?",
            "options": ["البيئة", "الرياضة", "التاريخ", "الاقتصاد"],
            "answer": 0
        },
        {
            "q": "I have lived here ___ 2020.",
            "options": ["since", "for", "at", "on"],
            "answer": 0
        },
        {
            "q": "The comparative of good is:",
            "options": ["better", "gooder", "best", "more good"],
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
            "options": ["written", "wrote", "writes", "writing"],
            "answer": 0
        }
    ]
}


# =========================================================
# Telegram Functions
# =========================================================

def telegram(method, data):

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
        {"callback_query_id": callback_id}
    )


# =========================================================
# اختيار الشعبة
# =========================================================

def branch_keyboard():

    return {
        "keyboard": [
            ["🧠 آداب وفلسفة"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# مواد الشعبة
# =========================================================

def subjects_keyboard(chat_id):

    user = users[chat_id]

    buttons = []

    for subject in QUESTIONS.keys():

        buttons.append([subject])

    # يظهر فقط إذا أجاب الطالب عن جميع المواد
    completed = user.get("completed_subjects", {})

    if len(completed) == len(QUESTIONS):

        buttons.append(["📊 أظهر لي معدلي"])

    buttons.append(["🔄 إعادة الاختبارات"])

    return {
        "keyboard": buttons,
        "resize_keyboard": True
    }


# =========================================================
# بدء اختبار المادة
# =========================================================

def start_subject(chat_id, subject):

    user = users.setdefault(chat_id, {})

    if subject in user.get("completed_subjects", {}):

        send_message(
            chat_id,
            f"✅ لقد أكملت اختبار {subject} سابقًا.\n\n"
            "يمكنك إكمال المواد الأخرى أو حساب معدلك.",
            subjects_keyboard(chat_id)
        )
        return

    questions = QUESTIONS[subject]

    # اختيار 10 أسئلة
    selected = random.sample(
        questions,
        min(10, len(questions))
    )

    user["quiz"] = {
        "subject": subject,
        "questions": selected,
        "current": 0,
        "score": 0
    }

    send_question(chat_id)


# =========================================================
# إرسال السؤال
# =========================================================

def send_question(chat_id):

    user = users[chat_id]
    quiz = user["quiz"]

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
# معالجة الإجابة
# =========================================================

def handle_answer(callback):

    chat_id = callback["message"]["chat"]["id"]

    answer_callback(callback["id"])

    user = users.get(chat_id)

    if not user or "quiz" not in user:
        return

    quiz = user["quiz"]

    selected = int(
        callback["data"].replace("answer_", "")
    )

    question = quiz["questions"][quiz["current"]]

    correct = question["answer"]

    if selected == correct:

        quiz["score"] += 1

        result = "✅ إجابة صحيحة!"

    else:

        result = (
            "❌ إجابة خاطئة!\n\n"
            f"✅ الإجابة الصحيحة: "
            f"{question['options'][correct]}"
        )

    quiz["current"] += 1

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
# السؤال التالي
# =========================================================

def next_question(callback):

    chat_id = callback["message"]["chat"]["id"]

    answer_callback(callback["id"])

    send_question(chat_id)


# =========================================================
# إنهاء اختبار المادة
# =========================================================

def finish_subject(chat_id):

    user = users[chat_id]
    quiz = user["quiz"]

    subject = quiz["subject"]

    score = quiz["score"]

    # تحويل النتيجة إلى معدل /20
    grade = score * 2

    user.setdefault(
        "completed_subjects",
        {}
    )

    user["completed_subjects"][subject] = grade

    del user["quiz"]

    send_message(
        chat_id,
        f"🎉 انتهيت من اختبار {subject}!\n\n"
        f"✅ الإجابات الصحيحة: {score}/10\n"
        f"📊 معدلك في المادة: {grade}/20\n\n"
        "📚 اختر المادة التالية 👇",
        subjects_keyboard(chat_id)
    )


# =========================================================
# حساب المعدل العام
# =========================================================

def show_average(chat_id):

    user = users.get(chat_id, {})

    completed = user.get(
        "completed_subjects",
        {}
    )

    if len(completed) < len(QUESTIONS):

        remaining = len(QUESTIONS) - len(completed)

        send_message(
            chat_id,
            f"⚠️ يجب إنهاء جميع المواد أولًا.\n\n"
            f"📚 بقيت لك {remaining} مادة."
        )

        return

    grades = list(completed.values())

    average = sum(grades) / len(grades)

    # نسبة النجاح
    success_percentage = round(
        average / 20 * 100,
        1
    )

    if average >= 16:

        level = "🏆 ممتاز جدًا"

    elif average >= 14:

        level = "🔥 جيد جدًا"

    elif average >= 10:

        level = "👍 ناجح"

    else:

        level = "💪 تحتاج إلى المزيد من التدريب"

    result = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🎓 نتيجتك الدراسية\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for subject, grade in completed.items():

        result += f"{subject}: {grade}/20\n"

    result += (
        "\n━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 معدلك العام: {average:.2f}/20\n"
        f"📈 نسبة النجاح: {success_percentage}%\n"
        f"🏆 تقييمك: {level}\n\n"
        "🎯 استمر في التدريب، كل اختبار يجعلك أفضل!"
    )

    send_message(chat_id, result)


# =========================================================
# إعادة الاختبارات
# =========================================================

def reset_tests(chat_id):

    users[chat_id]["completed_subjects"] = {}

    users[chat_id].pop("quiz", None)

    send_message(
        chat_id,
        "🔄 تم إعادة جميع الاختبارات!\n\n"
        "🎓 يمكنك البدء من جديد.",
        subjects_keyboard(chat_id)
    )


# =========================================================
# Flask
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
    # الأزرار Inline
    # =====================================================

    callback = data.get("callback_query")

    if callback:

        callback_data = callback.get("data", "")

        if callback_data.startswith("answer_"):

            handle_answer(callback)

        elif callback_data == "next":

            next_question(callback)

        return "OK"

    # =====================================================
    # الرسائل
    # =====================================================

    message = data.get("message", {})

    chat_id = message.get("chat", {}).get("id")

    text = message.get("text", "").strip()

    if not chat_id:
        return "OK"

    users.setdefault(chat_id, {})

    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        users[chat_id] = {}

        send_message(
            chat_id,
            "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"
            "📝 اختبر مستواك في مواد شعبتك.\n"
            "📊 أجب عن 10 أسئلة في كل مادة.\n"
            "🎯 وبعدها اكتشف معدلك التجريبي!\n\n"
            "👇 اختر شعبتك:",
            branch_keyboard()
        )

        return "OK"

    # =====================================================
    # اختيار الشعبة
    # =====================================================

    if text == "🧠 آداب وفلسفة":

        users[chat_id]["branch"] = "آداب وفلسفة"

        users[chat_id].setdefault(
            "completed_subjects",
            {}
        )

        send_message(
            chat_id,
            "🎓 شعبة آداب وفلسفة\n\n"
            "📚 اختر المادة التي تريد اختبار نفسك فيها:\n\n"
            "📝 كل مادة تحتوي على 10 أسئلة.",
            subjects_keyboard(chat_id)
        )

        return "OK"

    # =====================================================
    # اختيار مادة
    # =====================================================

    if text in QUESTIONS:

        if "branch" not in users[chat_id]:

            send_message(
                chat_id,
                "⚠️ اختر شعبتك أولًا.",
                branch_keyboard()
            )

            return "OK"

        start_subject(chat_id, text)

        return "OK"

    # =====================================================
    # حساب المعدل
    # =====================================================

    if text == "📊 أظهر لي معدلي":

        show_average(chat_id)

        return "OK"

    # =====================================================
    # إعادة الاختبارات
    # =====================================================

    if text == "🔄 إعادة الاختبارات":

        reset_tests(chat_id)

        return "OK"

    # =====================================================
    # رسالة افتراضية
    # =====================================================

    send_message(
        chat_id,
        "🤖 اختر أحد الأزرار من القائمة."
    )

    return "OK"


# =========================================================
# تشغيل التطبيق
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
