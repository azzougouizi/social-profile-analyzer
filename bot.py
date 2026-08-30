import os
import base64
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

user_state = {}


# =========================
# Telegram
# =========================

def telegram(method, data):
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
        print("Telegram error:", error)
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


def send_photo_url(chat_id, image_url, caption):
    return telegram(
        "sendPhoto",
        {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": caption
        }
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
                    image_bytes,
                    "image/jpeg"
                )
            },
            timeout=30
        )

        print(
            "Telegram photo:",
            response.status_code
        )

        return response.json()

    except Exception as error:
        print("Photo upload error:", error)
        return None


def answer_callback(callback_id):
    telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================
# MobileAPI
# =========================

BASE_URL = "https://api.mobileapi.dev"


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
            "MobileAPI:",
            path,
            response.status_code
        )

        print(
            response.text[:1500]
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


def search_devices(name):

    return mobileapi_get(
        "/devices/search/",
        {
            "name": name,
            "page": 1
        }
    )


def get_device(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/"
    )


def get_device_images(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/images/",
        {
            "limit": 5
        }
    )


def get_device_misc(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/misc/"
    )


# =========================
# Helpers
# =========================

def decode_base64_image(value):

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
            "Base64 image error:",
            error
        )

        return None


def get_value(data, *keys, default="غير متوفر"):

    for key in keys:

        value = data.get(key)

        if value not in (
            None,
            "",
            []
        ):
            return value

    return default


def build_phone_text(device, misc):

    name = get_value(
        device,
        "name",
        default="هاتف غير معروف"
    )

    manufacturer = get_value(
        device,
        "manufacturer_name",
        "brand_name",
        default="غير معروف"
    )

    model_number = get_value(
        device,
        "model_number",
        default="غير متوفر"
    )

    screen = get_value(
        device,
        "screen_resolution",
        default="غير متوفر"
    )

    camera = get_value(
        device,
        "camera",
        default="غير متوفر"
    )

    battery = get_value(
        device,
        "battery_capacity",
        default="غير متوفر"
    )

    hardware = get_value(
        device,
        "hardware",
        default="غير متوفر"
    )

    storage = get_value(
        device,
        "storage",
        default="غير متوفر"
    )

    weight = get_value(
        device,
        "weight",
        default="غير متوفر"
    )

    release_date = get_value(
        device,
        "release_date",
        default="غير متوفر"
    )

    colors = get_value(
        device,
        "colors",
        default="غير متوفر"
    )

    price = get_value(
        misc,
        "price",
        default="غير متوفر"
    )

    return (
        f"📱 {name}\n\n"
        f"🏢 الشركة: {manufacturer}\n"
        f"🔢 الموديل: {model_number}\n\n"
        f"💰 السعر في MobileAPI: {price}\n\n"
        f"📺 الشاشة: {screen}\n"
        f"📸 الكاميرا: {camera}\n"
        f"🔋 البطارية: {battery}\n"
        f"⚙️ المعالج/RAM: {hardware}\n"
        f"💾 التخزين: {storage}\n"
        f"⚖️ الوزن: {weight}\n"
        f"📅 تاريخ الإصدار: {release_date}\n"
        f"🎨 الألوان: {colors}\n\n"
        f"🇩🇿 سعر الجزائر: سيتم ربطه بمصدر جزائري."
    )


# =========================
# Flask
# =========================

@app.route("/", methods=["GET"])
def home():

    return "SOK DZAYR Phone Bot is running!"


