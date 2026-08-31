import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

# تخزين مؤقت للمستخدمين
users = {}


# =========================================================
# بنك الأسئلة
# =========================================================

QUESTIONS = {

    "الفلسفة": [
        {
            "q": "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            "answer": 2,
            "explanation": "المقولة الشهيرة تعود إلى رينيه ديكارت."
        },
        {
            "q": "ما المقصود بالفلسفة؟",
            "options": [
                "حفظ المعلومات",
                "حب الحكمة والبحث العقلي",
                "دراسة الرياضة",
                "دراسة النباتات"
            ],
            "answer": 1,
            "explanation": "الفلسفة تعني حب الحكمة وتعتمد على التفكير والتحليل."
        },
        {
            "q": "من صاحب نظرية المثل؟",
            "options": ["أفلاطون", "ديكارت", "كانط", "نيتشه"],
            "answer": 0,
            "explanation": "نظرية المثل من أشهر أفكار أفلاطون."
        },
        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": ["سقراط", "أرسطو", "كانط", "ديكارت"],
            "answer": 1,
            "explanation": "أرسطو اعتبر الإنسان كائنًا اجتماعيًا وسياسيًا."
        },
        {
            "q": "ما المقصود بالمنطق؟",
            "options": [
                "علم التفكير الصحيح",
                "علم التاريخ",
                "علم الفن",
                "علم الاقتصاد"
            ],
            "answer": 0,
            "explanation": "المنطق يهتم بقواعد التفكير والاستدلال الصحيح."
        },
        {
            "q": "من الفيلسوف المرتبط بالشك المنهجي؟",
            "options": ["أفلاطون", "ديكارت", "ماركس", "هيغل"],
            "answer": 1,
            "explanation": "اعتمد ديكارت الشك المنهجي للوصول إلى اليقين."
        },
        {
            "q": "الحرية ترتبط أساسًا بـ:",
            "options": [
                "الفوضى",
                "الاختيار والمسؤولية",
                "رفض التفكير",
                "إلغاء القوانين"
            ],
            "answer": 1,
            "explanation": "الحرية تعني القدرة على الاختيار مع تحمل المسؤولية."
        },
        {
            "q": "من ربط الأخلاق بالواجب؟",
            "options": ["كانط", "أفلاطون", "نيتشه", "أرسطو"],
            "answer": 0,
            "explanation": "كانط من أبرز الفلاسفة الذين ربطوا الأخلاق بالواجب."
        },
        {
            "q": "ما المقصود بالحقيقة في التصور الكلاسيكي؟",
            "options": [
                "الرأي الشخصي",
                "مطابقة الفكر للواقع",
                "الخيال",
                "الإشاعة"
            ],
            "answer": 1,
            "explanation": "الحقيقة في التصور الكلاسيكي هي مطابقة الفكر للواقع."
        },
        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "سقراط"],
            "answer": 0,
            "explanation": "كتاب الجمهورية من أشهر مؤلفات أفلاطون."
        },
        {
            "q": "ما الهدف من التفكير النقدي؟",
            "options": [
                "رفض كل شيء",
                "تحليل الأفكار والأدلة",
                "الحفظ فقط",
                "تجنب الأسئلة"
            ],
            "answer": 1,
            "explanation": "التفكير النقدي يقوم على التحليل وفحص الأدلة."
        },
        {
            "q": "ما المجال الذي يهتم بدراسة المعرفة؟",
            "options": [
                "الإبستمولوجيا",
                "الجماليات",
                "الاقتصاد",
                "السياسة"
            ],
            "answer": 0,
            "explanation": "الإبستمولوجيا تهتم بمصادر المعرفة وحدودها."
        },
        {
            "q": "من الفلاسفة اليونانيين القدماء؟",
            "options": ["سقراط", "ديكارت", "كانط", "ماركس"],
            "answer": 0,
            "explanation": "سقراط من أبرز فلاسفة اليونان القديمة."
        },
        {
            "q": "الأخلاق تهتم بـ:",
            "options": [
                "القيم والسلوك",
                "الطقس",
                "الحساب",
                "الجغرافيا"
            ],
            "answer": 0,
            "explanation": "الأخلاق تبحث في القيم التي توجه السلوك الإنساني."
        },
        {
            "q": "ما المجال الذي يهتم بالفن والجمال؟",
            "options": [
                "الجماليات",
                "المنطق",
                "الإبستمولوجيا",
                "السياسة"
            ],
            "answer": 0,
            "explanation": "علم الجمال يهتم بقضايا الفن والجمال."
        }
    ],

    "الفرنسية": [
        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": ["triste", "content", "malade", "fatigué"],
            "answer": 1,
            "explanation": "« Heureux » signifie « content »."
        },
        {
            "q": "Quel est le contraire de « difficile » ?",
            "options": ["long", "facile", "fort", "ancien"],
            "answer": 1,
            "explanation": "Le contraire de difficile est facile."
        },
        {
            "q": "Complétez : Je ___ au lycée.",
            "options": ["vais", "va", "allons", "allez"],
            "answer": 0,
            "explanation": "Avec « je », on dit « je vais »."
        },
        {
            "q": "Quel est le pluriel de « cheval » ?",
            "options": ["chevals", "chevaux", "chevales", "chevaus"],
            "answer": 1,
            "explanation": "Le pluriel de cheval est chevaux."
        },
        {
            "q": "« J'ai étudié » est au :",
            "options": ["présent", "futur", "passé composé", "imparfait"],
            "answer": 2,
            "explanation": "« J'ai étudié » est au passé composé."
        },
        {
            "q": "Complétez : Nous ___ nos devoirs.",
            "options": ["fait", "faisons", "faire", "faites"],
            "answer": 1,
            "explanation": "Avec nous, le verbe faire devient faisons."
        },
        {
            "q": "Quel mot est un adjectif ?",
            "options": ["rapidement", "maison", "intelligent", "courir"],
            "answer": 2,
            "explanation": "Intelligent est un adjectif."
        },
        {
            "q": "Quel est le féminin de « acteur » ?",
            "options": ["acteuse", "actrice", "acteurse", "acteur"],
            "answer": 1,
            "explanation": "Le féminin de acteur est actrice."
        },
        {
            "q": "Si j'avais le temps, je ___ davantage.",
            "options": ["lis", "lirais", "lirai", "lu"],
            "answer": 1,
            "explanation": "Après si + imparfait, on utilise le conditionnel."
        },
        {
            "q": "Quel est le contraire de « ancien » ?",
            "options": ["vieux", "moderne", "passé", "historique"],
            "answer": 1,
            "explanation": "Le contraire d'ancien peut être moderne."
        }
    ],

    "الإنجليزية": [
        {
            "q": "She ___ English every day.",
            "options": ["study", "studies", "studying", "studied"],
            "answer": 1,
            "explanation": "With she, we use studies."
        },
        {
            "q": "What is the past tense of go?",
            "options": ["goed", "gone", "went", "going"],
            "answer": 2,
            "explanation": "The past simple of go is went."
        },
        {
            "q": "Choose: I ___ a student.",
            "options": ["am", "is", "are", "be"],
            "answer": 0,
            "explanation": "With I, we use am."
        },
        {
            "q": "What is the opposite of easy?",
            "options": ["simple", "hard", "short", "small"],
            "answer": 1,
            "explanation": "The opposite of easy is hard."
        },
        {
            "q": "Choose the correct sentence.",
            "options": [
                "He don't like football.",
                "He doesn't like football.",
                "He doesn't likes football.",
                "He not like football."
            ],
            "answer": 1,
            "explanation": "We use doesn't + base verb."
        },
        {
            "q": "What is the comparative of good?",
            "options": ["gooder", "more good", "better", "best"],
            "answer": 2,
            "explanation": "The comparative form of good is better."
        },
        {
            "q": "They ___ playing now.",
            "options": ["is", "am", "are", "be"],
            "answer": 2,
            "explanation": "With they, we use are."
        },
        {
            "q": "What does environment mean?",
            "options": ["البيئة", "الرياضة", "التاريخ", "الاقتصاد"],
            "answer": 0,
            "explanation": "Environment means البيئة."
        },
        {
            "q": "I have lived here ___ 2020.",
            "options": ["for", "since", "at", "on"],
            "answer": 1,
            "explanation": "Since is used with a starting point."
        },
        {
            "q": "What is the past participle of write?",
            "options": ["wrote", "written", "writing", "writes"],
            "answer": 1,
            "explanation": "The past participle is written."
        }
    ],

    "الإسبانية": [
        {
            "q": "¿Cómo se dice « مرحبا » en español?",
            "options": ["Adiós", "Hola", "Gracias", "Por favor"],
            "answer": 1,
            "explanation": "Hola significa مرحبًا."
        },
        {
            "q": "¿Qué significa « gracias »?",
            "options": ["مرحبا", "شكرا", "وداعا", "نعم"],
            "answer": 1,
            "explanation": "Gracias significa شكرا."
        },
        {
            "q": "Completa: Yo ___ estudiante.",
            "options": ["soy", "eres", "es", "son"],
            "answer": 0,
            "explanation": "Con yo usamos soy."
        },
        {
            "q": "¿Cuál es el contrario de grande?",
            "options": ["alto", "pequeño", "bonito", "rápido"],
            "answer": 1,
            "explanation": "El contrario de grande es pequeño."
        },
        {
            "q": "¿Cómo se dice « كتاب »?",
            "options": ["mesa", "casa", "libro", "escuela"],
            "answer": 2,
            "explanation": "Libro significa كتاب."
        }
    ]
}


