import os
import random
import requests
from flask import Flask, request

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

# تخزين مؤقت للمستخدمين
users = {}


# =========================================================
# بنك الأسئلة
# =========================================================

QUESTIONS = {

    "الفلسفة": [

        {
            "q": "ما المقصود بالفلسفة؟",
            "options": [
                "دراسة المال",
                "حب الحكمة والبحث العقلي عن الحقيقة",
                "دراسة النباتات",
                "حفظ المعلومات فقط"
            ],
            "answer": 1,
            "explanation":
                "الفلسفة تعني حب الحكمة، وتهدف إلى التفكير العقلي والنقدي "
                "في قضايا الإنسان والوجود والمعرفة والقيم."
        },

        {
            "q": "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            "options": [
                "أفلاطون",
                "أرسطو",
                "ديكارت",
                "سقراط"
            ],
            "answer": 2,
            "explanation":
                "المقولة الشهيرة «أنا أفكر إذن أنا موجود» تعود إلى رينيه ديكارت."
        },

        {
            "q": "ما المنهج الذي يعتمد على الشك للوصول إلى اليقين عند ديكارت؟",
            "options": [
                "المنهج التجريبي",
                "الشك المنهجي",
                "المنهج التاريخي",
                "المنهج الأدبي"
            ],
            "answer": 1,
            "explanation":
                "اعتمد ديكارت الشك المنهجي باعتباره وسيلة للوصول إلى الحقيقة اليقينية."
        },

        {
            "q": "ما المقصود بالاستدلال؟",
            "options": [
                "حفظ النصوص",
                "الانتقال من مقدمات إلى نتيجة",
                "قراءة الشعر",
                "وصف الطبيعة"
            ],
            "answer": 1,
            "explanation":
                "الاستدلال هو عملية عقلية ننتقل فيها من مقدمات أو أدلة إلى نتيجة."
        },

        {
            "q": "من الفيلسوف الذي اشتهر بنظرية المثل؟",
            "options": [
                "أفلاطون",
                "كانط",
                "نيتشه",
                "ديكارت"
            ],
            "answer": 0,
            "explanation":
                "أفلاطون اشتهر بنظرية المثل التي تميز بين العالم المحسوس والعالم العقلي."
        },

        {
            "q": "ما وظيفة الفلسفة الأساسية؟",
            "options": [
                "إلغاء التفكير",
                "تنمية التفكير النقدي",
                "حفظ التواريخ",
                "تعلم الحساب فقط"
            ],
            "answer": 1,
            "explanation":
                "من أهم وظائف الفلسفة تدريب الإنسان على التفكير النقدي وطرح الأسئلة وتحليل الأفكار."
        },

        {
            "q": "ما المقصود بالحرية؟",
            "options": [
                "فعل أي شيء دون مسؤولية",
                "القدرة على الاختيار مع تحمل المسؤولية",
                "رفض القوانين دائمًا",
                "عدم التفكير"
            ],
            "answer": 1,
            "explanation":
                "الحرية لا تعني الفوضى، بل ترتبط بالاختيار وتحمل نتائج الاختيارات."
        },

        {
            "q": "من الفيلسوف المرتبط بفلسفة الأخلاق القائمة على الواجب؟",
            "options": [
                "كانط",
                "أفلاطون",
                "أرسطو",
                "سقراط"
            ],
            "answer": 0,
            "explanation":
                "كانط ربط الأخلاق بالواجب والمبدأ الأخلاقي العام."
        },

        {
            "q": "ما المقصود بالحقيقة؟",
            "options": [
                "الرأي الشخصي دائمًا",
                "مطابقة الفكر أو الحكم للواقع",
                "الخيال",
                "الإشاعة"
            ],
            "answer": 1,
            "explanation":
                "في التصور الكلاسيكي للحقيقة، تكون الحقيقة مطابقة الحكم أو الفكر للواقع."
        },

        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": [
                "أفلاطون",
                "أرسطو",
                "ديكارت",
                "هيغل"
            ],
            "answer": 0,
            "explanation":
                "كتاب الجمهورية من أشهر مؤلفات أفلاطون."
        },

        {
            "q": "ما المقصود بالمنطق؟",
            "options": [
                "علم التفكير الصحيح",
                "علم النبات",
                "علم الاقتصاد",
                "علم التاريخ"
            ],
            "answer": 0,
            "explanation":
                "المنطق يهتم بقواعد التفكير والاستدلال الصحيح."
        },

        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": [
                "أرسطو",
                "ديكارت",
                "كانط",
                "نيتشه"
            ],
            "answer": 0,
            "explanation":
                "أرسطو رأى أن الإنسان كائن اجتماعي وسياسي بطبيعته."
        }

    ],


    # =====================================================
    # الفرنسية
    # =====================================================

    "الفرنسية": [

        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": [
                "triste",
                "content",
                "fatigué",
                "malade"
            ],
            "answer": 1,
            "explanation":
                "« heureux » signifie « content »."
        },

        {
            "q": "Quel est le contraire de « difficile » ?",
            "options": [
                "compliqué",
                "facile",
                "long",
                "fort"
            ],
            "answer": 1,
            "explanation":
                "Le contraire de « difficile » est « facile »."
        },

        {
            "q": "Choisissez le bon verbe : Je ___ au lycée.",
            "options": [
                "vais",
                "va",
                "aller",
                "allons"
            ],
            "answer": 0,
            "explanation":
                "Avec « je », le verbe aller se conjugue « je vais »."
        },

        {
            "q": "Quel est le pluriel de « cheval » ?",
            "options": [
                "chevals",
                "chevaux",
                "chevales",
                "chevaus"
            ],
            "answer": 1,
            "explanation":
                "Le pluriel irrégulier de « cheval » est « chevaux »."
        },

        {
            "q": "Quel temps utilise-t-on dans : « Hier, j'ai étudié » ?",
            "options": [
                "Présent",
                "Futur",
                "Passé composé",
                "Imparfait"
            ],
            "answer": 2,
            "explanation":
                "« J'ai étudié » est au passé composé."
        },

        {
            "q": "Complétez : Nous ___ nos devoirs.",
            "options": [
                "fait",
                "faisons",
                "faire",
                "faites"
            ],
            "answer": 1,
            "explanation":
                "Avec « nous », le verbe faire devient « nous faisons »."
        },

        {
            "q": "Quel mot est un adjectif ?",
            "options": [
                "rapidement",
                "maison",
                "intelligent",
                "courir"
            ],
            "answer": 2,
            "explanation":
                "« intelligent » est un adjectif qualificatif."
        },

        {
            "q": "Quel est le féminin de « acteur » ?",
            "options": [
                "acteuse",
                "actrice",
                "acteurse",
                "acteure"
            ],
            "answer": 1,
            "explanation":
                "Le féminin de « acteur » est « actrice »."
        },

        {
            "q": "Complétez : Si j'avais le temps, je ___ davantage.",
            "options": [
                "lis",
                "lirais",
                "lirai",
                "lu"
            ],
            "answer": 1,
            "explanation":
                "Après « si + imparfait », on utilise généralement le conditionnel présent."
        },

        {
            "q": "Quel est le contraire de « ancien » ?",
            "options": [
                "vieux",
                "moderne",
                "passé",
                "historique"
            ],
            "answer": 1,
            "explanation":
                "Le contraire de « ancien » peut être « moderne »."
        }

    ],


    # =====================================================
    # الإنجليزية
    # =====================================================

    "الإنجليزية": [

        {
            "q": "Choose the correct form: She ___ English every day.",
            "options": [
                "study",
                "studies",
                "studying",
                "studied"
            ],
            "answer": 1,
            "explanation":
                "With « she » in the present simple, the verb takes -s: studies."
        },

        {
            "q": "What is the past tense of « go »?",
            "options": [
                "goed",
                "gone",
                "went",
                "going"
            ],
            "answer": 2,
            "explanation":
                "The past simple of « go » is « went »."
        },

        {
            "q": "Choose: I ___ a student.",
            "options": [
                "am",
                "is",
                "are",
                "be"
            ],
            "answer": 0,
            "explanation":
                "With « I », we use « am »."
        },

        {
            "q": "What is the opposite of « easy »?",
            "options": [
                "simple",
                "hard",
                "short",
                "small"
            ],
            "answer": 1,
            "explanation":
                "The opposite of « easy » is « hard » or « difficult »."
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
            "explanation":
                "With he/she/it, negative present simple uses doesn't + base verb."
        },

        {
            "q": "What is the comparative form of « good »?",
            "options": [
                "gooder",
                "more good",
                "better",
                "best"
            ],
            "answer": 2,
            "explanation":
                "The comparative form of good is better."
        },

        {
            "q": "Choose: They ___ playing now.",
            "options": [
                "is",
                "am",
                "are",
                "be"
            ],
            "answer": 2,
            "explanation":
                "Present continuous with they uses « are »."
        },

        {
            "q": "What does « environment » mean?",
            "options": [
                "البيئة",
                "الاقتصاد",
                "الرياضة",
                "التاريخ"
            ],
            "answer": 0,
            "explanation":
                "Environment means البيئة."
        },

        {
            "q": "Choose the correct word: I have lived here ___ 2020.",
            "options": [
                "for",
                "since",
                "at",
                "on"
            ],
            "answer": 1,
            "explanation":
                "We use « since » with a starting point in time."
        },

        {
            "q": "What is the past participle of « write »?",
            "options": [
                "wrote",
                "written",
                "writing",
                "writes"
            ],
            "answer": 1,
            "explanation":
                "The past participle of write is written."
        }

    ],


    # =====================================================
    # الإسبانية
    # =====================================================

    "الإسبانية": [

        {
            "q": "¿Cómo se dice « مرحبا » en español?",
            "options": [
                "Adiós",
                "Hola",
                "Gracias",
                "Por favor"
            ],
            "answer": 1,
            "explanation":
                "Hola significa مرحبًا."
        },

        {
            "q": "¿Qué significa « gracias »?",
            "options": [
                "مرحبا",
                "شكرا",
                "وداعا",
                "نعم"
            ],
            "answer": 1,
            "explanation":
                "Gracias significa شكرا."
        },

        {
            "q": "Completa: Yo ___ estudiante.",
            "options": [
                "soy",
                "eres",
                "es",
                "son"
            ],
            "answer": 0,
            "explanation":
                "Con « yo » usamos « soy » del verbo ser."
        },

        {
            "q": "¿Cuál es el contrario de « grande »?",
            "options": [
                "alto",
                "pequeño",
                "bonito",
                "rápido"
            ],
            "answer": 1,
            "explanation":
                "El contrario de grande es pequeño."
        },

        {
            "q": "¿Cómo se dice « كتاب »?",
            "options": [
                "mesa",
                "casa",
                "libro",
                "escuela"
            ],
            "answer": 2,
            "explanation":
                "Libro significa كتاب."
        }

    ]
}


