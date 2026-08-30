
import os
import base64
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

user_state = {}

BASE_URL = "https://api.mobileapi.dev"


# =====================================
# Telegram functions
# =====================================

def send_message(chat_id, text, keyboard=None):

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

        print(
            "Telegram message:",
            response.status_code
        )

    except Exception as error:
        print(
            "Telegram error:",
            error
        )


def send_photo_url(chat_id, photo_url, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption
    }

    try:

        response = requests.post(
            url,
            json=data,
            timeout=30
        )

        print(
            "Telegram photo URL:",
            response.status_code
        )

    except Exception as error:

        print(
            "Photo URL error:",
            error
        )


def send_photo_bytes(chat_id, image_bytes, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:

        response = requests.post(
            url,
            data={
                "chat_id": str(chat_id),
                "caption": caption
            },
            files={
                "photo": (
                    "phone.jpg",
                    image_bytes
                )
            },
            timeout=30
        )

        print(
            "Telegram photo bytes:",
            response.status_code
        )

    except Exception as error:

        print(
            "Photo upload error:",
            error
        )


# =====================================
# MobileAPI
# =====================================

def mobileapi_get(path, params=None):

    if params is None:
        params = {}

    params["key"] = MOBILE_API_KEY

    url = BASE_URL + path

    try:

        response = requests.get(
            url,
            params=params,
            timeout=25
        )

        print(
            "MobileAPI request:",
            path,
            response.status_code
        )

        print(
            "MobileAPI response:",
            response.text[:1000]
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:

        print(
            "MobileAPI error:",
            error
        )

        return None


def search_phones(phone_name):

    return mobileapi_get(
        "/devices/search/",
        {
            "name": phone_name,
            "page": 1
        }
    )


def get_phone(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/"
    )


def get_phone_images(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/images/"
    )


def get_phone_misc(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/misc/"
    )


# =====================================
# Helpers
# =====================================

def get_value(data, keys, default="غير متوفر"):

    if not isinstance(data, dict):
        return default

    for key in keys:

        value = data.get(key)

        if value not in (
            None,
            "",
            []
        ):
            return value

    return default


def decode_image(value):

    if not value:
        return None

    try:

        if "," in value:

            value = value.split(
                ",",
                1
            )[1]

        return base64.b64decode(
            value
        )

    except Exception as error:

        print(
            "Image decode error:",
            error
        )

        return None


def build_phone_info(device, misc):

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
            "display"
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

    hardware = get_value(
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

    price = get_value(
        misc,
        [
            "price",
            "price_usd"
        ]
    )

    return (
        f"📱 {name}\n\n"
        f"🏢 الشركة: {brand}\n"
        f"🔢 الموديل: {model}\n\n"
        f"💰 السعر المتوفر: {price}\n\n"
        f"📺 الشاشة: {screen}\n"
        f"📸 الكاميرا: {camera}\n"
        f"🔋 البطارية: {battery}\n"
        f"⚙️ المعالج: {hardware}\n"
        f"💾 التخزين: {storage}\n"
        f"📅 الإصدار: {release}\n\n"
        f"🇩🇿 سعر الجزائر: سنربطه لاحقًا بمصدر جزائري."
    )


# =====================================
# Show phone
# =====================================

def show_phone(chat_id, device_id):

    send_message(
        chat_id,
        "⏳ جاري جلب معلومات الهاتف..."
    )

    device = get_phone(
        device_id
    )

    if not device:

        send_message(
            chat_id,
            "❌ لم أتمكن من الحصول على معلومات الهاتف."
        )

        return

    misc = get_phone_misc(
        device_id
    )

    if misc is None:
        misc = {}

    info = build_phone_info(
        device,
        misc
    )

    # محاولة الحصول على الصورة الرئيسية

    image_b64 = device.get(
        "main_image_b64"
    )

    if image_b64:

        image_bytes = decode_image(
            image_b64
        )

        if image_bytes:

            send_photo_bytes(
                chat_id,
                image_bytes,
                info
            )

            return

    # محاولة الحصول على الصور من endpoint

    images = get_phone_images(
        device_id
    )

    if images:

        if isinstance(images, list):

            first = images[0]

            if isinstance(first, dict):

                image_b64 = first.get(
                    "image_b64"
                )

                image_url = first.get(
                    "image_url"
                )

                if image_b64:

                    image_bytes = decode_image(
                        image_b64
                    )

                    if image_bytes:

                        send_photo_bytes(
                            chat_id,
                            image_bytes,
                            info
                        )

                        return

                if image_url:

                    send_photo_url(
                        chat_id,
                        image_url,
                        info
                    )

                    return

    # إذا لم نجد صورة

    send_message(
        chat_id,
        info
    )


# =====================================
# Flask
# =====================================

@app.route("/", methods=["GET"])
def home():

    return "SOK DZAYR is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

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

    chat_id = chat.get(
        "id"
    )

    text = message.get(
        "text",
        ""
    ).strip()

    if not chat_id:

        return "OK"


    # =========================
    # Start
    # =========================

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
            "ابحث عن هاتف لمعرفة معلوماته التقنية.",
            keyboard
        )

        return "OK"


    # =========================
    # Search button
    # =========================

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


    # =========================
    # Help
    # =========================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط ابحث عن هاتف\n"
            "2️⃣ اكتب اسم الهاتف\n"
            "3️⃣ ستظهر النتائج\n"
            "4️⃣ اكتب رقم الهاتف من القائمة"
        )

        return "OK"


    # =========================
    # Current state
    # =========================

    state = user_state.get(
        chat_id,
        {}
    )

    step = state.get(
        "step"
    )


    # =========================
    # Search phone
    # =========================

    if step == "search":

        result = search_phones(
            text
        )

        if not result:

            send_message(
                chat_id,
                "❌ حدث خطأ أثناء الاتصال بـ MobileAPI."
            )

            return "OK"

        devices = result.get(
            "devices",
            []
        )

        if not devices:

            send_message(
                chat_id,
                f"❌ لم أجد نتائج لـ:\n{text}"
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

            name = device.get(
                "name",
                "هاتف غير معروف"
            )

            brand = device.get(
                "manufacturer_name",
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


    # =========================
    # Choose number
    # =========================

    if step == "choose":

        try:

            number = int(text)

            devices = state.get(
                "devices",
                []
            )

            if number < 1 or number > len(devices):

                send_message(
                    chat_id,
                    "❌ اختر رقمًا موجودًا في القائمة."
                )

                return "OK"

            device = devices[
                number - 1
            ]

            device_id = device.get(
                "id"
            )

            if not device_id:

                send_message(
                    chat_id,
                    "❌ لم أجد معرف الهاتف."
                )

                return "OK"

            user_state[chat_id] = {
                "step": None
            }

            show_phone(
                chat_id,
                device_id
            )

        except ValueError:

            send_message(
                chat_id,
                "❌ اكتب رقمًا فقط، مثل: 1"
            )

        return "OK"


    # =========================
    # Default
    # =========================

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
