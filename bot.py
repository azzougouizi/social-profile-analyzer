import os
import requests
from flask import Flask, request

app = Flask(__name__)

# =====================================
# الإعدادات
# =====================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

BASE_URL = "https://api.mobileapi.dev"

user_state = {}


# =====================================
# إرسال رسالة Telegram
# =====================================

def send_message(chat_id, text, keyboard=None):

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN غير موجود", flush=True)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    try:
        response = requests.post(
            url,
            json=data,
            timeout=30
        )

        print(
            "Telegram status:",
            response.status_code,
            flush=True
        )

        if response.status_code != 200:
            print(
                "Telegram response:",
                response.text[:500],
                flush=True
            )

    except Exception as error:
        print(
            "Telegram error:",
            repr(error),
            flush=True
        )


# =====================================
# الاتصال بـ MobileAPI
# =====================================

def mobileapi_get(path, params=None):

    if not MOBILE_API_KEY:
        return {
            "error": "MOBILE_API_KEY غير موجود في Render"
        }

    if params is None:
        params = {}

    # نسخة جديدة حتى لا نعدل البيانات الأصلية
    params = dict(params)

    params["key"] = MOBILE_API_KEY

    url = BASE_URL + path

    try:

        print(
            "MobileAPI request:",
            url,
            flush=True
        )

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        print(
            "MobileAPI status:",
            response.status_code,
            flush=True
        )

        # لا نطبع المفتاح السري
        print(
            "MobileAPI response:",
            response.text[:1000],
            flush=True
        )

        if response.status_code != 200:
            return {
                "error": f"HTTP {response.status_code}",
                "details": response.text[:300]
            }

        try:
            return response.json()

        except ValueError:
            return {
                "error": "استجابة MobileAPI ليست JSON",
                "details": response.text[:300]
            }

    except requests.exceptions.Timeout:
        return {
            "error": "انتهت مهلة الاتصال بـ MobileAPI"
        }

    except requests.exceptions.ConnectionError:
        return {
            "error": "تعذر الاتصال بـ MobileAPI"
        }

    except Exception as error:
        return {
            "error": str(error)
        }


# =====================================
# البحث عن الهواتف
# =====================================

def search_phones(phone_name):

    return mobileapi_get(
        "/devices/search/",
        {
            "name": phone_name,
            "page": 1
        }
    )


# =====================================
# دوال مساعدة
# =====================================

def get_value(data, keys, default="غير متوفر"):

    if not isinstance(data, dict):
        return default

    for key in keys:

        value = data.get(key)

        if value not in (
            None,
            "",
            [],
            {}
        ):
            return value

    return default


# =====================================
# بناء معلومات الهاتف
# =====================================

def build_phone_info(device):

    name = get_value(
        device,
        ["name"],
        "هاتف غير معروف"
    )

    brand = get_value(
        device,
        [
            "manufacturer_name",
            "brand_name",
            "manufacturer"
        ]
    )

    model = get_value(
        device,
        [
            "model_number",
            "model"
        ]
    )

    screen = get_value(
        device,
        [
            "screen_resolution",
            "display",
            "screen"
        ]
    )

    camera = get_value(
        device,
        [
            "camera",
            "camera_specs"
        ]
    )

    battery = get_value(
        device,
        [
            "battery_capacity",
            "battery"
        ]
    )

    processor = get_value(
        device,
        [
            "hardware",
            "processor",
            "chipset"
        ]
    )

    storage = get_value(
        device,
        [
            "storage",
            "internal_memory"
        ]
    )

    release = get_value(
        device,
        [
            "release_date",
            "released"
        ]
    )

    return (
        f"📱 {name}\n\n"
        f"🏢 الشركة: {brand}\n"
        f"🔢 الموديل: {model}\n\n"
        f"📺 الشاشة: {screen}\n"
        f"📸 الكاميرا: {camera}\n"
        f"🔋 البطارية: {battery}\n"
        f"⚙️ المعالج: {processor}\n"
        f"💾 التخزين: {storage}\n"
        f"📅 الإصدار: {release}"
    )


# =====================================
# الصفحة الرئيسية
# =====================================

@app.route("/", methods=["GET"])
def home():

    return "SOK DZAYR Phone Bot is running!"


