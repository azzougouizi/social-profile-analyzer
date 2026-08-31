import os
import random
import time
import threading
import requests

from flask import Flask, request

# =========================================================
# BacMind DZ
# بوت بكالوريا لشعبتي:
# - آداب وفلسفة
# - لغات أجنبية
# =========================================================

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN غير موجود في Environment Variables")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

# =========================================================
# تخزين المستخدمين
# =========================================================

users = {}

# =========================================================
# بنك الأسئلة
# =========================================================
# ملاحظة:
# يمكنك إضافة المزيد بنفس الشكل.
# كل مادة يمكن أن تحتوي على عشرات أو مئات الأسئلة.
# =========================================================

QUESTIONS = {

    "الفلسفة": [

        {
            "q": "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            "answer": 2,
            "explanation": "المقولة تعود إلى رينيه ديكارت."
        },

        {
            "q": "ما المقصود بالفلسفة؟",
            "options": [
                "حفظ المعلومات فقط",
                "حب الحكمة والبحث العقلي",
                "دراسة الأرقام",
                "دراسة الطبيعة فقط"
            ],
            "answer": 1,
            "explanation": "الفلسفة تعني حب الحكمة والبحث العقلي والنقدي."
        },

        {
            "q": "من صاحب نظرية المثل؟",
            "options": ["أفلاطون", "ديكارت", "كانط", "نيتشه"],
            "answer": 0,
            "explanation": "نظرية المثل مرتبطة بأفلاطون."
        },

        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": ["سقراط", "أرسطو", "ديكارت", "هيغل"],
            "answer": 1,
            "explanation": "القول منسوب إلى أرسطو."
        },

        {
            "q": "ما المقصود بالمنطق؟",
            "options": [
                "علم التفكير الصحيح",
                "علم التاريخ",
                "علم اللغة",
                "علم الفن"
            ],
            "answer": 0,
            "explanation": "المنطق يهتم بقواعد التفكير والاستدلال الصحيح."
        },

        {
            "q": "من الفيلسوف المرتبط بالشك المنهجي؟",
            "options": ["أرسطو", "ديكارت", "أفلاطون", "ماركس"],
            "answer": 1,
            "explanation": "استخدم ديكارت الشك المنهجي للوصول إلى اليقين."
        },

        {
            "q": "ما المقصود بالحرية؟",
            "options": [
                "فعل أي شيء دون مسؤولية",
                "القدرة على الاختيار وتحمل المسؤولية",
                "رفض جميع القوانين",
                "عدم التفكير"
            ],
            "answer": 1,
            "explanation": "الحرية ترتبط بالاختيار والمسؤولية."
        },

        {
            "q": "من الفيلسوف الذي ربط الأخلاق بالواجب؟",
            "options": ["كانط", "أفلاطون", "أرسطو", "سقراط"],
            "answer": 0,
            "explanation": "كانط من أبرز الفلاسفة المرتبطين بأخلاق الواجب."
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
            "explanation": "من التصورات الكلاسيكية للحقيقة مطابقة الحكم للواقع."
        },

        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            "answer": 0,
            "explanation": "الجمهورية من أشهر مؤلفات أفلاطون."
        },

        {
            "q": "ما الهدف من التفكير النقدي؟",
            "options": [
                "رفض كل شيء",
                "تحليل الأفكار والأدلة",
                "حفظ النصوص",
                "تجنب الأسئلة"
            ],
            "answer": 1,
            "explanation": "التفكير النقدي يعتمد على تحليل الأفكار وفحص الأدلة."
        },

        {
            "q": "ما المجال الذي يدرس المعرفة؟",
            "options": [
                "الإبستمولوجيا",
                "الجماليات",
                "الاقتصاد",
                "الرياضة"
            ],
            "answer": 0,
            "explanation": "الإبستمولوجيا تهتم بالمعرفة ومصادرها وحدودها."
        },

        {
            "q": "من أشهر فلاسفة اليونان القديمة؟",
            "options": ["سقراط", "ديكارت", "كانط", "هيغل"],
            "answer": 0,
            "explanation": "سقراط من أبرز فلاسفة اليونان القديمة."
        },

        {
            "q": "ما المقصود بالأخلاق؟",
            "options": [
                "دراسة السلوك والقيم",
                "دراسة الحساب",
                "دراسة الطقس",
                "دراسة الجغرافيا"
            ],
            "answer": 0,
            "explanation": "الأخلاق تبحث في القيم والمعايير التي توجه السلوك."
        },

        {
            "q": "ما الذي تدرسه الجماليات؟",
            "options": [
                "الجمال والفن",
                "الرياضيات",
                "الطقس",
                "الاقتصاد"
            ],
            "answer": 0,
            "explanation": "الجماليات أو علم الجمال تهتم بالفن والجمال."
        },

        {
            "q": "من الفيلسوف المرتبط بفكرة العقد الاجتماعي؟",
            "options": [
                "روسو",
                "أفلاطون",
                "أرسطو",
                "سقراط"
            ],
            "answer": 0,
            "explanation": "جان جاك روسو من أشهر فلاسفة العقد الاجتماعي."
        },

        {
            "q": "ما الفرق بين الرأي والمعرفة؟",
            "options": [
                "لا يوجد فرق",
                "المعرفة تقوم على تبرير وأدلة",
                "الرأي دائمًا صحيح",
                "المعرفة مجرد تخمين"
            ],
            "answer": 1,
            "explanation": "المعرفة تتطلب تبريرًا وأساسًا معرفيًا أقوى من مجرد الرأي."
        },

        {
            "q": "ما المقصود بالاستدلال؟",
            "options": [
                "الانتقال من مقدمات إلى نتيجة",
                "حفظ النصوص",
                "الخيال",
                "الوصف"
            ],
            "answer": 0,
            "explanation": "الاستدلال انتقال عقلي من مقدمات إلى نتيجة."
        },

        {
            "q": "من الفيلسوف الذي اشتهر بمفهوم العود الأبدي؟",
            "options": ["نيتشه", "كانط", "ديكارت", "لوك"],
            "answer": 0,
            "explanation": "العود الأبدي من الأفكار المرتبطة بنيتشه."
        },

        {
            "q": "ما المقصود بالوعي؟",
            "options": [
                "إدراك الإنسان لذاته وما يحيط به",
                "النوم",
                "النسيان",
                "الخيال فقط"
            ],
            "answer": 0,
            "explanation": "الوعي يرتبط بالإدراك والشعور بالذات والعالم."
        },

        {
            "q": "من الفيلسوف الذي اشتهر بعبارة اعرف نفسك؟",
            "options": ["سقراط", "كانط", "هيغل", "ماركس"],
            "answer": 0,
            "explanation": "ارتبطت العبارة بالفكر السقراطي."
        }

    ],

    # =====================================================
    # الفرنسية
    # =====================================================

    "الفرنسية": [

        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": ["Triste", "Content", "Malade", "Fatigué"],
            "answer": 1,
            "explanation": "Heureux et content ont un sens proche."
        },

        {
            "q": "Quel est le contraire de « difficile » ?",
            "options": ["Compliqué", "Facile", "Long", "Fort"],
            "answer": 1,
            "explanation": "Le contraire de difficile est facile."
        },

        {
            "q": "Complétez : Je ___ au lycée.",
            "options": ["vais", "va", "allons", "allez"],
            "answer": 0,
            "explanation": "Avec je, on dit je vais."
        },

        {
            "q": "Quel est le pluriel de « cheval » ?",
            "options": ["Chevals", "Chevaux", "Chevales", "Chevaus"],
            "answer": 1,
            "explanation": "Le pluriel de cheval est chevaux."
        },

        {
            "q": "« J'ai étudié » est à quel temps ?",
            "options": ["Présent", "Futur", "Passé composé", "Imparfait"],
            "answer": 2,
            "explanation": "J'ai étudié est au passé composé."
        },

        {
            "q": "Complétez : Nous ___ nos devoirs.",
            "options": ["fait", "faisons", "faites", "faire"],
            "answer": 1,
            "explanation": "Avec nous, on dit nous faisons."
        },

        {
            "q": "Quel mot est un adjectif ?",
            "options": ["Rapidement", "Maison", "Intelligent", "Courir"],
            "answer": 2,
            "explanation": "Intelligent est un adjectif."
        },

        {
            "q": "Quel est le féminin de « acteur » ?",
            "options": ["Acteuse", "Actrice", "Acteure", "Acteurs"],
            "answer": 1,
            "explanation": "Le féminin de acteur est actrice."
        },

        {
            "q": "Si j'avais le temps, je ___ davantage.",
            "options": ["lis", "lirais", "lirai", "lu"],
            "answer": 1,
            "explanation": "Après si + imparfait, on utilise ici le conditionnel."
        },

        {
            "q": "Quel est le contraire de « ancien » ?",
            "options": ["Vieux", "Moderne", "Passé", "Historique"],
            "answer": 1,
            "explanation": "Dans ce contexte, le contraire est moderne."
        },

        {
            "q": "Quel est le contraire de « rapide » ?",
            "options": ["Lent", "Fort", "Grand", "Beau"],
            "answer": 0,
            "explanation": "Le contraire de rapide est lent."
        },

        {
            "q": "Complétez : Ils ___ au marché.",
            "options": ["va", "vont", "aller", "allez"],
            "answer": 1,
            "explanation": "Avec ils, le verbe aller devient vont."
        },

        {
            "q": "Quel mot signifie « école » ?",
            "options": ["École", "Maison", "Rue", "Livre"],
            "answer": 0,
            "explanation": "École signifie مدرسة."
        },

        {
            "q": "Quel est le participe passé de « prendre » ?",
            "options": ["Pris", "Prendu", "Prenait", "Prendre"],
            "answer": 0,
            "explanation": "Le participe passé de prendre est pris."
        },

        {
            "q": "Quel est le contraire de « jeune » ?",
            "options": ["Petit", "Vieux", "Fort", "Nouveau"],
            "answer": 1,
            "explanation": "Le contraire de jeune est vieux."
        }

    ],

    # =====================================================
    # الإنجليزية
    # =====================================================

    "الإنجليزية": [

        {
            "q": "Choose the correct answer: She ___ English every day.",
            "options": ["study", "studies", "studying", "studied"],
            "answer": 1,
            "explanation": "With she, the present simple takes -s or -es."
        },

        {
            "q": "What is the past tense of go?",
            "options": ["goed", "gone", "went", "going"],
            "answer": 2,
            "explanation": "The past simple of go is went."
        },

        {
            "q": "Choose the correct sentence.",
            "options": [
                "I is a student.",
                "I am a student.",
                "I are a student.",
                "I be a student."
            ],
            "answer": 1,
            "explanation": "With I, the correct form is am."
        },

        {
            "q": "What is the opposite of easy?",
            "options": ["Simple", "Hard", "Short", "Small"],
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
            "explanation": "Use doesn't + base verb with he/she/it."
        },

        {
            "q": "What is the comparative form of good?",
            "options": ["Gooder", "More good", "Better", "Best"],
            "answer": 2,
            "explanation": "The comparative of good is better."
        },

        {
            "q": "They ___ playing now.",
            "options": ["is", "am", "are", "be"],
            "answer": 2,
            "explanation": "With they, use are in the present continuous."
        },

        {
            "q": "What does environment mean?",
            "options": ["البيئة", "الاقتصاد", "الرياضة", "التاريخ"],
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
            "explanation": "The past participle of write is written."
        },

        {
            "q": "Choose: We ___ students.",
            "options": ["is", "am", "are", "be"],
            "answer": 2,
            "explanation": "With we, use are."
        },

        {
            "q": "What is the opposite of expensive?",
            "options": ["Cheap", "Large", "Rich", "Fast"],
            "answer": 0,
            "explanation": "The opposite of expensive is cheap."
        },

        {
            "q": "Choose: I ___ my homework yesterday.",
            "options": ["do", "did", "does", "doing"],
            "answer": 1,
            "explanation": "Yesterday requires the past simple: did."
        },

        {
            "q": "What is the plural of child?",
            "options": ["Childs", "Children", "Childes", "Childrens"],
            "answer": 1,
            "explanation": "The plural of child is children."
        },

        {
            "q": "Choose: If I had money, I ___ a car.",
            "options": ["buy", "bought", "would buy", "will buy"],
            "answer": 2,
            "explanation": "Second conditional uses would + base verb."
        }

    ],

    # =====================================================
    # الإسبانية
    # =====================================================

    "الإسبانية": [

        {
            "q": "¿Cómo se dice « مرحبا » en español?",
            "options": ["Adiós", "Hola", "Gracias", "Por favor"],
            "answer": 1,
            "explanation": "Hola significa مرحبًا."
        },

        {
            "q": "¿Qué significa gracias?",
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
            "q": "¿Cómo se dice كتاب en español?",
            "options": ["Mesa", "Casa", "Libro", "Escuela"],
            "answer": 2,
            "explanation": "Libro significa كتاب."
        },

        {
            "q": "¿Cómo se dice « صباح الخير »?",
            "options": ["Buenas noches", "Buenos días", "Adiós", "Gracias"],
            "answer": 1,
            "explanation": "Buenos días significa صباح الخير."
        },

        {
            "q": "¿Qué significa casa?",
            "options": ["بيت", "مدرسة", "كتاب", "شارع"],
            "answer": 0,
            "explanation": "Casa significa بيت."
        },

        {
            "q": "Completa: Nosotros ___ estudiantes.",
            "options": ["soy", "eres", "somos", "son"],
            "answer": 2,
            "explanation": "Con nosotros usamos somos."
        },

        {
            "q": "¿Cuál es el contrario de bueno?",
            "options": ["malo", "grande", "alto", "nuevo"],
            "answer": 0,
            "explanation": "El contrario de bueno es malo."
        },

        {
            "q": "¿Qué significa escuela?",
            "options": ["مدرسة", "بيت", "كتاب", "مدينة"],
            "answer": 0,
            "explanation": "Escuela significa مدرسة."
        }

    ]
}