# =========================================================
# 🧬 أسئلة التحليل الدراسي
# =========================================================

ANALYSIS_QUESTIONS = [
    {
        "q": "📚 عندما تواجه درسًا صعبًا، ماذا تفعل؟",
        "options": [
            "أحاول فهمه حتى أنجح",
            "أبحث عن شرح آخر",
            "أؤجله",
            "أتجاهله"
        ],
        "scores": [
            {"analysis": 3, "persistence": 3},
            {"analysis": 2},
            {"organization": 1},
            {}
        ]
    },
    {
        "q": "⏰ كيف هو تركيزك أثناء الدراسة؟",
        "options": [
            "قوي جدًا",
            "جيد",
            "متوسط",
            "أتشتت بسرعة"
        ],
        "scores": [
            {"focus": 4},
            {"focus": 3},
            {"focus": 2},
            {"focus": 1}
        ]
    },
    {
        "q": "📝 عندما تخطئ في سؤال؟",
        "options": [
            "أحلل الخطأ",
            "أحاول مرة أخرى",
            "أشعر بالإحباط",
            "أتجاوزه"
        ],
        "scores": [
            {"analysis": 4},
            {"persistence": 3},
            {"confidence": 1},
            {}
        ]
    },
    {
        "q": "📅 هل لديك برنامج مراجعة؟",
        "options": [
            "نعم وألتزم به",
            "أحيانًا",
            "لا يوجد برنامج",
            "أراجع عشوائيًا"
        ],
        "scores": [
            {"organization": 4},
            {"organization": 2},
            {"organization": 1},
            {}
        ]
    },
    {
        "q": "🔥 عندما تتعب أثناء المراجعة؟",
        "options": [
            "أستريح ثم أعود",
            "أغير المادة",
            "أتوقف",
            "أؤجل كثيرًا"
        ],
        "scores": [
            {"persistence": 4},
            {"focus": 3},
            {"persistence": 1},
            {}
        ]
    },
    {
        "q": "🎯 كيف تتعامل مع المادة الضعيفة؟",
        "options": [
            "أخصص لها وقتًا إضافيًا",
            "أطلب المساعدة",
            "أركز على المواد السهلة",
            "أتجنبها"
        ],
        "scores": [
            {"persistence": 4, "organization": 3},
            {"analysis": 2},
            {"confidence": 1},
            {}
        ]
    },
    {
        "q": "📱 كيف تتعامل مع الهاتف أثناء الدراسة؟",
        "options": [
            "أضعه بعيدًا",
            "أستخدمه عند الحاجة",
            "أفتحه كثيرًا",
            "لا أستطيع تركه"
        ],
        "scores": [
            {"focus": 4},
            {"focus": 3},
            {"focus": 1},
            {}
        ]
    },
    {
        "q": "🏆 عندما تحصل على نتيجة جيدة؟",
        "options": [
            "أواصل العمل",
            "أفرح ثم أعود",
            "أرتاح طويلًا",
            "أتوقف مؤقتًا"
        ],
        "scores": [
            {"persistence": 4},
            {"persistence": 3},
            {"organization": 1},
            {}
        ]
    },
    {
        "q": "🧠 هل تراجع أخطاءك السابقة؟",
        "options": ["دائمًا", "غالبًا", "أحيانًا", "نادرًا"],
        "scores": [
            {"analysis": 4},
            {"analysis": 3},
            {"analysis": 2},
            {}
        ]
    },
    {
        "q": "⭐ كيف تصف ثقتك الدراسية؟",
        "options": [
            "أثق أنني أتحسن دائمًا",
            "ثقتي جيدة",
            "أتردد كثيرًا",
            "ثقتي ضعيفة"
        ],
        "scores": [
            {"confidence": 4},
            {"confidence": 3},
            {"confidence": 1},
            {}
        ]
    }
]