@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    # =====================
    # Callback button
    # =====================

    callback = data.get(
        "callback_query"
    )

    if callback:

        callback_id = callback.get(
            "id"
        )

        callback_data = callback.get(
            "data",
            ""
        )

        callback_message = callback.get(
            "message",
            {}
        )

        chat = callback_message.get(
            "chat",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        answer_callback(
            callback_id
        )

        if callback_data.startswith(
            "phone:"
        ):

            try:

                device_id = int(
                    callback_data.split(
                        ":",
                        1
                    )[1]
                )

                show_phone(
                    chat_id,
                    device_id
                )

            except Exception as error:

                print(
                    "Callback error:",
                    error
                )

                send_message(
                    chat_id,
                    "❌ حدث خطأ أثناء عرض الهاتف."
                )

        return "OK"


    # =====================
    # Normal Telegram message
    # =====================

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


    # =====================
    # START
    # =====================

    if text == "/start":

        keyboard = {
            "keyboard": [
                ["🔎 ابحث عن هاتف"],
                ["📋 هواتفي المتابعة"],
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
            "ابحث عن أي هاتف وسأعرض لك "
            "الصور والمعلومات التقنية والسعر المتوفر.",
            keyboard
        )

        return "OK"


    # =====================
    # SEARCH
    # =====================

    if text == "🔎 ابحث عن هاتف":

        user_state[chat_id] = {
            "step": "search"
        }

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف.\n\n"
            "مثال:\n"
            "iPhone 15\n"
            "iPhone 15 Pro\n"
            "Samsung Galaxy S24 Ultra"
        )

        return "OK"


    # =====================
    # TRACKED PHONES
    # =====================

    if text == "📋 هواتفي المتابعة":

        send_message(
            chat_id,
            "📋 لا توجد هواتف محفوظة حاليًا."
        )

        return "OK"


    # =====================
    # HELP
    # =====================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط 🔎 ابحث عن هاتف\n"
            "2️⃣ اكتب اسم الهاتف\n"
            "3️⃣ اختر الهاتف من النتائج\n"
            "4️⃣ ستظهر الصورة والمواصفات والسعر.\n\n"
            "🇩🇿 سعر السوق الجزائري سنضيفه لاحقًا."
        )

        return "OK"


    # =====================
    # USER SEARCH TEXT
    # =====================

    state = user_state.get(
        chat_id,
        {}
    )

    step = state.get(
        "step"
    )

    if step == "search":

        search_text = text

        try:

            result = search_devices(
                search_text
            )

            if result is None:

                send_message(
                    chat_id,
                    "❌ حدث خطأ في الاتصال بـ MobileAPI."
                )

                return "OK"

            devices = result.get(
                "devices",
                []
            )

            if not devices:

                send_message(
                    chat_id,
                    f"❌ لم أجد هاتفًا مطابقًا لـ:\n\n"
                    f"{search_text}\n\n"
                    f"جرّب اسمًا آخر."
                )

                user_state[chat_id] = {
                    "step": None
                }

                return "OK"


            # =================
            # First 10 results
            # =================

            devices = devices[:10]

            buttons = []

            for index, device in enumerate(
                devices,
                start=1
            ):

                device_id = device.get(
                    "id"
                )

                name = device.get(
                    "name",
                    "هاتف"
                )

                if not device_id:
                    continue

                buttons.append([
                    {
                        "text": f"{index}️⃣ {name}",
                        "callback_data": (
                            f"phone:{device_id}"
                        )
                    }
                ])

            keyboard = {
                "inline_keyboard": buttons
            }

            total = result.get(
                "total",
                len(devices)
            )

            send_message(
                chat_id,
                f"🔎 نتائج البحث عن:\n"
                f"{search_text}\n\n"
                f"📊 عدد النتائج: {total}\n\n"
                f"اختر الهاتف:",
                keyboard
            )

            user_state[chat_id] = {
                "step": "choose"
            }

        except Exception as error:

            print(
                "Search error:",
                error
            )

            send_message(
                chat_id,
                "❌ حدث خطأ أثناء البحث."
            )

        return "OK"


    # =====================
    # DEFAULT
    # =====================

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة."
    )

    return "OK"


# =========================
# Show phone
# =========================

def show_phone(chat_id, device_id):

    send_message(
        chat_id,
        "⏳ جاري جلب معلومات الهاتف..."
    )

    device = get_device(
        device_id
    )

    if not device:

        send_message(
            chat_id,
            "❌ لم أتمكن من جلب معلومات الهاتف."
        )

        return


    misc = get_device_misc(
        device_id
    )

    if misc is None:
        misc = {}


    caption = build_phone_text(
        device,
        misc
    )


    # =====================
    # Main image from detail
    # =====================

    main_image = device.get(
        "main_image_b64"
    )

    if main_image:

        image_bytes = decode_base64_image(
            main_image
        )

        if image_bytes:

            send_photo_bytes(
                chat_id,
                image_bytes,
                caption
            )

            return


    # =====================
    # Gallery image
    # =====================

    images = get_device_images(
        device_id
    )

    if images and isinstance(
        images,
        list
    ):

        first_image = images[0]

        image_url = first_image.get(
            "image_url"
        )

        image_b64 = first_image.get(
            "image_b64"
        )


        if image_b64:

            image_bytes = decode_base64_image(
                image_b64
            )

            if image_bytes:

                send_photo_bytes(
                    chat_id,
                    image_bytes,
                    caption
                )

                return


        if image_url and image_url.startswith(
            "http"
        ):

            send_photo_url(
                chat_id,
                image_url,
                caption
            )

            return


    # =====================
    # No image
    # =====================

    send_message(
        chat_id,
        caption
    )


# =========================
# Start server
# =========================

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