# =========================================================
# أدوات Telegram
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

    return telegram(
        "sendMessage",
        data
    )


def answer_callback(callback_id):

    telegram(
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
# بدء اختبار
# =========================================================

def start_quiz(chat_id, subject):

    questions = QUESTIONS.get(subject, [])

    if not questions:

        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة حاليًا."
        )

        return

    # نختار حتى 10 أسئلة
    count = min(
        10,
        len(questions)
    )

    selected = random.sample(
        questions,
        count
    )

    users[chat_id] = {
        "step": "quiz",
        "subject": subject,
        "questions": selected,
        "current": 0,
        "score": 0,
        "streak": 0,
        "best_streak": 0
    }

    send_question(chat_id)


# =========================================================
# إرسال السؤال
# =========================================================

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
                "callback_data": f"quiz_{i}"
            }
        ])

    send_message(
        chat_id,
        f"📝 {user['subject']}\n\n"
        f"السؤال {index + 1} / {len(questions)}\n\n"
        f"❓ {question['q']}\n\n"
        "اختر الإجابة:",
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# إنهاء الاختبار
# =========================================================

def finish_quiz(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    total = len(user["questions"])
    score = user["score"]

    percentage = round(
        score / total * 100
    )

    # حفظ الإحصائيات
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
        level = "👍 مقبول"

    else:
        level = "💪 تحتاج إلى مراجعة"

    send_message(
        chat_id,
        f"🎉 انتهى الاختبار!\n\n"
        f"📚 المادة: {user['subject']}\n"
        f"✅ الإجابات الصحيحة: {score}\n"
        f"❌ الإجابات الخاطئة: {total - score}\n"
        f"📊 النتيجة: {percentage}%\n"
        f"🏅 المستوى: {level}\n"
        f"🔥 أفضل سلسلة: {user['best_streak']}\n\n"
        "استمر في التدريب وستتحسن نتيجتك مع الوقت."
    )


# =========================================================
# معالجة الإجابات
# =========================================================

def handle_callback(callback):

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

    user = users.get(chat_id)

    if not user:
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

    index = user["current"]

    question = user["questions"][index]

    correct = question["answer"]

    if selected == correct:

        user["score"] += 1
        user["streak"] += 1

        user["best_streak"] = max(
            user["best_streak"],
            user["streak"]
        )

        result = (
            "✅ إجابة صحيحة!\n\n"
            f"🔥 سلسلة صحيحة: {user['streak']}"
        )

    else:

        user["streak"] = 0

        correct_text = (
            question["options"][correct]
        )

        result = (
            "❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة: {correct_text}"
        )

    result += (
        "\n\n"
        f"💡 الشرح:\n"
        f"{question['explanation']}"
    )

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
        message_id,
        result,
        keyboard
    )


    # حفظ أن السؤال تمت الإجابة عليه
    user["answered"] = True


# =========================================================
# السؤال التالي
# =========================================================

def handle_next(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


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
        "💡 حاول فهم أفكار الفيلسوف بدل حفظ اسمه فقط."
    )


# =========================================================
# مفاهيم فلسفية
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
        "راجع المفهوم، المشكلة، المواقف، والحجج."
    )