# =========================================================
# Telegram Functions
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
# القوائم
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            ["🧠 الفلسفة"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🇪🇸 الإسبانية"],
            ["🧬 تحليل مستواي الدراسي"],
            ["🧮 حساب المعدل"],
            ["🎭 نتيجة بكالوريا تجريبية"],
            ["📄 مواضيع PDF"],
            ["📊 مستواي", "🏆 الإنجازات"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# بدء الاختبار
# =========================================================

def start_quiz(chat_id, subject):

    questions = QUESTIONS.get(subject, [])

    if not questions:
        send_message(chat_id, "❌ لا توجد أسئلة لهذه المادة.")
        return

    count = min(10, len(questions))

    selected = random.sample(questions, count)

    old_user = users.get(chat_id, {})

    users[chat_id] = {
        **old_user,
        "mode": "quiz",
        "subject": subject,
        "questions": selected,
        "current": 0,
        "score": 0,
        "streak": 0,
        "best_streak": 0,
        "answered": False
    }

    send_question(chat_id)


def send_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    index = user["current"]

    if index >= len(user["questions"]):
        finish_quiz(chat_id)
        return

    question = user["questions"][index]

    keyboard = []

    for i, option in enumerate(question["options"]):

        keyboard.append([
            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"quiz_{i}"
            }
        ])

    send_message(
        chat_id,
        f"📚 المادة: {user['subject']}\n\n"
        f"📝 السؤال {index + 1}/{len(user['questions'])}\n\n"
        f"❓ {question['q']}",
        {
            "inline_keyboard": keyboard
        }
    )


def handle_quiz_answer(callback):

    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]

    answer_callback(callback["id"])

    user = users.get(chat_id)

    if not user or user.get("answered"):
        return

    selected = int(callback["data"].replace("quiz_", ""))

    question = user["questions"][user["current"]]

    correct = question["answer"]

    user["answered"] = True

    # عدد الأسئلة التي أجاب عنها الطالب طوال استخدام البوت
    user["total_answered"] = user.get("total_answered", 0) + 1

    if selected == correct:

        user["score"] += 1
        user["streak"] += 1

        user["best_streak"] = max(
            user["best_streak"],
            user["streak"]
        )

        user["total_correct"] = user.get("total_correct", 0) + 1

        text = (
            "✅ إجابة صحيحة!\n\n"
            f"🔥 سلسلة الإجابات: {user['streak']}\n\n"
            f"💡 {question['explanation']}"
        )

    else:

        user["streak"] = 0

        correct_text = question["options"][correct]

        text = (
            "❌ إجابة خاطئة\n\n"
            f"✅ الإجابة الصحيحة: {correct_text}\n\n"
            f"💡 {question['explanation']}"
        )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "➡️ السؤال التالي",
                    "callback_data": "next_question"
                }
            ]
        ]
    }

    edit_message(
        chat_id,
        message_id,
        text,
        keyboard
    )


