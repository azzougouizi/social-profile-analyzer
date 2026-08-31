import os
import requests
from flask import Flask, request

app = Flask(__name__)

# =====================================
# Environment Variables
# =====================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

BASE_URL = "https://api.mobileapi.dev"

user_state = {}


# =====================================
# Telegram Functions
# =====================================

def send_message(chat_id, text, keyboard=None):

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN غير موجود")
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
            timeout=20
        )

        print("Telegram status:", response.status_code)

        if response.status_code != 200:
            print("Telegram response:", response.text[:1000])

    except Exception as error:
        print("Telegram error:", error)


def send_photo(chat_id, photo_url, caption):

    if not BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption
            },
            timeout=30
        )

        print("Telegram photo status:", response.status_code)

        if response.status_code != 200:
            print("Telegram photo response:", response.text[:1000])

        return response.status_code == 200

    except Exception as error:
        print("Telegram photo error:", error)
        return False


# =====================================
# MobileAPI Functions
# =====================================

def mobileapi_get(path, params=None):

    if not MOBILE_API_KEY:
        print("ERROR: MOBILE_API_KEY غير موجود في Render")
        return None

    if params is None:
        params = {}

    params["key"] = MOBILE_API_KEY

    url = BASE_URL + path

    # Logs للتشخيص
    print("================================")
    print("MobileAPI request started")
    print("MobileAPI URL:", url)
    print("MOBILE_API_KEY موجود:", bool(MOBILE_API_KEY))
    print("================================")

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        print("MobileAPI status:", response.status_code)
        print("MobileAPI response:", response.text[:2000])

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:

        print("MobileAPI ERROR:", repr(error))

        return None


def search_phones(phone_name):

    print("Searching phone:", phone_name)

    return mobileapi_get(
        "/devices/search/",
        {
            "name": phone_name,
            "page": 1
        }
    )


# =====================================
# Helpers
# =====================================

def get_value(data, keys, default="غير متوفر"):

    if not isinstance(data, dict):
        return default

    for key in keys:

        value = data.get(key)

        if value not in (None, "", [], {}):

            return value

    return default


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
# Flask Routes
# =====================================

@app.route("/", methods=["GET"])
def home():

    return "SOK DZAYR Phone Bot is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    data = request.get_json(silent=True) or {}

    print("Webhook received")

    message = data.get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    text = message.get("text", "").strip()

    print("Message:", text)

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
            "اضغط «🔎 ابحث عن هاتف» للبحث عن مواصفات أي هاتف.",
            keyboard
        )

        return "OK"


    # =================================
    # SEARCH BUTTON
    # =================================

    if text == "🔎 ابحث عن هاتف":

        user_state[chat_id] = {
            "step": "search"
        }

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف.\n\n"
            "مثال:\n"
            "iPhone 15\n"
            "Samsung Galaxy S24"
        )

        return "OK"


    # =================================
    # HELP
    # =================================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط «ابحث عن هاتف»\n"
            "2️⃣ اكتب اسم الهاتف\n"
            "3️⃣ اختر رقم الهاتف من النتائج"
        )

        return "OK"


    # =================================
    # Current State
    # =================================

    state = user_state.get(chat_id, {})

    step = state.get("step")


    # =================================
    # Search Phone
    # =================================

    if step == "search":

        result = search_phones(text)

        if result is None:

            send_message(
                chat_id,
                "❌ حدث خطأ أثناء الاتصال بـ MobileAPI.\n\n"
                "⚠️ سيتم تسجيل سبب الخطأ في Render Logs."
            )

            return "OK"


        devices = result.get("devices", [])

        if not devices:

            send_message(
                chat_id,
                f"❌ لم أجد هاتفًا باسم:\n\n{text}"
            )

            return "OK"


        devices = devices[:10]

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

            name = get_value(
                device,
                ["name"],
                "هاتف غير معروف"
            )

            brand = get_value(
                device,
                [
                    "manufacturer_name",
                    "brand_name"
                ],
                ""
            )

            result_text += (
                f"{index}. 📱 {name} {brand}\n"
            )


        result_text += (
            "\n✍️ اكتب رقم الهاتف الذي تريد اختياره."
        )

        send_message(
            chat_id,
            result_text
        )

        return "OK"


    # =================================
    # Choose Phone
    # =================================

    if step == "choose":

        try:

            number = int(text)

        except ValueError:

            send_message(
                chat_id,
                "❌ اكتب رقمًا فقط.\n\nمثال: 1"
            )

            return "OK"


        devices = state.get("devices", [])

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

        info = build_phone_info(device)

        user_state[chat_id] = {
            "step": None
        }

        send_message(
            chat_id,
            info
        )

        return "OK"


    # =================================
    # Default
    # =================================

    send_message(
        chat_id,
        "اكتب /start لبدء استخدام البوت."
    )

    return "OK"


# =====================================
# Run
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