# =========================================================
# الكلمات
# =========================================================

def important_words(chat_id, language):

    words = {

        "🇫🇷 الفرنسية":
            "🇫🇷 كلمات فرنسية:\n\n"
            "Environnement = البيئة\n"
            "Société = المجتمع\n"
            "Éducation = التربية\n"
            "Liberté = الحرية\n"
            "Droit = الحق\n"
            "Problème = مشكلة\n"
            "Solution = حل",

        "🇬🇧 الإنجليزية":
            "🇬🇧 كلمات إنجليزية:\n\n"
            "Environment = البيئة\n"
            "Society = المجتمع\n"
            "Education = التعليم\n"
            "Freedom = الحرية\n"
            "Rights = الحقوق\n"
            "Problem = مشكلة\n"
            "Solution = حل",

        "🇪🇸 الإسبانية":
            "🇪🇸 كلمات إسبانية:\n\n"
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
            "لا توجد كلمات حاليًا."
        )
    )


# =========================================================
# الإحصائيات
# =========================================================

def show_stats(chat_id):

    user = users.get(
        chat_id,
        {}
    )

    if "last_score" not in user:

        send_message(
            chat_id,
            "📊 لا توجد إحصائيات بعد.\n\n"
            "ابدأ أول اختبار لتظهر نتيجتك."
        )

        return

    send_message(
        chat_id,
        f"📊 مستواك الحالي:\n\n"
        f"📚 المادة: {user.get('subject', '-')}\n"
        f"✅ صحيح: {user['last_score']}\n"
        f"❌ خطأ: "
        f"{user['last_total'] - user['last_score']}\n"
        f"🏆 النتيجة: {user['last_percentage']}%\n"
        f"🔥 أفضل سلسلة: "
        f"{user.get('best_streak', 0)}"
    )