def handle_next_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


def finish_quiz(chat_id):

    user = users[chat_id]

    total = len(user["questions"])
    score = user["score"]

    percentage = round(score / total * 100)

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage

    if percentage >= 90:
        level = "🏆 أسطوري"

    elif percentage >= 75:
        level = "🔥 ممتاز"

    elif percentage >= 60:
        level = "👏 جيد جدًا"

    elif percentage >= 50:
        level = "👍 جيد"

    else:
        level = "💪 تحتاج إلى تدريب أكثر"

    send_message(
        chat_id,
        f"🎉 انتهى الاختبار!\n\n"
        f"📚 المادة: {user['subject']}\n"
        f"✅ الصحيح: {score}/{total}\n"
        f"📊 النتيجة: {percentage}%\n"
        f"🏅 المستوى: {level}\n"
        f"🔥 أفضل سلسلة: {user['best_streak']}\n\n"
        "🚀 لا تتوقف هنا... كل سؤال تجيب عنه يقربك من هدفك!"
    )

    check_star_level(chat_id)


# =========================================================
# ⭐ نظام النجوم والتحفيز
# =========================================================

def check_star_level(chat_id):

    user = users.get(chat_id, {})

    answered = user.get("total_answered", 0)

    old_level = user.get("star_level", 0)

    if answered >= 150:
        level = 5
        title = "👑 طالب قوي وذكي جدًا"

    elif answered >= 120:
        level = 4
        title = "🔥 طالب متفوق"

    elif answered >= 90:
        level = 3
        title = "🚀 طالب متميز"

    elif answered >= 60:
        level = 2
        title = "⭐⭐ طالب مجتهد"

    elif answered >= 30:
        level = 1
        title = "⭐ طالب طموح"

    else:
        level = 0
        title = ""

    if level > old_level:

        user["star_level"] = level

        stars = "⭐" * level

        send_message(
            chat_id,
            f"🎉 إنجاز جديد!\n\n"
            f"{stars}\n\n"
            f"{title}\n\n"
            f"📚 أجبت الآن عن {answered} سؤالًا.\n\n"
            "💪 استمر... القادم أفضل!"
        )