# =====================================
# Telegram Webhook
# =====================================

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    data = request.get_json(silent=True) or {}

    message = data.get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    text = message.get("text", "").strip()

    print(
        "Telegram message received:",
        text,
        flush=True
    )

    if not chat_id:
        return "OK"


    # =================================
    # START
    # =================================

    if text == "/start":

        keyboard = {
            "keyboard": [
                ["🔎 ابحث عن هاتف"],
                ["ℹ️ المساعدة"]
            ],
            "resize_keyboard": True
        }

        user_state[chat_id] = {
            "step": None
        }

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في SOK DZAYR 📱\n\n"
            "اضغط على «🔎 ابحث عن هاتف» للبحث عن هاتف.",
            keyboard
        )

        return "OK"


    # =================================
    # زر البحث
    # =================================

    if text == "🔎 ابحث عن هاتف":

        user_state[chat_id] = {
            "step": "search"
        }

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف الذي تريد البحث عنه.\n\n"
            "مثال:\n"
            "iPhone 15\n"
            "Samsung Galaxy S24"
        )

        return "OK"


    # =================================
    # المساعدة
    # =================================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط «🔎 ابحث عن هاتف»\n"
            "2️⃣ اكتب اسم الهاتف\n"
            "3️⃣ اختر رقم الهاتف من النتائج\n"
            "4️⃣ ستظهر معلومات الهاتف"
        )

        return "OK"


    # =================================
    # حالة المستخدم
    # =================================

    state = user_state.get(
        chat_id,
        {}
    )

    step = state.get("step")


    # =================================
    # البحث
    # =================================

    if step == "search":

        send_message(
            chat_id,
            "⏳ جاري البحث..."
        )

        result = search_phones(text)


        # فحص الأخطاء
        if result is None:

            send_message(
                chat_id,
                "❌ لم تصل أي استجابة من MobileAPI."
            )

            return "OK"


        if not isinstance(result, dict):

            send_message(
                chat_id,
                "❌ استجابة غير صحيحة من MobileAPI."
            )

            return "OK"


        if result.get("error"):

            error_text = result.get(
                "error",
                "خطأ غير معروف"
            )

            send_message(
                chat_id,
                f"❌ خطأ أثناء الاتصال بـ MobileAPI:\n\n"
                f"{error_text}"
            )

            return "OK"


        devices = result.get(
            "devices",
            []
        )


        # بعض APIs تستخدم results بدل devices
        if not devices:
            devices = result.get(
                "results",
                []
            )


        if not isinstance(devices, list):
            devices = []


        if not devices:

            send_message(
                chat_id,
                f"❌ لم أجد نتائج للهاتف:\n\n{text}"
            )

            return "OK"


        devices = devices[:10]


        # حفظ النتائج
        user_state[chat_id] = {
            "step": "choose",
            "devices": devices
        }


        result_text = (
            f"🔎 نتائج البحث عن:\n{text}\n\n"
        )


        for index, device in enumerate(
            devices,
            start=1
        ):

            if not isinstance(device, dict):
                continue

            name = get_value(
                device,
                ["name"],
                "هاتف غير معروف"
            )

            brand = get_value(
                device,
                [
                    "manufacturer_name",
                    "brand_name",
                    "manufacturer"
                ],
                ""
            )

            result_text += (
                f"{index}. 📱 {name}"
            )

            if brand:
                result_text += f" — {brand}"

            result_text += "\n"


        result_text += (
            "\n✍️ اكتب رقم الهاتف الذي تريد اختياره.\n"
            "مثال: 1"
        )


        send_message(
            chat_id,
            result_text
        )

        return "OK"


    # =================================
    # اختيار الهاتف
    # =================================

    if step == "choose":

        try:
            number = int(text.strip())

        except ValueError:

            send_message(
                chat_id,
                "❌ اكتب رقمًا فقط.\n\n"
                "مثال: 1"
            )

            return "OK"


        devices = state.get(
            "devices",
            []
        )


        if (
            number < 1
            or number > len(devices)
        ):

            send_message(
                chat_id,
                "❌ اختر رقمًا موجودًا في القائمة."
            )

            return "OK"


        device = devices[number - 1]


        if not isinstance(device, dict):

            send_message(
                chat_id,
                "❌ حدث خطأ في بيانات الهاتف."
            )

            return "OK"


        info = build_phone_info(device)


        # إنهاء حالة الاختيار
        user_state[chat_id] = {
            "step": None
        }


        send_message(
            chat_id,
            info
        )

        return "OK"


    # =================================
    # رسالة افتراضية
    # =================================

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة الرئيسية."
    )

    return "OK"


# =====================================
# تشغيل التطبيق
# =====================================

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