# =========================================================
# الإنجازات
# =========================================================

def achievements(chat_id):

    user = users.get(
        chat_id,
        {}
    )

    percentage = user.get(
        "last_percentage",
        0
    )

    streak = user.get(
        "best_streak",
        0
    )

    badges = []

    if percentage >= 50:
        badges.append("🎯 أول نجاح")

    if percentage >= 80:
        badges.append("🔥 متفوق")

    if percentage >= 90:
        badges.append("🏆 عبقري")

    if streak >= 3:
        badges.append("⚡ سلسلة 3")

    if streak >= 5:
        badges.append("🚀 سلسلة 5")

    if not badges:
        badges.append(
            "🔒 لم تحصل على شارة بعد"
        )

    send_message(
        chat_id,
        "🏆 إنجازاتك:\n\n" +
        "\n".join(badges)
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

    # Callback
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

        if callback_data == "next":

            answer_callback(
                callback.get("id")
            )

            handle_next(
                chat_id
            )

        else:

            handle_callback(
                callback
            )

        return "OK"


    # Message
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


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        users[chat_id] = {
            "step": "main"
        }

        send_message(
            chat_id,
            "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"
            "البوت المتخصص في:\n"
            "🧠 آداب وفلسفة\n"
            "🌍 لغات أجنبية\n\n"
            "تدرّب، اختبر نفسك، وطوّر مستواك.\n\n"
            "🚀 هدفنا: أن تدخل البكالوريا بثقة.",
            main_keyboard()
        )

        return "OK"


    # =====================================================
    # فلسفة
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


    if text == "📝 اختبار اللغة":

        # نحدد اللغة من آخر اختيار
        # إذا لم تكن محفوظة، نستخدم الفرنسية
        subject = users.get(
            chat_id,
            {}
        ).get(
            "language",
            "الفرنسية"
        )

        start_quiz(
            chat_id,
            subject
        )

        return "OK"


    # =====================================================
    # الإنجليزية
    # =====================================================

    if text == "🇬🇧 الإنجليزية":

        users[chat_id] = {
            "step": "language",
            "language": "الإنجليزية"
        }

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

        users[chat_id] = {
            "step": "language",
            "language": "الإسبانية"
        }

        send_message(
            chat_id,
            "🇪🇸 قسم الإسبانية:",
            language_keyboard()
        )

        return "OK"


    # =====================================================
    # اختبار فرنسي
    # =====================================================

    if text == "🇫🇷 اختبار فرنسي":

        start_quiz(
            chat_id,
            "الفرنسية"
        )

        return "OK"


    # =====================================================
    # كلمات
    # =====================================================

    if text == "📚 كلمات مهمة":

        language = users.get(
            chat_id,
            {}
        ).get(
            "language",
            "الفرنسية"
        )

        important_words(
            chat_id,
            "🇫🇷 الفرنسية"
            if language == "الفرنسية"
            else
            "🇬🇧 الإنجليزية"
            if language == "الإنجليزية"
            else
            "🇪🇸 الإسبانية"
        )

        return "OK"


    # =====================================================
    # مواضيع
    # =====================================================

    if text == "📄 مواضيع البكالوريا":

        bac_topics(
            chat_id
        )

        return "OK"


    if text == "📚 آداب وفلسفة":

        send_message(
            chat_id,
            "📚 مواضيع شعبة آداب وفلسفة:\n\n"
            "سنضيف هنا المواضيع حسب السنوات والمادة."
        )

        return "OK"


    if text == "🌍 لغات أجنبية":

        send_message(
            chat_id,
            "🌍 مواضيع شعبة لغات أجنبية:\n\n"
            "سنضيف هنا المواضيع حسب اللغة والسنة."
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
            "ℹ️ كيف تستخدم BacMind DZ؟\n\n"
            "1️⃣ اختر المادة.\n"
            "2️⃣ ابدأ الاختبار.\n"
            "3️⃣ أجب عن الأسئلة.\n"
            "4️⃣ شاهد الشرح.\n"
            "5️⃣ تابع نتيجتك ومستواك.\n\n"
            "🎯 ركّز على الفهم وليس الحفظ فقط."
        )

        return "OK"


    # =====================================================
    # رجوع
    # =====================================================

    if text == "🔙 القائمة الرئيسية":

        users[chat_id] = {
            "step": "main"
        }

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_keyboard()
        )

        return "OK"


    # =====================================================
    # افتراضي
    # =====================================================

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة الرئيسية."
    )

    return "OK"


# =========================================================
# تشغيل
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
