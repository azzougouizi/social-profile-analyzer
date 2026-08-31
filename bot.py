import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

users = {}


# ==================================================
# روابط أرشيف البكالوريا
# ==================================================

BAC_ARCHIVE_URL = "https://eddirasa.com/ens-sec/3as/bac-solutions/"


# ==================================================
# أسئلة الاختبارات
# ==================================================

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
        }
    ],

    "الفيزياء": [
        {
            "question": "ما هي وحدة قياس القوة؟",
            "options": ["جول", "واط", "نيوتن", "باسكال"],
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
        }
    ]
}


# ==================================================
# Telegram
# ==================================================

def telegram_request(method, data):

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود")
        return None

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
            response.status_code
        )

        return response.json()

    except Exception as error:

        print(
            "Telegram error:",
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

    telegram_request(
        "sendMessage",
        data
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

    telegram_request(
        "editMessageText",
        data
    )


# ==================================================
# القائمة الرئيسية
# ==================================================

def main_menu():

    return {
        "keyboard": [
            ["📝 الاختبارات"],
            ["📄 مواضيع البكالوريا"],
            ["📊 نتيجتي"],
            ["🎓 شعب البكالوريا"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


# ==================================================
# قائمة الاختبارات
# ==================================================

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


# ==================================================
# شعب البكالوريا
# ==================================================

BAC_BRANCHES = [
    "🔬 علوم تجريبية",
    "📐 رياضيات",
    "⚙️ تقني رياضي",
    "💼 تسيير واقتصاد",
    "📚 آداب وفلسفة",
    "🌍 لغات أجنبية",
    "🎨 فنون"
]


def branches_menu():

    rows = []

    for branch in BAC_BRANCHES:

        rows.append([branch])

    rows.append(["🔙 رجوع"])

    return {
        "keyboard": rows,
        "resize_keyboard": True
    }


# ==================================================
# السنوات
# ==================================================

def years_menu():

    return {
        "keyboard": [
            ["2026", "2025", "2024"],
            ["2023", "2022", "2021"],
            ["2020", "2019", "2018"],
            ["2017", "2016", "2015"],
            ["2014", "2013", "2012"],
            ["2011", "2010", "2009"],
            ["2008"],
            ["🔙 رجوع"]
        ],
        "resize_keyboard": True
    }


# ==================================================
# بدء الاختبار
# ==================================================

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
        "step": "quiz",
        "subject": subject,
        "questions": questions,
        "current": 0,
        "score": 0,
        "answered": False
    }

    send_question(chat_id)


# ==================================================
# إرسال سؤال
# ==================================================

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

    keyboard = []

    for index, option in enumerate(
        question["options"]
    ):

        keyboard.append([
            {
                "text": f"{chr(65 + index)} - {option}",
                "callback_data": f"answer_{index}"
            }
        ])

    send_message(
        chat_id,
        f"📝 اختبار {user['subject']}\n\n"
        f"السؤال {current + 1} من "
        f"{len(questions)}\n\n"
        f"❓ {question['question']}\n\n"
        "اختر الإجابة:",
        {
            "inline_keyboard": keyboard
        }
    )


# ==================================================
# إنهاء الاختبار
# ==================================================

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

        message = "🏆 ممتاز! استمر هكذا."

    elif percentage >= 60:

        message = "👏 جيد جدًا، واصل المراجعة."

    elif percentage >= 50:

        message = "👍 نتيجة مقبولة ويمكن تحسينها."

    else:

        message = "💪 لا تستسلم، راجع الدروس وأعد الاختبار."

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage

    send_message(
        chat_id,
        f"🎉 انتهى الاختبار!\n\n"
        f"📚 المادة: {user['subject']}\n"
        f"✅ صحيح: {score}\n"
        f"❌ خطأ: {total - score}\n"
        f"📊 النتيجة: {percentage}%\n\n"
        f"{message}"
    )


# ==================================================
# Callback
# ==================================================

def handle_callback(callback):

    callback_id = callback.get("id")

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

    chat_id = chat.get(
        "id"
    )

    message_id = message.get(
        "message_id"
    )

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

    if data == "next_question":

        user["current"] += 1
        user["answered"] = False

        send_question(chat_id)

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

    question = user["questions"][current]

    correct = question["answer"]

    user["answered"] = True

    if selected == correct:

        user["score"] += 1

        result = "✅ إجابة صحيحة!"

    else:

        correct_text = question["options"][correct]

        result = (
            "❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة: {correct_text}"
        )

    edit_message(
        chat_id,
        message_id,
        f"{result}\n\n"
        f"📊 نقاطك: {user['score']}\n\n"
        "اضغط للانتقال للسؤال التالي:",
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


# ==================================================
# Flask
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return "🇩🇿 BAC DZ AI is running!"


@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    data = request.get_json(
        silent=True
    ) or {}

    callback = data.get(
        "callback_query"
    )

    if callback:

        handle_callback(
            callback
        )

        return "OK"

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


    # ==========================================
    # START
    # ==========================================

    if text == "/start":

        users[chat_id] = {
            "step": "main"
        }

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في BAC DZ AI 🎓\n\n"
            "مساعدك للتحضير للبكالوريا.\n\n"
            "اختر الخدمة:",
            main_menu()
        )

        return "OK"


    # ==========================================
    # الاختبارات
    # ==========================================

    if text == "📝 الاختبارات":

        users[chat_id] = {
            "step": "subjects"
        }

        send_message(
            chat_id,
            "📚 اختر المادة:",
            subjects_menu()
        )

        return "OK"


    # ==========================================
    # اختيار مادة
    # ==========================================

    if text in SUBJECT_NAMES:

        start_quiz(
            chat_id,
            SUBJECT_NAMES[text]
        )

        return "OK"


    # ==========================================
    # مواضيع البكالوريا
    # ==========================================

    if text == "📄 مواضيع البكالوريا":

        users[chat_id] = {
            "step": "bac_branch"
        }

        send_message(
            chat_id,
            "🎓 اختر شعبة البكالوريا:",
            branches_menu()
        )

        return "OK"


    # ==========================================
    # اختيار الشعبة
    # ==========================================

    if (
        text in BAC_BRANCHES
        and users.get(chat_id, {}).get("step")
        == "bac_branch"
    ):

        users[chat_id] = {
            "step": "bac_year",
            "branch": text
        }

        send_message(
            chat_id,
            f"🎓 الشعبة: {text}\n\n"
            "📅 اختر السنة:",
            years_menu()
        )

        return "OK"


    # ==========================================
    # اختيار السنة
    # ==========================================

    if (
        text.isdigit()
        and len(text) == 4
        and users.get(chat_id, {}).get("step")
        == "bac_year"
    ):

        year = int(text)

        if year < 2008 or year > 2026:

            send_message(
                chat_id,
                "❌ اختر سنة بين 2008 و2026."
            )

            return "OK"

        branch = users[chat_id].get(
            "branch",
            ""
        )

        users[chat_id]["year"] = year

        send_message(
            chat_id,
            f"🎓 الشعبة: {branch}\n"
            f"📅 السنة: {year}\n\n"
            "📚 افتح أرشيف المواضيع والحلول:",
            {
                "inline_keyboard": [
                    [
                        {
                            "text": "📄 فتح مواضيع البكالوريا",
                            "url": BAC_ARCHIVE_URL
                        }
                    ]
                ]
            }
        )

        return "OK"


    # ==========================================
    # النتيجة
    # ==========================================

    if text == "📊 نتيجتي":

        user = users.get(
            chat_id,
            {}
        )

        if "last_score" not in user:

            send_message(
                chat_id,
                "📊 لا توجد نتيجة بعد.\n\n"
                "ابدأ اختبارًا من 📝 الاختبارات."
            )

        else:

            send_message(
                chat_id,
                f"📊 آخر نتيجة:\n\n"
                f"✅ صحيح: {user['last_score']}\n"
                f"❌ خطأ: "
                f"{user['last_total'] - user['last_score']}\n"
                f"🏆 النتيجة: "
                f"{user['last_percentage']}%"
            )

        return "OK"


    # ==========================================
    # الشعب
    # ==========================================

    if text == "🎓 شعب البكالوريا":

        send_message(
            chat_id,
            "🎓 الشعب المتوفرة:\n\n"
            "🔬 علوم تجريبية\n"
            "📐 رياضيات\n"
            "⚙️ تقني رياضي\n"
            "💼 تسيير واقتصاد\n"
            "📚 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n"
            "🎨 فنون"
        )

        return "OK"


    # ==========================================
    # رجوع
    # ==========================================

    if text == "🔙 رجوع":

        users[chat_id] = {
            "step": "main"
        }

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_menu()
        )

        return "OK"


    # ==========================================
    # المساعدة
    # ==========================================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ BAC DZ AI\n\n"
            "📝 الاختبارات:\n"
            "اختبر نفسك في المواد المختلفة.\n\n"
            "📄 مواضيع البكالوريا:\n"
            "اختر الشعبة والسنة للوصول إلى الأرشيف.\n\n"
            "📊 نتيجتي:\n"
            "تعرف على آخر نتيجة للاختبار."
        )

        return "OK"


    # ==========================================
    # رسالة غير معروفة
    # ==========================================

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة الرئيسية."
    )

    return "OK"


# ==================================================
# تشغيل التطبيق
# ==================================================

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
