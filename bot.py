import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# إعدادات Telegram
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN غير موجود في Environment Variables")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN else ""
)

# =========================================================
# بيانات المستخدمين
# ملاحظة: التخزين هنا مؤقت، وقد يختفي عند إعادة تشغيل Render.
# =========================================================

users = {}


# =========================================================
# بنك الأسئلة
# كل شيء موجود داخل bot.py
# =========================================================

QUESTIONS = {

    "الفلسفة": [
        {
            "q": "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            "answer": 2,
            "explanation": "المقولة ترتبط برينيه ديكارت، الذي جعل التفكير نقطة أساسية في إثبات وجود الذات."
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
            "explanation": "الفلسفة تقوم على التساؤل والتفكير والتحليل والنقد والبحث عن الحقيقة."
        },
        {
            "q": "من صاحب نظرية المثل؟",
            "options": ["أفلاطون", "ديكارت", "كانط", "نيتشه"],
            "answer": 0,
            "explanation": "أفلاطون من أشهر الفلاسفة المرتبطين بنظرية المثل."
        },
        {
            "q": "من قال إن الإنسان حيوان سياسي؟",
            "options": ["سقراط", "أرسطو", "ديكارت", "هيغل"],
            "answer": 1,
            "explanation": "يرتبط هذا القول بأرسطو الذي اعتبر الإنسان كائنًا اجتماعيًا وسياسيًا."
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
            "options": ["أرسطو", "ديكارت", "أفلاطون", "ماركس"],
            "answer": 1,
            "explanation": "استخدم ديكارت الشك المنهجي للوصول إلى اليقين."
        },
        {
            "q": "ما معنى الحرية؟",
            "options": [
                "فعل أي شيء دون مسؤولية",
                "القدرة على الاختيار وتحمل المسؤولية",
                "رفض جميع القوانين",
                "عدم التفكير"
            ],
            "answer": 1,
            "explanation": "الحرية ترتبط بالاختيار، لكنها لا تنفصل عن المسؤولية."
        },
        {
            "q": "من الفيلسوف الذي ربط الأخلاق بالواجب؟",
            "options": ["كانط", "أفلاطون", "أرسطو", "سقراط"],
            "answer": 0,
            "explanation": "يربط كانط الأخلاق بالواجب والمبدأ الأخلاقي."
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
            "explanation": "من التصورات الكلاسيكية للحقيقة أنها مطابقة الحكم أو الفكر للواقع."
        },
        {
            "q": "من صاحب كتاب الجمهورية؟",
            "options": ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            "answer": 0,
            "explanation": "الجمهورية من أشهر مؤلفات أفلاطون."
        },
        {
            "q": "ما الهدف الأساسي من التفكير النقدي؟",
            "options": [
                "رفض كل شيء",
                "تحليل الأفكار والأدلة",
                "حفظ النصوص",
                "تجنب الأسئلة"
            ],
            "answer": 1,
            "explanation": "التفكير النقدي يقوم على تحليل الأفكار وفحص الأدلة قبل إصدار الحكم."
        },
        {
            "q": "أي مفهوم يرتبط بالبحث عن المعرفة؟",
            "options": [
                "الإبستمولوجيا",
                "الجمال",
                "الرياضة",
                "الاقتصاد"
            ],
            "answer": 0,
            "explanation": "الإبستمولوجيا مجال فلسفي يهتم بالمعرفة ومصادرها وحدودها."
        },
        {
            "q": "من أبرز فلاسفة اليونان القديمة؟",
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
            "explanation": "الأخلاق تبحث في القيم والمعايير التي توجه السلوك الإنساني."
        },
        {
            "q": "أي مفهوم يرتبط بالحكم على الجميل والقبيح؟",
            "options": ["الجماليات", "المنطق", "السياسة", "الاقتصاد"],
            "answer": 0,
            "explanation": "الجماليات أو علم الجمال يهتم بقضايا الفن والجمال."
        },

        {
            "q": "ما العلاقة بين العقل والتجربة في المعرفة؟",
            "options": [
                "لا علاقة بينهما",
                "يمكن أن يتكاملا في بناء المعرفة",
                "التجربة تمنع التفكير",
                "العقل يمنع العلم"
            ],
            "answer": 1,
            "explanation": "ناقش الفلاسفة العلاقة بين العقل والتجربة، ويمكن النظر إليهما كوسيلتين متكاملتين في بناء المعرفة."
        },
        {
            "q": "ما المقصود بالوعي؟",
            "options": [
                "إدراك الإنسان لذاته وما يحيط به",
                "النوم",
                "النسيان",
                "الحركة فقط"
            ],
            "answer": 0,
            "explanation": "الوعي يشير إلى إدراك الإنسان لذاته وللعالم المحيط به."
        },
        {
            "q": "ما المقصود بالدولة في الفكر السياسي؟",
            "options": [
                "تنظيم سياسي واجتماعي",
                "مجموعة كتب",
                "نوع من العلوم",
                "مكان للدراسة فقط"
            ],
            "answer": 0,
            "explanation": "الدولة تنظيم سياسي واجتماعي يقوم على مؤسسات وقوانين وسلطة."
        },
        {
            "q": "ما المقصود بالقيمة الأخلاقية؟",
            "options": [
                "مبدأ يوجه السلوك",
                "رقم رياضي",
                "مكان جغرافي",
                "نوع من الأدب"
            ],
            "answer": 0,
            "explanation": "القيم الأخلاقية تساعد الإنسان على الحكم على الأفعال وتوجيه السلوك."
        },
        {
            "q": "ما وظيفة السؤال الفلسفي؟",
            "options": [
                "إلغاء التفكير",
                "فتح مجال للتفكير والنقاش",
                "حفظ الإجابة فقط",
                "منع الحوار"
            ],
            "answer": 1,
            "explanation": "السؤال الفلسفي يفتح المجال للتحليل والنقاش والبحث عن الحجج."
        }
    ],

    "الفرنسية": [
        {
            "q": "Quel est le synonyme de « heureux » ?",
            "options": ["Triste", "Content", "Malade", "Fatigué"],
            "answer": 1,
            "explanation": "« Heureux » et « content » ont un sens proche."
        },
        {
            "q": "Quel est le contraire de « difficile » ?",
            "options": ["Compliqué", "Facile", "Long", "Fort"],
            "answer": 1,
            "explanation": "Le contraire de « difficile » est « facile »."
        },
        {
            "q": "Complétez : Je ___ au lycée.",
            "options": ["vais", "va", "allons", "allez"],
            "answer": 0,
            "explanation": "Avec « je », le verbe aller se conjugue « je vais »."
        },
        {
            "q": "Quel est le pluriel de « cheval » ?",
            "options": ["Chevals", "Chevaux", "Chevales", "Chevaus"],
            "answer": 1,
            "explanation": "Le pluriel de « cheval » est « chevaux »."
        },
        {
            "q": "« J'ai étudié » est à quel temps ?",
            "options": ["Présent", "Futur", "Passé composé", "Imparfait"],
            "answer": 2,
            "explanation": "« J'ai étudié » est au passé composé."
        },
        {
            "q": "Complétez : Nous ___ nos devoirs.",
            "options": ["fait", "faisons", "faites", "faire"],
            "answer": 1,
            "explanation": "Avec « nous », on dit « nous faisons »."
        },
        {
            "q": "Quel mot est un adjectif ?",
            "options": ["Rapidement", "Maison", "Intelligent", "Courir"],
            "answer": 2,
            "explanation": "« Intelligent » est un adjectif qualificatif."
        },
        {
            "q": "Quel est le féminin de « acteur » ?",
            "options": ["Acteuse", "Actrice", "Acteure", "Acteurs"],
            "answer": 1,
            "explanation": "Le féminin de « acteur » est « actrice »."
        },
        {
            "q": "Si j'avais le temps, je ___ davantage.",
            "options": ["lis", "lirais", "lirai", "lu"],
            "answer": 1,
            "explanation": "Après « si + imparfait », on utilise ici le conditionnel présent."
        },
        {
            "q": "Quel est le contraire de « ancien » ?",
            "options": ["Vieux", "Moderne", "Passé", "Historique"],
            "answer": 1,
            "explanation": "Dans ce contexte, le contraire d'ancien est moderne."
        },
        {
            "q": "Complétez : Il ___ très intelligent.",
            "options": ["sont", "es", "est", "être"],
            "answer": 2,
            "explanation": "Avec « il », le verbe être se conjugue « est »."
        },
        {
            "q": "Quel est le contraire de « rapide » ?",
            "options": ["Lent", "Fort", "Grand", "Jeune"],
            "answer": 0,
            "explanation": "Le contraire de « rapide » est « lent »."
        },
        {
            "q": "Complétez : Nous ___ français.",
            "options": ["parle", "parlons", "parlez", "parler"],
            "answer": 1,
            "explanation": "Avec « nous », on dit « nous parlons »."
        },
        {
            "q": "Quel mot signifie « école » ?",
            "options": ["École", "Maison", "Livre", "Route"],
            "answer": 0,
            "explanation": "Le mot « école » signifie مدرسة."
        },
        {
            "q": "Quel est le féminin de « étudiant » ?",
            "options": ["Étudiante", "Étude", "Étudieuse", "Étudiée"],
            "answer": 0,
            "explanation": "Le féminin de « étudiant » est « étudiante »."
        }
    ],

    "الإنجليزية": [
        {
            "q": "Choose the correct answer: She ___ English every day.",
            "options": ["study", "studies", "studying", "studied"],
            "answer": 1,
            "explanation": "With she/he/it in the present simple, the verb usually takes -s or -es."
        },
        {
            "q": "What is the past tense of « go »?",
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
            "explanation": "The correct form with I is « I am »."
        },
        {
            "q": "What is the opposite of « easy »?",
            "options": ["Simple", "Hard", "Short", "Small"],
            "answer": 1,
            "explanation": "The opposite of easy is hard or difficult."
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
            "explanation": "With he/she/it, use doesn't + the base form of the verb."
        },
        {
            "q": "What is the comparative form of « good »?",
            "options": ["Gooder", "More good", "Better", "Best"],
            "answer": 2,
            "explanation": "The comparative form of good is better."
        },
        {
            "q": "Choose: They ___ playing now.",
            "options": ["is", "am", "are", "be"],
            "answer": 2,
            "explanation": "The present continuous with they uses « are »."
        },
        {
            "q": "What does « environment » mean?",
            "options": ["البيئة", "الاقتصاد", "الرياضة", "التاريخ"],
            "answer": 0,
            "explanation": "Environment means البيئة."
        },
        {
            "q": "I have lived here ___ 2020.",
            "options": ["for", "since", "at", "on"],
            "answer": 1,
            "explanation": "Since is used with a starting point in time."
        },
        {
            "q": "What is the past participle of « write »?",
            "options": ["wrote", "written", "writing", "writes"],
            "answer": 1,
            "explanation": "The past participle of write is written."
        },
        {
            "q": "Choose the correct form: They ___ football yesterday.",
            "options": ["play", "played", "playing", "plays"],
            "answer": 1,
            "explanation": "Yesterday refers to the past, so we use the past simple: played."
        },
        {
            "q": "Choose: I ___ never been to London.",
            "options": ["have", "has", "am", "was"],
            "answer": 0,
            "explanation": "With I, the present perfect uses have."
        },
        {
            "q": "What is the opposite of « strong »?",
            "options": ["Weak", "Tall", "Fast", "Rich"],
            "answer": 0,
            "explanation": "The opposite of strong is weak."
        },
        {
            "q": "Choose: If I study hard, I ___ pass.",
            "options": ["would", "will", "was", "did"],
            "answer": 1,
            "explanation": "In the first conditional, we commonly use if + present, will + base verb."
        },
        {
            "q": "What does « education » mean?",
            "options": ["التعليم", "السفر", "الرياضة", "الطعام"],
            "answer": 0,
            "explanation": "Education means التعليم."
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
            "explanation": "Con « yo » usamos « soy »."
        },
        {
            "q": "¿Cuál es el contrario de « grande »?",
            "options": ["alto", "pequeño", "bonito", "rápido"],
            "answer": 1,
            "explanation": "El contrario de grande es pequeño."
        },
        {
            "q": "¿Cómo se dice « كتاب » en español?",
            "options": ["Mesa", "Casa", "Libro", "Escuela"],
            "answer": 2,
            "explanation": "Libro significa كتاب."
        },
        {
            "q": "¿Cómo se dice « مدرسة » en español?",
            "options": ["Escuela", "Casa", "Libro", "Calle"],
            "answer": 0,
            "explanation": "Escuela significa مدرسة."
        },
        {
            "q": "Completa: Nosotros ___ español.",
            "options": ["hablo", "hablas", "hablamos", "hablan"],
            "answer": 2,
            "explanation": "Con nosotros usamos « hablamos »."
        },
        {
            "q": "¿Cuál es el contrario de « bueno »?",
            "options": ["malo", "grande", "alto", "rápido"],
            "answer": 0,
            "explanation": "El contrario de bueno es malo."
        },
        {
            "q": "¿Qué significa « libertad »?",
            "options": ["الحرية", "المجتمع", "المدرسة", "الطريق"],
            "answer": 0,
            "explanation": "Libertad significa الحرية."
        },
        {
            "q": "Completa: Ella ___ inteligente.",
            "options": ["soy", "eres", "es", "son"],
            "answer": 2,
            "explanation": "Con ella usamos « es » del verbo ser."
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
            timeout=15
        )

        print(f"Telegram {method}: HTTP {response.status_code}")

        if response.status_code >= 400:
            print("Telegram response:", response.text)

        return response.json()

    except requests.RequestException as error:
        print("Telegram connection error:", error)
        return None

    except ValueError as error:
        print("Telegram JSON error:", error)
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
        {"callback_query_id": callback_id}
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
# القوائم
# =========================================================

def main_keyboard():
    return {
        "keyboard": [
            ["🧠 الفلسفة"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🇪🇸 الإسبانية"],
            ["📄 مواضيع البكالوريا"],
            ["📊 مستواي", "🏆 الإنجازات"],
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


def language_keyboard(language):
    return {
        "keyboard": [
            [f"📝 اختبار {language}"],
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
# نظام النجوم
# =========================================================

def get_stars(answered):
    if answered >= 120:
        return 5
    if answered >= 90:
        return 4
    if answered >= 60:
        return 3
    if answered >= 30:
        return 2
    if answered >= 10:
        return 1
    return 0


def get_student_title(stars):
    titles = {
        0: "🌱 طالب في بداية الطريق",
        1: "⭐ طالب طموح",
        2: "⭐⭐ طالب مجتهد",
        3: "⭐⭐⭐ طالب متقدم",
        4: "⭐⭐⭐⭐ طالب متميز",
        5: "⭐⭐⭐⭐⭐ طالب قوي وذكي"
    }
    return titles.get(stars, titles[0])


def achievement_message(stars):
    messages = {
        1: "رائع! بدأت تبني عادة المراجعة. استمر ولا تتوقف! 🚀",
        2: "ممتاز! اجتهادك بدأ يظهر. أنت على الطريق الصحيح! 🔥",
        3: "أداء قوي! أصبحت من الطلاب المتقدمين. واصل التحدي! 💪",
        4: "مذهل! مستواك متميز. بقيت خطوة واحدة نحو القمة! 🏆",
        5: "أسطوري! وصلت إلى خمس نجوم ⭐⭐⭐⭐⭐ أنت طالب قوي وذكي، واصل حتى تحقق هدف البكالوريا! 🎓🔥"
    }
    return messages.get(stars)


def update_progress(chat_id, correct):
    user = users.setdefault(chat_id, {})

    old_answered = user.get("answered_total", 0)
    old_stars = get_stars(old_answered)

    user["answered_total"] = old_answered + 1

    if correct:
        user["correct_total"] = user.get("correct_total", 0) + 1
    else:
        user["wrong_total"] = user.get("wrong_total", 0) + 1

    new_stars = get_stars(user["answered_total"])

    if new_stars > old_stars:
        send_message(
            chat_id,
            f"🎉 تهانينا!\n\n"
            f"لقد وصلت إلى المستوى:\n"
            f"{get_student_title(new_stars)}\n\n"
            f"📚 عدد الأسئلة التي أجبت عنها: "
            f"{user['answered_total']}\n\n"
            f"{achievement_message(new_stars)}"
        )


# =========================================================
# بدء الاختبار
# =========================================================

def start_quiz(chat_id, subject):
    questions = QUESTIONS.get(subject, [])

    if not questions:
        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة حاليًا."
        )
        return

    # 10 أسئلة مختلفة في كل اختبار
    amount = min(10, len(questions))

    selected = random.sample(
        questions,
        amount
    )

    users[chat_id] = {
        **users.get(chat_id, {}),
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


# =========================================================
# إرسال السؤال
# =========================================================

def send_question(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    questions = user.get("questions", [])
    index = user.get("current", 0)

    if index >= len(questions):
        finish_quiz(chat_id)
        return

    question = questions[index]

    keyboard = []

    for i, option in enumerate(question["options"]):
        keyboard.append([
            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"answer:{i}"
            }
        ])

    send_message(
        chat_id,
        f"📝 {user['subject']}\n\n"
        f"السؤال {index + 1}/{len(questions)}\n\n"
        f"❓ {question['q']}\n\n"
        "اختر إجابتك:",
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# معالجة الإجابة
# =========================================================

def handle_answer(callback):
    callback_id = callback.get("id")
    answer_callback(callback_id)

    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    message_id = message.get("message_id")

    if not chat_id:
        return

    user = users.get(chat_id)

    if not user or user.get("mode") != "quiz":
        return

    if user.get("answered"):
        return

    data = callback.get("data", "")

    if not data.startswith("answer:"):
        return

    try:
        selected = int(data.split(":")[1])
    except (ValueError, IndexError):
        return

    index = user["current"]
    questions = user["questions"]

    if index >= len(questions):
        return

    question = questions[index]
    correct_index = question["answer"]

    is_correct = selected == correct_index

    # منع الضغط على أكثر من إجابة
    user["answered"] = True

    update_progress(
        chat_id,
        is_correct
    )

    if is_correct:
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

        correct_text = question["options"][correct_index]

        result = (
            "❌ إجابة خاطئة.\n\n"
            f"✅ الإجابة الصحيحة: {correct_text}"
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
                        "callback_data": "next"
                    }
                ]
            ]
        }
    )


# =========================================================
# السؤال التالي
# =========================================================

def handle_next(callback):
    callback_id = callback.get("id")
    answer_callback(callback_id)

    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    user = users.get(chat_id)

    if not user or user.get("mode") != "quiz":
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


# =========================================================
# نهاية الاختبار
# =========================================================

def finish_quiz(chat_id):
    user = users.get(chat_id)

    if not user:
        return

    total = len(user.get("questions", []))
    score = user.get("score", 0)

    if total == 0:
        return

    percentage = round(
        score / total * 100
    )

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage
    user["mode"] = "main"

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

    stars = get_stars(
        user.get("answered_total", 0)
    )

    send_message(
        chat_id,
        f"🎉 انتهى الاختبار!\n\n"
        f"📚 المادة: {user['subject']}\n"
        f"✅ صحيح: {score}\n"
        f"❌ خطأ: {total - score}\n"
        f"📊 النتيجة: {percentage}%\n"
        f"🏅 المستوى: {level}\n"
        f"🔥 أفضل سلسلة: {user.get('best_streak', 0)}\n\n"
        f"⭐ رتبتك الحالية: "
        f"{'⭐' * stars if stars else '🌱'}\n"
        f"{get_student_title(stars)}\n\n"
        "🚀 لا تتوقف! كل سؤال تجيب عنه يقربك من النجاح."
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
        "💡 حاول فهم أفكار الفيلسوف بدل حفظ اسمه فقط."
    )


# =========================================================
# المفاهيم
# =========================================================

def philosophy_concepts(chat_id):
    send_message(
        chat_id,
        "💡 مفاهيم مهمة:\n\n"
        "🧠 الوعي\n"
        "🔓 الحرية\n"
        "⚖️ الأخلاق\n"
        "🔎 الحقيقة\n"
        "📚 المعرفة\n"
        "🏛️ الدولة\n"
        "🗣️ اللغة\n"
        "🎨 الفن\n"
        "🔬 العلم\n\n"
        "🎯 ركز على: المفهوم + المشكلة + المواقف + الحجج + النقد."
    )


# =========================================================
# الكلمات
# =========================================================

def important_words(chat_id, language):
    words = {
        "الفرنسية": (
            "🇫🇷 كلمات مهمة:\n\n"
            "Environnement = البيئة\n"
            "Société = المجتمع\n"
            "Éducation = التعليم\n"
            "Liberté = الحرية\n"
            "Droit = الحق\n"
            "Problème = مشكلة\n"
            "Solution = حل"
        ),
        "الإنجليزية": (
            "🇬🇧 كلمات مهمة:\n\n"
            "Environment = البيئة\n"
            "Society = المجتمع\n"
            "Education = التعليم\n"
            "Freedom = الحرية\n"
            "Rights = الحقوق\n"
            "Problem = مشكلة\n"
            "Solution = حل"
        ),
        "الإسبانية": (
            "🇪🇸 كلمات مهمة:\n\n"
            "Educación = التعليم\n"
            "Sociedad = المجتمع\n"
            "Libertad = الحرية\n"
            "Problema = مشكلة\n"
            "Solución = حل\n"
            "Medio ambiente = البيئة"
        )
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
    user = users.get(chat_id, {})

    answered = user.get("answered_total", 0)
    correct = user.get("correct_total", 0)
    wrong = user.get("wrong_total", 0)

    if answered:
        accuracy = round(
            correct / answered * 100
        )
    else:
        accuracy = 0

    stars = get_stars(answered)

    send_message(
        chat_id,
        f"📊 إحصائياتك\n\n"
        f"📝 الأسئلة المجاب عنها: {answered}\n"
        f"✅ الصحيحة: {correct}\n"
        f"❌ الخاطئة: {wrong}\n"
        f"🎯 نسبة النجاح: {accuracy}%\n"
        f"⭐ النجوم: {'⭐' * stars if stars else 'لا توجد بعد'}\n"
        f"🏅 الرتبة: {get_student_title(stars)}\n\n"
        "💡 كلما تدربت أكثر، ارتفع مستواك."
    )


# =========================================================
# الإنجازات
# =========================================================

def achievements(chat_id):
    user = users.get(chat_id, {})

    answered = user.get("answered_total", 0)
    stars = get_stars(answered)

    progress = [
        "⭐ 10 أسئلة — بداية قوية",
        "⭐⭐ 30 سؤالًا — طالب طموح",
        "⭐⭐⭐ 60 سؤالًا — طالب مجتهد",
        "⭐⭐⭐⭐ 90 سؤالًا — طالب متميز",
        "⭐⭐⭐⭐⭐ 120 سؤالًا — طالب قوي وذكي"
    ]

    send_message(
        chat_id,
        "🏆 نظام الإنجازات\n\n"
        + "\n".join(progress)
        + "\n\n"
        f"📚 تقدمك الحالي: {answered} سؤال\n"
        f"🏅 رتبتك: {get_student_title(stars)}"
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


@app.route("/telegram/webhook", methods=["POST"])
def webhook():
    data = request.get_json(
        silent=True
    ) or {}

    # -----------------------------------------
    # Callback Query
    # -----------------------------------------

    callback = data.get("callback_query")

    if callback:
        callback_data = callback.get("data", "")

        if callback_data == "next":
            handle_next(callback)

        elif callback_data.startswith("answer:"):
            handle_answer(callback)

        return "OK"

    # -----------------------------------------
    # Message
    # -----------------------------------------

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:
        return "OK"

    # -----------------------------------------
    # START
    # -----------------------------------------

    if text == "/start":
        users[chat_id] = {
            **users.get(chat_id, {}),
            "mode": "main"
        }

        send_message(
            chat_id,
            "🎓 أهلاً بك في BacMind DZ 🇩🇿\n\n"
            "بوتك التدريبي للبكالوريا.\n\n"
            "🧠 فلسفة\n"
            "🇫🇷 فرنسية\n"
            "🇬🇧 إنجليزية\n"
            "🇪🇸 إسبانية\n"
            "📝 اختبارات\n"
            "🏆 إنجازات ونجوم\n"
            "📊 متابعة مستواك\n\n"
            "🚀 تدرب كل يوم، واجب عن الأسئلة، واقترب من النجاح.",
            main_keyboard()
        )

        return "OK"

    # -----------------------------------------
    # الفلسفة
    # -----------------------------------------

    if text == "🧠 الفلسفة":
        users.setdefault(chat_id, {})["mode"] = "philosophy"

        send_message(
            chat_id,
            "🧠 قسم الفلسفة:",
            philosophy_keyboard()
        )
        return "OK"

    if text == "📝 اختبار فلسفة":
        start_quiz(chat_id, "الفلسفة")
        return "OK"

    if text == "💡 مفاهيم فلسفية":
        philosophy_concepts(chat_id)
        return "OK"

    if text == "👨‍🏫 الفلاسفة":
        philosophers(chat_id)
        return "OK"

    # -----------------------------------------
    # الفرنسية
    # -----------------------------------------

    if text == "🇫🇷 الفرنسية":
        users[chat_id] = {
            **users.get(chat_id, {}),
            "mode": "language",
            "language": "الفرنسية"
        }

        send_message(
            chat_id,
            "🇫🇷 قسم الفرنسية:",
            language_keyboard("الفرنسية")
        )
        return "OK"

    if text == "📝 اختبار الفرنسية":
        start_quiz(chat_id, "الفرنسية")
        return "OK"

    # -----------------------------------------
    # الإنجليزية
    # -----------------------------------------

    if text == "🇬🇧 الإنجليزية":
        users[chat_id] = {
            **users.get(chat_id, {}),
            "mode": "language",
            "language": "الإنجليزية"
        }

        send_message(
            chat_id,
            "🇬🇧 قسم الإنجليزية:",
            language_keyboard("الإنجليزية")
        )
        return "OK"

    if text == "📝 اختبار الإنجليزية":
        start_quiz(chat_id, "الإنجليزية")
        return "OK"

    # -----------------------------------------
    # الإسبانية
    # -----------------------------------------

    if text == "🇪🇸 الإسبانية":
        users[chat_id] = {
            **users.get(chat_id, {}),
            "mode": "language",
            "language": "الإسبانية"
        }

        send_message(
            chat_id,
            "🇪🇸 قسم الإسبانية:",
            language_keyboard("الإسبانية")
        )
        return "OK"

    if text == "📝 اختبار الإسبانية":
        start_quiz(chat_id, "الإسبانية")
        return "OK"

    # -----------------------------------------
    # الكلمات
    # -----------------------------------------

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
            language
        )
        return "OK"

    # -----------------------------------------
    # مواضيع البكالوريا
    # -----------------------------------------

    if text == "📄 مواضيع البكالوريا":
        bac_topics(chat_id)
        return "OK"

    if text == "📚 آداب وفلسفة":
        send_message(
            chat_id,
            "📚 شعبة آداب وفلسفة\n\n"
            "يمكنك الآن التدرب على أسئلة الفلسفة واللغات.\n\n"
            "📄 قسم مواضيع البكالوريا سيُستخدم لإضافة مواضيع السنوات السابقة."
        )
        return "OK"

    if text == "🌍 لغات أجنبية":
        send_message(
            chat_id,
            "🌍 شعبة لغات أجنبية\n\n"
            "يمكنك التدرب على الفرنسية والإنجليزية والإسبانية.\n\n"
            "📄 سيتم تنظيم مواضيع البكالوريا حسب المادة والسنة."
        )
        return "OK"

    # -----------------------------------------
    # الإحصائيات
    # -----------------------------------------

    if text == "📊 مستواي":
        show_stats(chat_id)
        return "OK"

    # -----------------------------------------
    # الإنجازات
    # -----------------------------------------

    if text == "🏆 الإنجازات":
        achievements(chat_id)
        return "OK"

    # -----------------------------------------
    # المساعدة
    # -----------------------------------------

    if text == "ℹ️ المساعدة":
        send_message(
            chat_id,
            "ℹ️ طريقة استخدام البوت:\n\n"
            "1️⃣ اختر المادة.\n"
            "2️⃣ اضغط على الاختبار.\n"
            "3️⃣ أجب عن الأسئلة.\n"
            "4️⃣ شاهد الإجابة والشرح.\n"
            "5️⃣ تابع إحصائياتك.\n"
            "6️⃣ اجمع النجوم مع استمرارك.\n\n"
            "⭐ 10 أسئلة = بداية الطريق\n"
            "⭐⭐ 30 سؤالًا = طالب طموح\n"
            "⭐⭐⭐ 60 سؤالًا = طالب مجتهد\n"
            "⭐⭐⭐⭐ 90 سؤالًا = طالب متميز\n"
            "⭐⭐⭐⭐⭐ 120 سؤالًا = طالب قوي وذكي\n\n"
            "🎯 هدفك ليس الإجابة فقط، بل أن تتعلم من أخطائك."
        )
        return "OK"

    # -----------------------------------------
    # الرجوع
    # -----------------------------------------

    if text == "🔙 القائمة الرئيسية":
        users[chat_id] = {
            **users.get(chat_id, {}),
            "mode": "main"
        }

        send_message(
            chat_id,
            "🏠 القائمة الرئيسية:",
            main_keyboard()
        )
        return "OK"

    # -----------------------------------------
    # رسالة افتراضية
    # -----------------------------------------

    send_message(
        chat_id,
        "لم أفهم الأمر 🤔\n\n"
        "اضغط /start لفتح القائمة الرئيسية."
    )

    return "OK"


# =========================================================
# التشغيل
# =========================================================

if __name__ == "__main__":
    print("🚀 BacMind DZ starting...")
    print(f"📚 عدد مواد الأسئلة: {len(QUESTIONS)}")
    print(
        "📝 إجمالي الأسئلة:",
        sum(len(v) for v in QUESTIONS.values())
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