# =========================================================
# 🧬 التحليل الدراسي
# =========================================================

def start_analysis(chat_id):

    users.setdefault(chat_id, {})

    users[chat_id]["analysis"] = {
        "current": 0,
        "scores": {
            "focus": 0,
            "organization": 0,
            "persistence": 0,
            "analysis": 0,
            "confidence": 0
        }
    }

    send_analysis_question(chat_id)


def send_analysis_question(chat_id):

    analysis = users[chat_id]["analysis"]

    index = analysis["current"]

    if index >= len(ANALYSIS_QUESTIONS):
        finish_analysis(chat_id)
        return

    question = ANALYSIS_QUESTIONS[index]

    keyboard = []

    for i, option in enumerate(question["options"]):

        keyboard.append([
            {
                "text": option,
                "callback_data": f"analysis_{i}"
            }
        ])

    send_message(
        chat_id,
        f"🧬 BAC DNA — التحليل الدراسي\n\n"
        f"📊 السؤال {index + 1}/{len(ANALYSIS_QUESTIONS)}\n\n"
        f"{question['q']}",
        {
            "inline_keyboard": keyboard
        }
    )


def handle_analysis_answer(callback):

    chat_id = callback["message"]["chat"]["id"]

    answer_callback(callback["id"])

    selected = int(
        callback["data"].replace("analysis_", "")
    )

    analysis = users[chat_id]["analysis"]

    index = analysis["current"]

    question = ANALYSIS_QUESTIONS[index]

    scores = question["scores"][selected]

    for category, points in scores.items():

        analysis["scores"][category] += points

    analysis["current"] += 1

    send_analysis_question(chat_id)