# =========================================================
# دوال Telegram
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

        if response.status_code == 429:
            print("WARNING: Telegram rate limit 429")

        try:
            return response.json()
        except Exception:
            return None

    except Exception as exc:
        print(f"Telegram error: {exc}")
        return None


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def answer_callback(callback_id):
    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


def edit_message(chat_id, message_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("editMessageText", data)


# =========================================================
# لوحات المفاتيح
# =========================================================

def main_keyboard():
    return {
        "keyboard": [
            ["🧠 الفلسفة"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🇪🇸 الإسبانية"],
            ["📝 الاختبارات"],
            ["🧮 حساب المعدل"],
            ["📄 مواضيع البكالوريا"],
            ["🎭 معدل بكالوريا وهمي"],
            ["📊 مستواي", "🏆 الإنجازات"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


def subject_keyboard():
    return {
        "keyboard": [
            ["🧠 فلسفة"],
            ["🇫🇷 فرنسية"],
            ["🇬🇧 إنجليزية"],
            ["🇪🇸 إسبانية"],
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }


def back_keyboard():
    return {
        "keyboard": [
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# الاختبارات
# =========================================================

def start_quiz(chat_id, subject):
    questions = QUESTIONS.get(subject, [])

    if not questions:
        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة."
        )
        return

    amount = min(10, len(questions))

    selected = random.sample(
        questions,
        amount
    )

    users[chat_id] = {
        "mode": "quiz",
        "subject": subject,
        "questions": selected,
        "current": 0,
        "score": 0,
        "answered": False,
        "streak": 0,
        "best_streak": 0,
        "total_answered": users.get(
            chat_id, {}
        ).get(
            "total_answered",
            0
        )
    }

    send_question(chat_id)


def send_question(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    index = user["current"]
    questions = user["questions"]

    if index >= len(questions):
        finish_quiz(chat_id)
        return

    question = questions[index]

    keyboard = []

    for i, option in enumerate(
        question["options"]
    ):
        keyboard.append([
            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"answer:{i}"
            }
        ])

    send_message(
        chat_id,
        (
            f"📚 {user['subject']}\n\n"
            f"📝 السؤال {index + 1} / "
            f"{len(questions)}\n\n"
            f"❓ {question['q']}"
        ),
        {
            "inline_keyboard": keyboard
        }
    )


def finish_quiz(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    total = len(user["questions"])
    score = user["score"]

    percentage = round(
        score * 100 / total
    ) if total else 0

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage

    if percentage >= 90:
        level = "👑 أسطوري"
    elif percentage >= 80:
        level = "🔥 ممتاز"
    elif percentage >= 70:
        level = "👏 جيد جدًا"
    elif percentage >= 50:
        level = "👍 جيد"
    else:
        level = "💪 تحتاج إلى المزيد من التدريب"

    motivation = get_motivation(percentage)

    send_message(
        chat_id,
        (
            "🎉 انتهى الاختبار!\n\n"
            f"📚 المادة: {user['subject']}\n"
            f"✅ صحيح: {score}\n"
            f"❌ خطأ: {total - score}\n"
            f"📊 النتيجة: {percentage}%\n"
            f"🏆 المستوى: {level}\n"
            f"🔥 أفضل سلسلة: {user['best_streak']}\n\n"
            f"{motivation}"
        ),
        main_keyboard()
    )


def handle_answer(callback):
    callback_id = callback.get("id")
    answer_callback(callback_id)

    data = callback.get("data", "")

    if not data.startswith("answer:"):
        return

    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    message_id = message.get("message_id")

    user = users.get(chat_id)

    if not user:
        return

    if user.get("answered"):
        return

    try:
        selected = int(
            data.split(":", 1)[1]
        )
    except Exception:
        return

    index = user["current"]

    if index >= len(user["questions"]):
        return

    question = user["questions"][index]
    correct = question["answer"]

    user["answered"] = True
    user["total_answered"] = (
        user.get("total_answered", 0) + 1
    )

    if selected == correct:
        user["score"] += 1
        user["streak"] += 1

        user["best_streak"] = max(
            user["best_streak"],
            user["streak"]
        )

        result = (
            "✅ إجابة صحيحة!\n\n"
            f"🔥 السلسلة الحالية: "
            f"{user['streak']}"
        )

    else:
        user["streak"] = 0

        result = (
            "❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة: "
            f"{question['options'][correct]}"
        )

    result += (
        f"\n\n💡 الشرح:\n"
        f"{question['explanation']}"
    )

    edit_message(
        chat_id,
        message_id,
        result,
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


def handle_next(callback):
    callback_id = callback.get("id")
    answer_callback(callback_id)

    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    user = users.get(chat_id)

    if not user:
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


# =========================================================
# التحفيز
# =========================================================

def get_motivation(percentage):
    if percentage >= 90:
        return "👑 رائع! أنت قريب جدًا من مستوى ممتاز في البكالوريا."
    if percentage >= 80:
        return "🔥 ممتاز! استمر بنفس القوة."
    if percentage >= 70:
        return "👏 تقدم جميل، لا تتوقف."
    if percentage >= 50:
        return "💪 لديك أساس جيد، والمزيد من التدريب سيرفع نتيجتك."
    return "🌱 لا تستسلم. كل سؤال تخطئ فيه هو فرصة لتتعلم."


# =========================================================
# النجوم والإنجازات
# =========================================================

def get_star_level(answered):
    if answered >= 250:
        return 5, "👑 طالب قوي وذكي"
    if answered >= 200:
        return 4, "🔥 طالب متفوق"
    if answered >= 150:
        return 3, "⭐ طالب مجتهد"
    if answered >= 100:
        return 2, "👏 طالب نشيط"
    if answered >= 30:
        return 1, "🎯 طالب طموح"

    return 0, "🌱 البداية فقط"


def show_achievements(chat_id):
    user = users.get(chat_id, {})

    answered = user.get(
        "total_answered",
        0
    )

    stars, title = get_star_level(
        answered
    )

    star_text = (
        "⭐" * stars
        if stars
        else "🔒 لا توجد نجوم بعد"
    )

    send_message(
        chat_id,
        (
            "🏆 إنجازاتك\n\n"
            f"📝 عدد الإجابات: {answered}\n"
            f"⭐ المستوى: {star_text}\n"
            f"🎖️ اللقب: {title}\n\n"
            "🎯 30 إجابة = طالب طموح\n"
            "👏 100 إجابة = طالب نشيط\n"
            "⭐ 150 إجابة = طالب مجتهد\n"
            "🔥 200 إجابة = طالب متفوق\n"
            "👑 250 إجابة = طالب قوي وذكي"
        )
    )


# =========================================================
# المستوى
# =========================================================

def show_stats(chat_id):
    user = users.get(chat_id, {})

    answered = user.get(
        "total_answered",
        0
    )

    stars, title = get_star_level(
        answered
    )

    if "last_percentage" not in user:
        last = "لا توجد نتيجة اختبار بعد."
    else:
        last = (
            f"{user['last_percentage']}% "
            f"({user['last_score']}/"
            f"{user['last_total']})"
        )

    send_message(
        chat_id,
        (
            "📊 مستواك\n\n"
            f"📝 إجاباتك: {answered}\n"
            f"⭐ النجوم: {'⭐' * stars if stars else '0'}\n"
            f"🏆 اللقب: {title}\n"
            f"📈 آخر نتيجة: {last}\n"
            f"🔥 أفضل سلسلة: "
            f"{user.get('best_streak', 0)}"
        )
    )


# =========================================================
# حساب المعدل
# =========================================================

# هذه القيم موضوعة في مكان واحد ليسهل تعديلها.
# إذا أردت تغيير المعاملات لاحقًا، غيّر هذا القسم فقط.

COEFFICIENTS = {
    "آداب وفلسفة": {
        "اللغة العربية": 5,
        "الفلسفة": 6,
        "التاريخ والجغرافيا": 4,
        "اللغة الفرنسية": 3,
        "اللغة الإنجليزية": 3,
        "العلوم الإسلامية": 2,
        "الرياضيات": 2,
        "التربية البدنية": 1,
        "الأمازيغية": 2,
    },

    "لغات أجنبية": {
        "اللغة العربية": 5,
        "اللغة الفرنسية": 5,
        "اللغة الإنجليزية": 5,
        "اللغة الأجنبية الثالثة": 4,
        "التاريخ والجغرافيا": 4,
        "الفلسفة": 2,
        "العلوم الإسلامية": 2,
        "الرياضيات": 2,
        "التربية البدنية": 1,
        "الأمازيغية": 2,
    }
}


def start_average(chat_id):
    users[chat_id] = {
        "mode": "average_select"
    }

    keyboard = {
        "keyboard": [
            ["📚 آداب وفلسفة"],
            ["🌍 لغات أجنبية"],
            ["🔙 القائمة الرئيسية"]
        ],
        "resize_keyboard": True
    }

    send_message(
        chat_id,
        "🧮 اختر شعبتك لحساب المعدل:",
        keyboard
    )


def start_average_input(chat_id, branch):
    subjects = list(
        COEFFICIENTS[branch].keys()
    )

    users[chat_id] = {
        "mode": "average",
        "branch": branch,
        "subjects": subjects,
        "index": 0,
        "grades": {}
    }

    ask_next_grade(chat_id)


def ask_next_grade(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    subjects = user["subjects"]
    index = user["index"]

    if index >= len(subjects):
        calculate_average(chat_id)
        return

    subject = subjects[index]
    coefficient = COEFFICIENTS[
        user["branch"]
    ][subject]

    send_message(
        chat_id,
        (
            f"🧮 المادة {index + 1}/"
            f"{len(subjects)}\n\n"
            f"📚 {subject}\n"
            f"🔢 المعامل: {coefficient}\n\n"
            "أرسل النقطة من 0 إلى 20."
        ),
        back_keyboard()
    )


def calculate_average(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    branch = user["branch"]
    grades = user["grades"]

    total = 0
    coefficients = 0

    for subject, grade in grades.items():
        coefficient = COEFFICIENTS[
            branch
        ][subject]

        total += grade * coefficient
        coefficients += coefficient

    average = (
        total / coefficients
        if coefficients
        else 0
    )

    if average >= 16:
        level = "👑 ممتاز جدًا"
    elif average >= 14:
        level = "🔥 ممتاز"
    elif average >= 12:
        level = "👏 جيد جدًا"
    elif average >= 10:
        level = "✅ ناجح"
    else:
        level = "💪 تحتاج إلى المزيد من العمل"

    send_message(
        chat_id,
        (
            "🧮 نتيجة حساب المعدل\n\n"
            f"📚 الشعبة: {branch}\n"
            f"📊 المعدل: {average:.2f}/20\n"
            f"🏆 التقييم: {level}\n\n"
            "💡 هذه حاسبة تدريبية وليست نتيجة رسمية."
        ),
        main_keyboard()
    )

    user["last_average"] = average
    user["mode"] = "main"


# =========================================================
# معدل بكالوريا وهمي
# =========================================================

def start_fake_result(chat_id):
    users[chat_id] = {
        "mode": "fake_name"
    }

    send_message(
        chat_id,
        (
            "😂 🎭 معدل بكالوريا وهمي\n\n"
            "سنقوم بإنشاء نتيجة ترفيهية لك.\n\n"
            "👤 أرسل الاسم واللقب.\n\n"
            "⚠️ لا ترسل اسمًا حقيقيًا إذا كنت لا تريد ذلك."
        ),
        back_keyboard()
    )


def process_fake_name(chat_id, text):
    users[chat_id]["fake_name"] = text
    users[chat_id]["mode"] = "fake_number"

    send_message(
        chat_id,
        (
            "✅ تم استلام الاسم.\n\n"
            "🔢 الآن أرسل رقم تسجيل وهمي، "
            "مثال: 123456\n\n"
            "⚠️ لا ترسل رقم تسجيل حقيقي."
        ),
        back_keyboard()
    )


def process_fake_number(chat_id, text):
    user = users[chat_id]

    user["fake_number"] = text
    user["mode"] = "main"

    send_message(
        chat_id,
        (
            "⏳ انتظر قليلًا...\n\n"
            "🔎 جارٍ تجهيز النتيجة...\n"
            "📊 جارٍ حساب المعدل...\n"
            "🎓 جارٍ إعداد النتيجة..."
        )
    )

    # نرسل النتيجة في Thread حتى لا نوقف webhook
    threading.Thread(
        target=send_fake_result,
        args=(chat_id,),
        daemon=True
    ).start()


def send_fake_result(chat_id):
    time.sleep(3)

    user = users.get(chat_id)

    if not user:
        return

    average = round(
        random.uniform(9.50, 19.75),
        2
    )

    if average >= 18:
        title = "👑 عبقري البكالوريا"
        joke = "😂 الجامعة بدأت تبحث عنك!"
    elif average >= 16:
        title = "🔥 ممتاز جدًا"
        joke = "😎 الأستاذ بدأ يشك أنك تخفي شيئًا!"
    elif average >= 14:
        title = "👏 ممتاز"
        joke = "😂 الوالدة بدأت تحضر للحلوى!"
    elif average >= 12:
        title = "😎 ناجح ومطمئن"
        joke = "🔥 شد حيلك وستصل للأعلى!"
    elif average >= 10:
        title = "😅 ناجح بصعوبة"
        joke = "😂 المهم وصلت للضفة!"
    else:
        title = "💪 تحتاج إلى إعادة المحاولة"
        joke = "😂 حتى الحظ يحتاج إلى مراجعة!"

    send_message(
        chat_id,
        (
            "🎓 نتيجة المحاكاة جاهزة!\n\n"
            f"👤 الاسم: {user.get('fake_name', '-')}\n"
            f"🔢 رقم التسجيل الوهمي: "
            f"{user.get('fake_number', '-')}\n\n"
            f"📊 المعدل الوهمي: "
            f"{average:.2f}/20\n"
            f"🏆 التقدير: {title}\n\n"
            f"{joke}\n\n"
            "⚠️ هذه نتيجة وهمية للترفيه والمزاح فقط، "
            "وليست نتيجة بكالوريا رسمية."
        ),
        main_keyboard()
    )


# =========================================================
# مواضيع البكالوريا
# =========================================================

def show_bac_topics(chat_id):
    send_message(
        chat_id,
        (
            "📄 مواضيع البكالوريا\n\n"
            "سنضيف ملفات PDF هنا حسب:\n\n"
            "📚 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n\n"
            "⚠️ لا توجد ملفات PDF مرفوعة حاليًا."
        )
    )


# =========================================================
# المساعدة
# =========================================================

def show_help(chat_id):
    send_message(
        chat_id,
        (
            "ℹ️ طريقة استخدام BacMind DZ\n\n"
            "📝 الاختبارات:\n"
            "اختر المادة وأجب عن الأسئلة.\n\n"
            "⭐ الإنجازات:\n"
            "كلما أجبت عن أسئلة أكثر ترتفع نجومك.\n\n"
            "🧮 حساب المعدل:\n"
            "أدخل نقاطك ليحسب البوت المعدل التدريبي.\n\n"
            "🎭 المعدل الوهمي:\n"
            "قسم ترفيهي فقط.\n\n"
            "📄 مواضيع البكالوريا:\n"
            "قسم مخصص لملفات PDF."
        )
    )


# =========================================================
# استقبال Telegram Webhook
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "🎓 BacMind DZ is running!"


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/telegram/webhook", methods=["POST"])
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    # -----------------------------------------------------
    # Callback Query
    # -----------------------------------------------------

    callback = data.get("callback_query")

    if callback:

        callback_data = callback.get(
            "data",
            ""
        )

        if callback_data == "next_question":
            handle_next(callback)
        else:
            handle_answer(callback)

        return "OK"

    # -----------------------------------------------------
    # Message
    # -----------------------------------------------------

    message = data.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get("id")

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:
        return "OK"

    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    if text == "/start":

        users[chat_id] = {
            "mode": "main",
            "total_answered": 0
        }

        send_message(
            chat_id,
            (
                "🎓 أهلاً بك في BacMind DZ 🇩🇿\n\n"
                "البوت المخصص لمساعدة طلاب:\n"
                "📚 آداب وفلسفة\n"
                "🌍 لغات أجنبية\n\n"
                "🚀 اختبر نفسك، احسب معدلك، "
                "واجمع النجوم!"
            ),
            main_keyboard()
        )

        return "OK"

    # -----------------------------------------------------
    # رجوع
    # -----------------------------------------------------

    if text == "🔙 القائمة الرئيسية":

        old = users.get(chat_id, {})

        users[chat_id] = {
            "mode": "main",
            "total_answered": old.get(
                "total_answered",
                0
            ),
            "best_streak": old.get(
                "best_streak",
                0
            )
        }

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_keyboard()
        )

        return "OK"

    # -----------------------------------------------------
    # معالجة الأوضاع الخاصة
    # -----------------------------------------------------

    user = users.get(chat_id, {})

    mode = user.get(
        "mode",
        "main"
    )

    if mode == "fake_name":
        process_fake_name(
            chat_id,
            text
        )
        return "OK"

    if mode == "fake_number":
        process_fake_number(
            chat_id,
            text
        )
        return "OK"

    if mode == "average":

        try:
            grade = float(
                text.replace(",", ".")
            )

            if grade < 0 or grade > 20:
                raise ValueError

        except ValueError:

            send_message(
                chat_id,
                "❌ أرسل نقطة صحيحة بين 0 و20."
            )

            return "OK"

        subject = user["subjects"][
            user["index"]
        ]

        user["grades"][subject] = grade
        user["index"] += 1

        ask_next_grade(chat_id)

        return "OK"

    # -----------------------------------------------------
    # القوائم
    # -----------------------------------------------------

    if text == "📝 الاختبارات":

        send_message(
            chat_id,
            "📝 اختر المادة:",
            subject_keyboard()
        )

        return "OK"

    if text == "🧠 الفلسفة":

        send_message(
            chat_id,
            "🧠 اختبار الفلسفة:",
            {
                "keyboard": [
                    ["▶️ ابدأ اختبار الفلسفة"],
                    ["🔙 القائمة الرئيسية"]
                ],
                "resize_keyboard": True
            }
        )

        return "OK"

    if text == "▶️ ابدأ اختبار الفلسفة":

        start_quiz(
            chat_id,
            "الفلسفة"
        )

        return "OK"

    if text == "🇫🇷 الفرنسية":

        send_message(
            chat_id,
            "🇫🇷 اختبار الفرنسية:",
            {
                "keyboard": [
                    ["▶️ ابدأ اختبار الفرنسية"],
                    ["🔙 القائمة الرئيسية"]
                ],
                "resize_keyboard": True
            }
        )

        return "OK"

    if text == "▶️ ابدأ اختبار الفرنسية":

        start_quiz(
            chat_id,
            "الفرنسية"
        )

        return "OK"

    if text == "🇬🇧 الإنجليزية":

        send_message(
            chat_id,
            "🇬🇧 اختبار الإنجليزية:",
            {
                "keyboard": [
                    ["▶️ ابدأ اختبار الإنجليزية"],
                    ["🔙 القائمة الرئيسية"]
                ],
                "resize_keyboard": True
            }
        )

        return "OK"

    if text == "▶️ ابدأ اختبار الإنجليزية":

        start_quiz(
            chat_id,
            "الإنجليزية"
        )

        return "OK"

    if text == "🇪🇸 الإسبانية":

        send_message(
            chat_id,
            "🇪🇸 اختبار الإسبانية:",
            {
                "keyboard": [
                    ["▶️ ابدأ اختبار الإسبانية"],
                    ["🔙 القائمة الرئيسية"]
                ],
                "resize_keyboard": True
            }
        )

        return "OK"

    if text == "▶️ ابدأ اختبار الإسبانية":

        start_quiz(
            chat_id,
            "الإسبانية"
        )

        return "OK"

    # -----------------------------------------------------
    # المعدل
    # -----------------------------------------------------

    if text == "🧮 حساب المعدل":

        start_average(chat_id)
        return "OK"

    if text == "📚 آداب وفلسفة":

        start_average_input(
            chat_id,
            "آداب وفلسفة"
        )

        return "OK"

    if text == "🌍 لغات أجنبية":

        start_average_input(
            chat_id,
            "لغات أجنبية"
        )

        return "OK"

    # -----------------------------------------------------
    # المزاح
    # -----------------------------------------------------

    if text == "🎭 معدل بكالوريا وهمي":

        start_fake_result(chat_id)
        return "OK"

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if text == "📄 مواضيع البكالوريا":

        show_bac_topics(chat_id)
        return "OK"

    # -----------------------------------------------------
    # الإحصائيات
    # -----------------------------------------------------

    if text == "📊 مستواي":

        show_stats(chat_id)
        return "OK"

    # -----------------------------------------------------
    # الإنجازات
    # -----------------------------------------------------

    if text == "🏆 الإنجازات":

        show_achievements(chat_id)
        return "OK"

    # -----------------------------------------------------
    # المساعدة
    # -----------------------------------------------------

    if text == "ℹ️ المساعدة":

        show_help(chat_id)
        return "OK"

    # -----------------------------------------------------
    # افتراضي
    # -----------------------------------------------------

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة الرئيسية.",
        main_keyboard()
    )

    return "OK"


# =========================================================
# تشغيل Render
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
