import os
import re
import random
import requests

from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# الإعدادات
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_CODE = "1230"

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
}

TIMEOUT = 20


# =========================================================
# أدوات عامة
# =========================================================

def get_page(url):
    """تحميل صفحة ويب."""
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        return response.text

    except Exception as e:
        print(f"GET ERROR: {url} -> {e}")
        return None


def clean_text(text):
    """تنظيف النص."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def send_message(chat_id, text):
    """إرسال رسالة Telegram."""
    if not BOT_TOKEN:
        print("BOT_TOKEN is missing.")
        return False

    try:
        response = requests.post(
            f"{TELEGRAM}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=15
        )

        print(
            "Telegram:",
            response.status_code,
            response.text[:300]
        )

        return response.ok

    except Exception as e:
        print("Telegram ERROR:", e)
        return False


# =========================================================
# القائمة الرئيسية
# =========================================================

def main_menu(chat_id):

    keyboard = {
        "keyboard": [
            ["📖 آية اليوم", "🤲 حديث اليوم"],
            ["💎 نصيحة إيمانية", "📿 الأذكار"],
            ["🎙️ بودكاست إيماني", "📚 فائدة إسلامية"],
            ["🔄 تحديث المحتوى"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

    send_message(
        chat_id,
        "🕌 أهلاً بك في البوت الإسلامي\n\n"
        "اختر ما تريد من القائمة:",
    )

    try:
        requests.post(
            f"{TELEGRAM}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "👇 اختر الخدمة:",
                "reply_markup": keyboard
            },
            timeout=15
        )

    except Exception as e:
        print("MENU ERROR:", e)


# =========================================================
# آية اليوم
# =========================================================

# أسماء السور
SURAH_NAMES = {
    1: "الفاتحة",
    2: "البقرة",
    3: "آل عمران",
    4: "النساء",
    5: "المائدة",
    6: "الأنعام",
    7: "الأعراف",
    8: "الأنفال",
    9: "التوبة",
    10: "يونس",
    11: "هود",
    12: "يوسف",
    13: "الرعد",
    14: "إبراهيم",
    15: "الحجر",
    16: "النحل",
    17: "الإسراء",
    18: "الكهف",
    19: "مريم",
    20: "طه",
    21: "الأنبياء",
    22: "الحج",
    23: "المؤمنون",
    24: "النور",
    25: "الفرقان",
    26: "الشعراء",
    27: "النمل",
    28: "القصص",
    29: "العنكبوت",
    30: "الروم",
    31: "لقمان",
    32: "السجدة",
    33: "الأحزاب",
    34: "سبأ",
    35: "فاطر",
    36: "يس",
    37: "الصافات",
    38: "ص",
    39: "الزمر",
    40: "غافر",
    41: "فصلت",
    42: "الشورى",
    43: "الزخرف",
    44: "الدخان",
    45: "الجاثية",
    46: "الأحقاف",
    47: "محمد",
    48: "الفتح",
    49: "الحجرات",
    50: "ق",
    51: "الذاريات",
    52: "الطور",
    53: "النجم",
    54: "القمر",
    55: "الرحمن",
    56: "الواقعة",
    57: "الحديد",
    58: "المجادلة",
    59: "الحشر",
    60: "الممتحنة",
    61: "الصف",
    62: "الجمعة",
    63: "المنافقون",
    64: "التغابن",
    65: "الطلاق",
    66: "التحريم",
    67: "الملك",
    68: "القلم",
    69: "الحاقة",
    70: "المعارج",
    71: "نوح",
    72: "الجن",
    73: "المزمل",
    74: "المدثر",
    75: "القيامة",
    76: "الإنسان",
    77: "المرسلات",
    78: "النبأ",
    79: "النازعات",
    80: "عبس",
    81: "التكوير",
    82: "الانفطار",
    83: "المطففين",
    84: "الانشقاق",
    85: "البروج",
    86: "الطارق",
    87: "الأعلى",
    88: "الغاشية",
    89: "الفجر",
    90: "البلد",
    91: "الشمس",
    92: "الليل",
    93: "الضحى",
    94: "الشرح",
    95: "التين",
    96: "العلق",
    97: "القدر",
    98: "البينة",
    99: "الزلزلة",
    100: "العاديات",
    101: "القارعة",
    102: "التكاثر",
    103: "العصر",
    104: "الهمزة",
    105: "الفيل",
    106: "قريش",
    107: "الماعون",
    108: "الكوثر",
    109: "الكافرون",
    110: "النصر",
    111: "المسد",
    112: "الإخلاص",
    113: "الفلق",
    114: "الناس",
}


def get_random_ayah():

    # نستخدم آية عشوائية من القرآن.
    # المصدر هو صفحة الآية نفسها في Quran.com.
    surah = random.randint(1, 114)

    # نستخدم رقم آية صغيرًا ثم نتحقق من الصفحة.
    # إذا كانت الآية غير موجودة نعيد المحاولة.
    for _ in range(10):

        ayah = random.randint(1, 20)

        url = f"https://quran.com/ar/{surah}:{ayah}"

        html = get_page(url)

        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        text = clean_text(
            soup.get_text(" ", strip=True)
        )

        if not text:
            continue

        # البحث عن صيغة السورة والآية
        surah_name = SURAH_NAMES.get(
            surah,
            f"السورة {surah}"
        )

        # نبحث عن بداية النص بعد العنوان
        pattern = re.compile(
            rf"{re.escape(surah_name)}\s+{surah}:{ayah}\s+(.+?)(?:صفحة|جزء|اقرأ التفسير)",
            re.IGNORECASE
        )

        match = pattern.search(text)

        if match:

            verse = clean_text(
                match.group(1)
            )

            # إزالة بعض العناصر الزائدة
            if len(verse) > 10:

                return (
                    f"📖 آية اليوم\n\n"
                    f"﴿{verse}﴾\n\n"
                    f"📚 سورة {surah_name} — الآية {ayah}\n\n"
                    f"🔗 المصدر: Quran.com"
                )

    return (
        "📖 آية اليوم\n\n"
        "تعذر جلب آية من المصدر الآن.\n"
        "حاول مرة أخرى بعد قليل."
    )


# =========================================================
# حديث اليوم
# =========================================================

def get_hadith():

    # الدرر السنية توفر صفحات حديثية قابلة للقراءة.
    # نستخدم مجموعة صفحات بحثية معروفة كمصدر.
    urls = [
        "https://dorar.net/hadith/sharh/139",
        "https://dorar.net/hadith/sharh/149",
        "https://dorar.net/hadith/sharh/155",
    ]

    random.shuffle(urls)

    for url in urls:

        html = get_page(url)

        if not html:
            continue

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        text = clean_text(
            soup.get_text(" ", strip=True)
        )

        if not text:
            continue

        # محاولة العثور على نص حديث
        keywords = [
            "خلاصة حكم المحدث",
            "الراوي",
            "المصدر"
        ]

        if not all(
            keyword in text
            for keyword in keywords
        ):
            continue

        # استخراج جزء مناسب من الصفحة
        start = text.find("خلاصة حكم المحدث")

        if start > 0:

            beginning = text[:start]

            # آخر فقرة قبل معلومات التخريج
            parts = re.split(
                r"﻿|الراوي",
                beginning
            )

            candidate = parts[-1].strip()

            if len(candidate) > 30:

                return (
                    "🤲 حديث اليوم\n\n"
                    f"«{candidate[:900]}»\n\n"
                    "📚 المصدر: الموسوعة الحديثية - "
                    "الدرر السنية\n\n"
                    "⚠️ يُفضّل الرجوع إلى صفحة المصدر "
                    "للتأكد من التفاصيل والتخريج."
                )

    return (
        "🤲 حديث اليوم\n\n"
        "تعذر جلب الحديث من المصدر الآن.\n"
        "حاول مرة أخرى بعد قليل."
    )


# =========================================================
# نصائح إيمانية
# =========================================================

# هذه ليست أحاديث ولا ننسبها للنبي ﷺ.
# هي نصائح عامة بصياغة البوت.

TIPS = [
    "حافظ على الصلاة في وقتها، واجعلها من أولويات يومك.",
    "اجعل لك وردًا يوميًا من القرآن ولو كان قليلًا، فالمداومة خير.",
    "أكثر من الاستغفار خلال يومك، وخصوصًا عندما تشعر بالضيق.",
    "بر الوالدين من أعظم أبواب الخير، فاحرص على الكلام الطيب معهما.",
    "لا تحتقر عملًا صالحًا صغيرًا؛ فالاستمرار على الخير مهم.",
    "إذا أخطأت فلا تيأس، بادر بالتوبة والإصلاح ولا تؤجل الخير.",
    "اجعل لسانك عامرًا بالذكر أثناء انتظارك أو تنقلك أو عملك.",
    "الصدقة ليست بالمال فقط؛ الكلمة الطيبة والمعونة والابتسامة من الخير.",
    "ابتعد عن الغيبة والنميمة، واحفظ لسانك ما استطعت.",
    "خصص وقتًا يوميًا للدعاء بهدوء وخشوع.",
]


def show_tip():

    tip = random.choice(TIPS)

    return (
        "💎 نصيحة إيمانية\n\n"
        f"{tip}\n\n"
        "🌿 نسأل الله أن ينفعنا وإياكم."
    )


# =========================================================
# الأذكار
# =========================================================

def get_azkar():

    url = (
        "https://www.islamweb.net/"
        "ar/article/178309/"
    )

    html = get_page(url)

    if not html:

        return (
            "📿 الأذكار\n\n"
            "تعذر الوصول إلى مصدر الأذكار الآن."
        )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = clean_text(
        soup.get_text(" ", strip=True)
    )

    if not text:

        return (
            "📿 الأذكار\n\n"
            "تعذر استخراج الأذكار من المصدر."
        )

    # نبحث عن بداية أذكار الصباح
    start = text.find("أذكار الصباح")

    if start == -1:

        return (
            "📿 الأذكار\n\n"
            "تعذر استخراج أذكار الصباح حاليًا."
        )

    content = text[start:]

    # لا نرسل صفحة ضخمة جدًا إلى Telegram
    content = content[:3500]

    return (
        "📿 أذكار الصباح والمساء\n\n"
        f"{content}\n\n"
        "📚 المصدر: إسلام ويب"
    )


# =========================================================
# بودكاست إيماني
# =========================================================

def get_podcast():

    # لا نخترع روابط صوتية.
    # نستخدم صفحة بحث/استماع يمكن للمستخدم متابعتها.
    return (
        "🎙️ بودكاست إيماني\n\n"
        "يمكنك الاستماع إلى محتوى إسلامي صوتي "
        "من خلال المشاريع والمواقع الإسلامية الموثوقة.\n\n"
        "🔊 للاستماع إلى القرآن الكريم والتلاوات:\n"
        "https://quran.com/ar\n\n"
        "🎧 اختر السورة والقارئ من الموقع."
    )


# =========================================================
# فائدة إسلامية
# =========================================================

def get_islamic_info():

    facts = [
        (
            "📚 فائدة إسلامية\n\n"
            "القرآن الكريم هو كلام الله تعالى، "
            "وتلاوته عبادة، والتدبر فيه يعين المسلم "
            "على فهم معانيه والعمل بها."
        ),
        (
            "📚 فائدة إسلامية\n\n"
            "الذكر من أعظم الأعمال، وقد أمر الله "
            "تعالى بالإكثار من ذكره."
        ),
        (
            "📚 فائدة إسلامية\n\n"
            "التوبة باب عظيم من أبواب الرحمة، "
            "فلا ينبغي للمسلم أن ييأس من رحمة الله."
        ),
        (
            "📚 فائدة إسلامية\n\n"
            "من المهم عند نقل الحديث عن النبي ﷺ "
            "التأكد من صحة الحديث ومصدره قبل نشره."
        ),
        (
            "📚 فائدة إسلامية\n\n"
            "من أجمل ما يعين على الاستمرار في الطاعة "
            "أن يجعل المسلم لنفسه أعمالًا صالحة "
            "يستطيع المداومة عليها."
        ),
    ]

    return random.choice(facts)


# =========================================================
# معالجة الأوامر
# =========================================================

def handle_message(chat_id, text):

    if text == "/start":

        send_message(
            chat_id,
            "👋 أهلاً وسهلاً بك في البوت الإسلامي.\n\n"
            "🕌 محتوى إيماني، آيات، أحاديث، "
            "أذكار ونصائح.\n\n"
            "🔐 أرسل رمز الدخول للمتابعة."
        )

        return

    if text == ACCESS_CODE:

        main_menu(chat_id)

        return

    if text == "📖 آية اليوم":

        send_message(
            chat_id,
            "⏳ جاري جلب آية اليوم..."
        )

        send_message(
            chat_id,
            get_random_ayah()
        )

        return

    if text == "🤲 حديث اليوم":

        send_message(
            chat_id,
            "⏳ جاري البحث عن حديث من مصدر حديثي..."
        )

        send_message(
            chat_id,
            get_hadith()
        )

        return

    if text == "💎 نصيحة إيمانية":

        send_message(
            chat_id,
            show_tip()
        )

        return

    if text == "📿 الأذكار":

        send_message(
            chat_id,
            "⏳ جاري جلب الأذكار..."
        )

        send_message(
            chat_id,
            get_azkar()
        )

        return

    if text == "🎙️ بودكاست إيماني":

        send_message(
            chat_id,
            get_podcast()
        )

        return

    if text == "📚 فائدة إسلامية":

        send_message(
            chat_id,
            get_islamic_info()
        )

        return

    if text == "🔄 تحديث المحتوى":

        send_message(
            chat_id,
            "🔄 تم تحديث المحتوى.\n\n"
            "اختر الخدمة التي تريدها من القائمة."
        )

        main_menu(chat_id)

        return

    send_message(
        chat_id,
        "❗ اختر خدمة من القائمة الموجودة أسفل الشاشة."
    )


# =========================================================
# Webhook Telegram
# =========================================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    message = data.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get("id")

    if not chat_id:
        return "OK"

    text = message.get(
        "text",
        ""
    ).strip()

    handle_message(
        chat_id,
        text
    )

    return "OK"


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def home():

    return "Islamic Telegram Bot is running"


# =========================================================
# Health Check
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "bot": "Islamic Telegram Bot"
    }


# =========================================================
# تشغيل Flask
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