def finish_analysis(chat_id):

    scores = users[chat_id]["analysis"]["scores"]

    send_message(
        chat_id,
        "🧬 جاري تحليل ملفك الدراسي...\n\n"
        "🧠 تحليل طريقة تفكيرك...\n"
        "📚 دراسة أسلوب مراجعتك...\n"
        "📊 اكتشاف نقاط القوة...\n"
        "🎯 تحديد نقاط التطوير...\n\n"
        "⏳ يتم تجهيز النتيجة..."
    )

    names = {
        "focus": "⏰ التركيز",
        "organization": "📅 التنظيم",
        "persistence": "🔥 المثابرة",
        "analysis": "🧠 التحليل",
        "confidence": "💪 الثقة الدراسية"
    }

    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)

    def stars(value):

        if value >= 12:
            return "⭐⭐⭐⭐⭐"

        elif value >= 9:
            return "⭐⭐⭐⭐"

        elif value >= 6:
            return "⭐⭐⭐"

        elif value >= 3:
            return "⭐⭐"

        return "⭐"

    result = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BAC DNA — النتيجة\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for category, value in scores.items():

        result += (
            f"{names[category]}: "
            f"{stars(value)}\n"
        )

    result += (
        "\n━━━━━━━━━━━━━━━━━━\n\n"
        f"💪 أقوى نقطة لديك:\n"
        f"{names[strongest]}\n\n"
        f"⚠️ الجانب الذي يحتاج تطويرًا:\n"
        f"{names[weakest]}\n\n"
        "🎯 نصيحة BacMind DZ:\n"
        "لا تبحث عن الكمال، ابحث عن التقدم كل يوم.\n\n"
        "🚀 أنت قادر على تحقيق نتائج قوية في البكالوريا!"
    )

    users[chat_id]["dna_result"] = result

    send_message(chat_id, result)


# =========================================================
# 📊 الإحصائيات
# =========================================================

def show_stats(chat_id):

    user = users.get(chat_id, {})

    answered = user.get("total_answered", 0)
    correct = user.get("total_correct", 0)

    percentage = (
        round(correct / answered * 100)
        if answered > 0
        else 0
    )

    stars = "⭐" * user.get("star_level", 0)

    send_message(
        chat_id,
        f"📊 مستواك الدراسي\n\n"
        f"📝 الأسئلة المجاب عنها: {answered}\n"
        f"✅ الإجابات الصحيحة: {correct}\n"
        f"📈 نسبة النجاح: {percentage}%\n"
        f"🔥 أفضل سلسلة: {user.get('best_streak', 0)}\n"
        f"🏆 المستوى: {stars or 'لم تحصل على نجمة بعد'}"
    )


# =========================================================
# 🏆 الإنجازات
# =========================================================

def achievements(chat_id):

    user = users.get(chat_id, {})

    answered = user.get("total_answered", 0)
    badges = []

    if answered >= 10:
        badges.append("🎯 بداية قوية")

    if answered >= 30:
        badges.append("⭐ طالب طموح")

    if answered >= 60:
        badges.append("⭐⭐ طالب مجتهد")

    if answered >= 90:
        badges.append("⭐⭐⭐ طالب متميز")

    if answered >= 120:
        badges.append("⭐⭐⭐⭐ طالب متفوق")

    if answered >= 150:
        badges.append("⭐⭐⭐⭐⭐ طالب قوي وذكي")

    if not badges:
        badges.append("🔒 ابدأ الاختبارات للحصول على الإنجازات")

    send_message(
        chat_id,
        "🏆 إنجازاتك:\n\n" +
        "\n".join(badges)
    )


