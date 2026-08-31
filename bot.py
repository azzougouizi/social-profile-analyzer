import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# ==============================
# إعدادات Telegram
# ==============================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ WARNING: BOT_TOKEN غير موجود في Environment Variables")


# ==============================
# تخزين مؤقت للطلاب
# ==============================

users = {}


# ==============================
# الأسئلة
# يمكنك إضافة أسئلة أخرى هنا
# ==============================

QUIZES = {

    "الرياضيات": [
        {
            "question": "ما هو ناتج 5 × 6 ؟",
            "options": ["20", "25", "30", "35"],
            "answer": 2
        },
        {
            "question": "ما هو الجذر التربيعي للعدد 81 ؟",
            "options": ["7", "8", "9", "10"],
            "answer": 2
        },
        {
            "question": "إذا كان x = 5، فما قيمة 2x + 3 ؟",
            "options": ["10", "11", "13", "15"],
            "answer": 2
        },
        {
            "question": "ما هو مشتق x² ؟",
            "options": ["x", "2x", "x²", "2"],
            "answer": 1
        },
        {
            "question": "ما قيمة 10² ؟",
            "options": ["20", "50", "100", "1000"],
            "answer": 2
        }
    ],

    "الفيزياء": [
        {
            "question": "ما هي وحدة قياس القوة؟",
            "options": ["جول", "واط", "نيوتن", "باسكال"],
            "answer": 2
        },
        {
            "question": "ما هي سرعة الضوء تقريبًا؟",
            "options": [
                "3000 km/s",
                "30000 km/s",
                "300000 km/s",
                "3000000 km/s"
            ],
            "answer": 2
        },
        {
            "question": "ما هي وحدة قياس الطاقة؟",
            "options": ["نيوتن", "جول", "أمبير", "فولت"],
            "answer": 1
        },
        {
            "question": "ما الجهاز المستخدم لقياس شدة التيار الكهربائي؟",
            "options": [
                "الفولتميتر",
                "الأميتر",
                "البارومتر",
                "الترمومتر"
            ],
            "answer": 1
        }
    ],

    "العلوم": [
        {
            "question": "ما هي الوحدة الأساسية للحياة؟",
            "options": ["النسيج", "العضو", "الخلية", "الجزيء"],
            "answer": 2
        },
        {
            "question": "أين تحدث عملية البناء الضوئي؟",
            "options": [
                "النواة",
                "الميتوكوندريا",
                "البلاستيدات الخضراء",
                "الريبوسومات"
            ],
            "answer": 2
        },
        {
            "question": "ما الغاز الذي تمتصه النباتات في البناء الضوئي؟",
            "options": [
                "الأكسجين",
                "النيتروجين",
                "ثاني أكسيد الكربون",
                "الهيدروجين"
            ],
            "answer": 2
        }
    ],

    "التاريخ": [
        {
            "question": "متى اندلعت الثورة التحريرية الجزائرية؟",
            "options": [
                "1952",
                "1954",
                "1956",
                "1962"
            ],
            "answer": 1
        },
        {
            "question": "متى استقلت الجزائر؟",
            "options": [
                "1954",
                "1960",
                "1962",
                "1963"
            ],
            "answer": 2
        },
        {
            "question": "ما هو تاريخ اندلاع الثورة الجزائرية؟",
            "options": [
                "1 نوفمبر 1954",
                "5 يوليو 1962",
                "19 مارس 1962",
                "8 ماي 1945"
            ],
            "answer": 0
        }
    ],

    "الجغرافيا": [
        {
            "question": "ما هي أكبر قارة في العالم من حيث المساحة؟",
            "options": [
                "إفريقيا",
                "أوروبا",
                "آسيا",
                "أمريكا الجنوبية"
            ],
            "answer": 2
        },
        {
            "question": "ما هو أكبر محيط في العالم؟",
            "options": [
                "المحيط الأطلسي",
                "المحيط الهندي",
                "المحيط الهادئ",
                "المحيط المتجمد"
            ],
            "answer": 2
        }
    ],

    "اللغة العربية": [
        {
            "question": "ما هو جمع كلمة «كتاب»؟",
            "options": [
                "كاتب",
                "كتابات",
                "كتب",
                "مكتبة"
            ],
            "answer": 2
        },
        {
            "question": "ما نوع كلمة «جميل» في الجملة: «منظر جميل»؟",
            "options": [
                "فعل",
                "اسم",
                "صفة",
                "حرف"
            ],
            "answer": 2
        }
    ],

    "الفرنسية": [
        {
            "question": "Quel est le pluriel de « livre » ?",
            "options": [
                "livres",
                "livre",
                "livreses",
                "livrez"
            ],
            "answer": 0
        },
        {
            "question": "Quel est le contraire de « grand » ?",
            "options": [
                "fort",
                "petit",
                "long",
                "haut"
            ],
            "answer": 1
        }
    ],

    "الإنجليزية": [
        {
            "question": "What is the past tense of 'go'?",
            "options": [
                "goed",
                "gone",
                "went",
                "going"
            ],
            "answer": 2
        },
        {
            "question": "Choose the correct sentence:",
            "options": [
                "He go to school.",
                "He goes to school.",
                "He going school.",
                "He gone school."
            ],
            "answer": 1
        }
    ]
}


