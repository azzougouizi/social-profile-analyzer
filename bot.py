import os
import base64
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

user_state = {}


def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    try:
        response = requests.post(
            url,
            json=data,
            timeout=20
        )
        print("Telegram:", response.status_code)
        return response.json()
    except Exception as error:
        print("Telegram error:", error)
        return None


def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return telegram_request("sendMessage", data)


def send_photo(chat_id, photo_bytes, caption):
    files = {
        "photo": (
            "phone.jpg",
            photo_bytes,
            "image/jpeg"
        )
    }

    data = {
        "chat_id": str(chat_id),
        "caption": caption
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:
        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=30
        )

        print("Telegram photo:", response.status_code)
        return response.json()

    except Exception as error:
        print("Photo error:", error)
        return None


def search_phones(phone_name):
    url = "https://api.mobileapi.dev/devices/search/"

    params = {
        "key": MOBILE_API_KEY,
        "name": phone_name,
        "page": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    print("MobileAPI search:", response.status_code)
    print("MobileAPI:", response.text[:3000])

    if response.status_code != 200:
        return None

    return response.json()


def get_device_details(device_id):
    url = f"https://api.mobileapi.dev/devices/{device_id}/"

    params = {
        "key": MOBILE_API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    print("Device details:", response.status_code)

    if response.status_code != 200:
        return None

    return response.json()


def get_device_misc(device_id):
    url = f"https://api.mobileapi.dev/devices/{device_id}/misc/"

    params = {
        "key": MOBILE_API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    print("Device misc:", response.status_code)

    if response.status_code != 200:
        return {}

    return response.json()


def get_device_images(device_id):
    url = f"https://api.mobileapi.dev/devices/{device_id}/images/"

    params = {
        "key": MOBILE_API_KEY,
        "limit": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    print("Device images:", response.status_code)

    if response.status_code != 200:
        return []

    return response.json()


def decode_image(image_b64):
    if not image_b64:
        return None

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        return base64.b64decode(image_b64)

    except Exception as error:
        print("Image decode error:", error)
        return None


def phone_caption(device, misc):
    name = device.get(
        "name",
        "هاتف غير معروف"
    )

    brand = device.get(
        "manufacturer_name",
        "غير معروف"
    )

    screen = device.get(
        "screen_resolution",
        "غير متوفر"
    )

    camera = device.get(
        "camera",
        "غير متوفر"
    )

    battery = device.get(
        "battery_capacity",
        "غير متوفر"
    )

    hardware = device.get(
        "hardware",
        "غير متوفر"
    )

    storage = device.get(
        "storage",
        "غير متوفر"
    )

    weight = device.get(
        "weight",
        "غير متوفر"
    )

    release_date = device.get(
        "release_date",
        "غير متوفر"
    )

    price = misc.get(
        "price",
        "غير متوفر"
    )

    text = (
        f"📱 {name}\n\n"
        f"🏢 الشركة: {brand}\n"
        f"💰 السعر في قاعدة MobileAPI: {price}\n\n"
        f"📺 الشاشة: {screen}\n"
        f"📸 الكاميرا: {camera}\n"
        f"🔋 البطارية: {battery}\n"
        f"⚙️ المعالج/RAM: {hardware}\n"
        f"💾 التخزين: {storage}\n"
        f"⚖️ الوزن: {weight}\n"
        f"📅 الإصدار: {release_date}\n\n"
        f"🇩🇿 سعر السوق الجزائري: سيتم ربطه بمصدر جزائري لاحقًا."
    )

    return text


@app.route("/", methods=["GET"])
def home():
    return "SOK DZAYR is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    data = request.get_json(silent=True) or {}

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
            "ابحث عن هاتف وسأعرض لك النتائج والصور والمعلومات التقنية.",
            keyboard
        )

        return "OK"

    if text == "🔎 ابحث عن هاتف":

        user_state[chat_id] = {
            "step": "search"
        }

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف.\n\n"
            "مثال:\n"
            "iPhone 15\n"
            "Samsung Galaxy S24 Ultra"
        )

        return "OK"

    if text == "📋 هواتفي المتابعة":

        send_message(
            chat_id,
            "📋 لا توجد هواتف محفوظة حاليًا."
        )

        return "OK"

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ اكتب اسم الهاتف وسأبحث عنه.\n\n"
            "ستظهر لك النتائج مع الصورة والمعلومات التقنية.\n\n"
            "🇩🇿 أسعار الجزائر سنضيفها من مصدر جزائري لاحقًا."
        )

        return "OK"

    state = user_state.get(
        chat_id,
        {}
    )

    step = state.get(
        "step"
    )

    if step == "search":

        phone_name = text

        try:

            result = search_phones(
                phone_name
            )

            if result is None:

                send_message(
                    chat_id,
                    "❌ تعذر الاتصال بـ MobileAPI."
                )

                return "OK"

            devices = result.get(
                "devices",
                []
            )

            if not devices:

                send_message(
                    chat_id,
                    f"❌ لم أجد نتائج لـ:\n\n{phone_name}\n\n"
                    "جرّب اسمًا آخر."
                )

                user_state[chat_id] = {
                    "step": None
                }

                return "OK"

            # نعرض أول 10 نتائج فقط
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

                user_state.setdefault(
                    chat_id,
                    {}
                )

                user_state[chat_id][
                    f"device_{index}"
                ] = device_id

                buttons.append([
                    {
                        "text": f"{index}️⃣ {name}",
                        "callback_data": f"phone:{device_id}"
                    }
                ])

            keyboard = {
                "inline_keyboard": buttons
            }

            send_message(
                chat_id,
                f"🔎 نتائج البحث عن:\n{phone_name}\n\n"
                "اختر الهاتف الذي تريد تفاصيله:",
                keyboard
            )

            user_state[chat_id]["step"] = "choose"

        except Exception as error:

            print("Search error:", error)

            send_message(
                chat_id,
                "❌ حدث خطأ أثناء البحث."
            )

        return "OK"

    return "OK"


@app.route("/telegram/webhook", methods=["POST"])
def duplicate_webhook():
    return "OK"


@app.route("/telegram/webhook", methods=["GET"])
def webhook_check():
    return "OK"


@app.route("/telegram/callback", methods=["POST"])
def telegram_callback():

    data = request.get_json(
        silent=True
    ) or {}

    callback = data.get(
        "callback_query",
        {}
    )

    if not callback:
        return "OK"

    callback_id = callback.get(
        "id"
    )

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

    telegram_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )

    if not callback_data.startswith(
        "phone:"
    ):
        return "OK"

    try:

        device_id = int(
            callback_data.split(
                ":",
                1
            )[1]
        )

        device = get_device_details(
            device_id
        )

        if not device:

            send_message(
                chat_id,
                "❌ تعذر الحصول على معلومات الهاتف."
            )

            return "OK"

        misc = get_device_misc(
            device_id
        )

        caption = phone_caption(
            device,
            misc
        )

        image_data = decode_image(
            device.get(
                "main_image_b64"
            )
        )

        if image_data:

            send_photo(
                chat_id,
                image_data,
                caption
            )

        else:

            images = get_device_images(
                device_id
            )

            if images:

                first_image = images[0]

                image_url = first_image.get(
                    "image_url"
                )

                image_b64 = first_image.get(
                    "image_b64"
                )

                if image_b64:

                    image_data = decode_image(
                        image_b64
                    )

                    if image_data:

                        send_photo(
                            chat_id,
                            image_data,
                            caption
                        )

                elif image_url and image_url.startswith(
                    "http"
                ):

                    telegram_request(
                        "sendPhoto",
                        {
                            "chat_id": chat_id,
                            "photo": image_url,
                            "caption": caption
                        }
                    )

                else:

                    send_message(
                        chat_id,
                        caption
                    )

            else:

                send_message(
                    chat_id,
                    caption
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