# =========================================================
# 🧮 حساب المعدل
# =========================================================

def start_average(chat_id):

    users.setdefault(chat_id, {})

    users[chat_id]["mode"] = "average"

    send_message(
        chat_id,
        "🧮 حاسبة المعدل\n\n"
        "أرسل علاماتك بهذا الشكل:\n\n"
        "14 12 16 10 15\n\n"
        "وسيحسب البوت المعدل البسيط."
    )


def calculate_average(chat_id, text):

    try:

        numbers = [
            float(x.replace(",", "."))
            for x in text.split()
        ]

        if not numbers:
            raise ValueError

        average = sum(numbers) / len(numbers)

        users[chat_id]["mode"] = None

        send_message(
            chat_id,
            f"🧮 النتيجة:\n\n"
            f"📊 المعدل = {average:.2f}/20\n\n"
            "🎯 يمكنك تحسينه أكثر مع العمل المنتظم!"
        )

    except Exception:

        send_message(
            chat_id,
            "❌ صيغة غير صحيحة.\n\n"
            "مثال:\n"
            "14 12 16 10 15"
        )


# =========================================================
# 🎭 نتيجة تجريبية للمزاح
# =========================================================

def start_fake_result(chat_id):

    users.setdefault(chat_id, {})

    users[chat_id]["mode"] = "fake_name"

    send_message(
        chat_id,
        "🎭 نتيجة البكالوريا التجريبية\n\n"
        "⚠️ هذه فقرة للمزاح والترفيه فقط وليست نتيجة رسمية.\n\n"
        "أرسل الاسم واللقب:"
    )


def fake_result_step(chat_id, text):

    user = users[chat_id]

    mode = user.get("mode")

    if mode == "fake_name":

        user["fake_name"] = text
        user["mode"] = "fake_number"

        send_message(
            chat_id,
            "📝 الآن أرسل رقم تسجيل وهمي أو أي رقم للتجربة 😄"
        )

        return

    if mode == "fake_number":

        user["fake_number"] = text
        user["mode"] = None

        send_message(
            chat_id,
            "⏳ جاري البحث عن النتيجة...\n\n"
            "🔍 تحليل البيانات...\n"
            "📚 مراجعة النقاط...\n"
            "🧮 حساب المعدل..."
        )

        fake_average = round(
            random.uniform(10.0, 18.9),
            2
        )

        messages = [
            "🔥 نتيجة جميلة! استمر في العمل.",
            "🚀 لديك مستقبل قوي إذا واصلت الاجتهاد.",
            "⭐ مجهودك يظهر في النتيجة!",
            "💪 القادم سيكون أفضل وأقوى."
        ]

        send_message(
            chat_id,
            f"🎓 النتيجة التجريبية\n\n"
            f"👤 الاسم: {user['fake_name']}\n"
            f"📝 الرقم: {user['fake_number']}\n\n"
            f"📊 المعدل الوهمي: {fake_average}/20\n\n"
            f"{random.choice(messages)}\n\n"
            "⚠️ تذكير: هذه نتيجة عشوائية للترفيه وليست نتيجة بكالوريا حقيقية."
        )


# =========================================================
# 📄 ملفات PDF
# =========================================================

def pdf_topics(chat_id):

    send_message(
        chat_id,
        "📄 مكتبة مواضيع البكالوريا\n\n"
        "🧠 فلسفة\n"
        "🇫🇷 لغة فرنسية\n"
        "🇬🇧 لغة إنجليزية\n"
        "🇪🇸 لغة إسبانية\n\n"
        "📌 يمكنك لاحقًا إضافة روابط PDF حقيقية داخل الكود."
    )