# ==============================
# Telegram API
# ==============================

def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    try:
        response = requests.post(
            url,
            json=data,
            timeout=20
        )

        print(
            "Telegram:",
            method,
            response.status_code,
            response.text[:500]
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

    telegram_request(
        "sendMessage",
        data
    )


def edit_message(chat_id, message_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    telegram_request(
        "editMessageText",
        data
    )


# ==============================
# القائمة الرئيسية
# ==============================

def main_menu():

    return {
        "keyboard": [
            ["📝 الاختبارات"],
            ["📊 نتيجتي"],
            ["🎓 تغيير الشعبة"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


# ==============================
# قائمة المواد
# ==============================

def subjects_menu():

    return {
        "keyboard": [
            ["📐 الرياضيات", "⚡ الفيزياء"],
            ["🧬 العلوم", "🌍 التاريخ"],
            ["🗺️ الجغرافيا", "📖 اللغة العربية"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🔙 رجوع"]
        ],
        "resize_keyboard": True
    }


# ==============================
# تحويل اسم المادة
# ==============================

SUBJECT_NAMES = {
    "📐 الرياضيات": "الرياضيات",
    "⚡ الفيزياء": "الفيزياء",
    "🧬 العلوم": "العلوم",
    "🌍 التاريخ": "التاريخ",
    "🗺️ الجغرافيا": "الجغرافيا",
    "📖 اللغة العربية": "اللغة العربية",
    "🇫🇷 الفرنسية": "الفرنسية",
    "🇬🇧 الإنجليزية": "الإنجليزية"
}


# ==============================
# بداية اختبار
# ==============================

def start_quiz(chat_id, subject):

    questions = QUIZES.get(subject, [])

    if not questions:

        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة حاليًا."
        )

        return

    questions = questions.copy()

    random.shuffle(questions)

    users[chat_id] = {
        "subject": subject,
        "questions": questions,
        "current": 0,
        "score": 0,
        "answered": False
    }

    send_question(chat_id)


# ==============================
# إرسال السؤال
# ==============================

def send_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    current = user["current"]
    questions = user["questions"]

    if current >= len(questions):

        finish_quiz(chat_id)

        return

    question = questions[current]

    options = question["options"]

    keyboard = []

    for index, option in enumerate(options):

        keyboard.append(
            [
                {
                    "text": f"{chr(65 + index)} - {option}",
                    "callback_data": f"answer_{index}"
                }
            ]
        )

    reply_markup = {
        "inline_keyboard": keyboard
    }

    text = (
        f"📝 اختبار {user['subject']}\n\n"
        f"السؤال {current + 1} من {len(questions)}\n\n"
        f"❓ {question['question']}\n\n"
        "اختر الإجابة الصحيحة:"
    )

    send_message(
        chat_id,
        text,
        reply_markup
    )


# ==============================
# إنهاء الاختبار
# ==============================

def finish_quiz(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    score = user["score"]
    total = len(user["questions"])

    percentage = round(
        (score / total) * 100
    )

    if percentage >= 80:
        message = "🏆 ممتاز! مستوى رائع جدًا."
    elif percentage >= 60:
        message = "👏 جيد جدًا! استمر في المراجعة."
    elif percentage >= 50:
        message = "👍 نتيجة مقبولة، ويمكنك تحسينها."
    else:
        message = "💪 لا تستسلم، راجع الدرس وأعد الاختبار."

    users[chat_id]["last_score"] = score
    users[chat_id]["last_total"] = total
    users[chat_id]["last_percentage"] = percentage

    send_message(
        chat_id,
        f"🎉 انتهى الاختبار!\n\n"
        f"📚 المادة: {user['subject']}\n"
        f"✅ الإجابات الصحيحة: {score}\n"
        f"❌ الإجابات الخاطئة: {total - score}\n"
        f"📊 النتيجة: {percentage}%\n\n"
        f"{message}\n\n"
        "🔄 يمكنك بدء اختبار جديد من القائمة."
    )

    users[chat_id]["questions"] = []
    users[chat_id]["current"] = 0
    users[chat_id]["score"] = 0


# ==============================
# معالجة أزرار الاختبار
# ==============================

def handle_callback(callback):

    callback_id = callback.get("id")

    data = callback.get("data", "")

    message = callback.get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    message_id = message.get("message_id")

    # إزالة حالة الضغط من Telegram
    telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )

    if not chat_id:
        return

    user = users.get(chat_id)

    if not user:
        send_message(
            chat_id,
            "❌ انتهى الاختبار. ابدأ اختبارًا جديدًا."
        )
        return

    if not data.startswith("answer_"):
        return

    if user.get("answered"):
        return

    try:

        selected = int(
            data.replace(
                "answer_",
                ""
            )
        )

    except ValueError:
        return

    current = user["current"]

    questions = user["questions"]

    if current >= len(questions):
        return

    question = questions[current]

    correct = question["answer"]

    user["answered"] = True

    if selected == correct:

        user["score"] += 1

        result_text = "✅ إجابة صحيحة!"

    else:

        correct_text = question["options"][correct]

        result_text = (
            f"❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة: {correct_text}"
        )

    edit_message(
        chat_id,
        message_id,
        (
            f"{result_text}\n\n"
            f"📊 نقاطك الحالية: {user['score']}\n\n"
            "⏭️ اضغط «السؤال التالي» للمتابعة."
        ),
        {
            "inline_keyboard": [
                [
                    {
                        "text": "➡️ السؤال التالي",
                        "callback_data": "next_question"
                    }
                ]
            ]
        }
    )


# ==============================
# السؤال التالي
# ==============================

def handle_next_question(callback):

    callback_id = callback.get("id")

    message = callback.get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )

    if not chat_id:
        return

    user = users.get(chat_id)

    if not user:
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


# ==============================
# Flask
# ==============================

@app.route("/", methods=["GET"])
def home():

    return "🇩🇿 BAC DZ AI is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    data = request.get_json(
        silent=True
    ) or {}

    # ==========================
    # Callback Query
    # ==========================

    callback = data.get("callback_query")

    if callback:

        callback_data = callback.get(
            "data",
            ""
        )

        if callback_data == "next_question":

            handle_next_question(
                callback
            )

        elif callback_data.startswith(
            "answer_"
        ):

            handle_callback(
                callback
            )

        return "OK"


    # ==========================
    # Message
    # ==========================

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


    # ==========================
    # START
    # ==========================

    if text == "/start":

        users[chat_id] = {
            "step": "main"
        }

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في BAC DZ AI 🎓\n\n"
            "رفيقك في التحضير للبكالوريا 📚\n\n"
            "اختر الخدمة التي تريدها:",
            main_menu()
        )

        return "OK"


    # ==========================
    # الاختبارات
    # ==========================

    if text == "📝 الاختبارات":

        users[chat_id] = {
            "step": "subjects"
        }

        send_message(
            chat_id,
            "📚 اختر المادة التي تريد اختبار نفسك فيها:",
            subjects_menu()
        )

        return "OK"


    # ==========================
    # اختيار المادة
    # ==========================

    if text in SUBJECT_NAMES:

        subject = SUBJECT_NAMES[text]

        start_quiz(
            chat_id,
            subject
        )

        return "OK"


    # ==========================
    # رجوع
    # ==========================

    if text == "🔙 رجوع":

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_menu()
        )

        return "OK"


    # ==========================
    # النتيجة
    # ==========================

    if text == "📊 نتيجتي":

        user = users.get(
            chat_id,
            {}
        )

        if "last_score" not in user:

            send_message(
                chat_id,
                "📊 لا توجد نتيجة بعد.\n\n"
                "ابدأ اختبارًا أولًا من 📝 الاختبارات."
            )

        else:

            send_message(
                chat_id,
                f"📊 آخر نتيجة لك:\n\n"
                f"✅ الصحيح: {user['last_score']}\n"
                f"❌ الخطأ: "
                f"{user['last_total'] - user['last_score']}\n"
                f"🏆 النتيجة: "
                f"{user['last_percentage']}%"
            )

        return "OK"


    # ==========================
    # تغيير الشعبة
    # ==========================

    if text == "🎓 تغيير الشعبة":

        send_message(
            chat_id,
            "🎓 سيتم إضافة اختيار الشعبة في المرحلة القادمة."
        )

        return "OK"


    # ==========================
    # المساعدة
    # ==========================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ BAC DZ AI\n\n"
            "📝 الاختبارات:\n"
            "اختر المادة وأجب عن الأسئلة.\n\n"
            "📊 نتيجتي:\n"
            "تعرف على آخر نتيجة لك.\n\n"
            "🎓 تغيير الشعبة:\n"
            "سيتم تطويرها لاحقًا.\n\n"
            "🚀 سيتم إضافة خدمات أخرى في الإصدارات القادمة."
        )

        return "OK"


    # ==========================
    # رسالة غير معروفة
    # ==========================

    send_message(
        chat_id,
        "استخدم /start لفتح القائمة الرئيسية."
    )

    return "OK"


# ==============================
# تشغيل السيرفر
# ==============================

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