# =========================================================
# المساعدة
# =========================================================

def help_message(chat_id):

    send_message(
        chat_id,
        "ℹ️ مرحبًا بك في BacMind DZ 🎓🇩🇿\n\n"
        "🧠 اختبر نفسك في المواد.\n"
        "🧬 اكتشف شخصيتك الدراسية.\n"
        "🧮 احسب معدلك.\n"
        "🎭 جرب النتيجة الترفيهية.\n"
        "📄 تصفح مكتبة المواضيع.\n"
        "📊 تابع تقدمك.\n"
        "🏆 اجمع النجوم والإنجازات.\n\n"
        "🚀 هدفنا: طالب أقوى كل يوم."
    )


# =========================================================
# Flask
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "🎓 BacMind DZ is running!"


@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True) or {}

    # =====================================================
    # CALLBACK
    # =====================================================

    callback = data.get("callback_query")

    if callback:

        callback_data = callback.get("data", "")

        chat_id = callback["message"]["chat"]["id"]

        if callback_data.startswith("quiz_"):

            handle_quiz_answer(callback)

        elif callback_data == "next_question":

            answer_callback(callback["id"])
            handle_next_question(chat_id)

        elif callback_data.startswith("analysis_"):

            handle_analysis_answer(callback)

        return "OK"

    # =====================================================
    # MESSAGE
    # =====================================================

    message = data.get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    text = message.get("text", "").strip()

    if not chat_id:
        return "OK"

    users.setdefault(chat_id, {})

    # =====================================================
    # أوضاع خاصة
    # =====================================================

    mode = users[chat_id].get("mode")

    if mode == "average":

        calculate_average(chat_id, text)
        return "OK"

    if mode in ["fake_name", "fake_number"]:

        fake_result_step(chat_id, text)
        return "OK"

    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        users[chat_id] = {
            "total_answered": 0,
            "total_correct": 0,
            "star_level": 0
        }

        send_message(
            chat_id,
            "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"
            "✨ منصة تعليمية وتحفيزية مخصصة لـ:\n\n"
            "🧠 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n\n"
            "🚀 تدرب اليوم... وتألق في البكالوريا غدًا!",
            main_keyboard()
        )

        return "OK"

    # =====================================================
    # المواد
    # =====================================================

    if text == "🧠 الفلسفة":

        start_quiz(chat_id, "الفلسفة")
        return "OK"

    if text == "🇫🇷 الفرنسية":

        start_quiz(chat_id, "الفرنسية")
        return "OK"

    if text == "🇬🇧 الإنجليزية":

        start_quiz(chat_id, "الإنجليزية")
        return "OK"

    if text == "🇪🇸 الإسبانية":

        start_quiz(chat_id, "الإسبانية")
        return "OK"

    # =====================================================
    # التحليل
    # =====================================================

    if text == "🧬 تحليل مستواي الدراسي":

        start_analysis(chat_id)
        return "OK"

    # =====================================================
    # المعدل
    # =====================================================

    if text == "🧮 حساب المعدل":

        start_average(chat_id)
        return "OK"

    # =====================================================
    # النتيجة التجريبية
    # =====================================================

    if text == "🎭 نتيجة بكالوريا تجريبية":

        start_fake_result(chat_id)
        return "OK"

    # =====================================================
    # PDF
    # =====================================================

    if text == "📄 مواضيع PDF":

        pdf_topics(chat_id)
        return "OK"

    # =====================================================
    # الإحصائيات
    # =====================================================

    if text == "📊 مستواي":

        show_stats(chat_id)
        return "OK"

    if text == "🏆 الإنجازات":

        achievements(chat_id)
        return "OK"

    # =====================================================
    # المساعدة
    # =====================================================

    if text == "ℹ️ المساعدة":

        help_message(chat_id)
        return "OK"

    send_message(
        chat_id,
        "🤖 لم أفهم طلبك.\n\n"
        "استخدم القائمة أو اكتب /start."
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
