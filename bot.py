import os
import base64
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

BASE_URL = "https://api.mobileapi.dev"

user_state = {}


# =====================================
# Telegram
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

        print("Telegram:", response.status_code)
        print("Telegram response:", response.text[:500])

    except Exception as error:
        print("Telegram error:", error)


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
                "photo": ("phone.jpg", image_bytes)
            },
            timeout=30
        )

        print("Telegram photo:", response.status_code)
        print("Telegram photo response:", response.text[:500])

        return response.ok

    except Exception as error:
        print("Photo error:", error)
        return False


def send_photo_url(chat_id, photo_url, caption):
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

        print("Telegram photo URL:", response.status_code)
        print("Telegram photo URL response:", response.text[:500])

        return response.ok

    except Exception as error:
        print("Photo URL error:", error)
        return False


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
            timeout=30
        )

        print("MobileAPI:", path, response.status_code)
        print("MobileAPI response:", response.text[:2000])

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:

        print("MobileAPI error:", error)

        return None


def search_phones(phone_name):

    return mobileapi_get(
        "/devices/search/",
        {
            "name": phone_name,
            "page": 1
        }
    )


def get_phone_images(device_id):

    return mobileapi_get(
        f"/devices/{device_id}/images/"
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


def decode_base64_image(value):

    if not value:
        return None

    try:

        if isinstance(value, str):

            if "," in value:
                value = value.split(",", 1)[1]

            return base64.b64decode(value)

    except Exception as error:

        print("Base64 image error:", error)

    return None


# =====================================
# Algeria price
# =====================================

def search_algeria_prices(phone_name):

    """
    محاولة جلب أسعار الجزائر.
    إذا لم يتوفر مصدر الأسعار أو تغيرت استجابته،
    لا يتوقف البوت؛ فقط يعرض أن السعر غير متوفر.
    """

    url = "https://api.teno-store.com/v1/products"

    params = {
        "category": "telephones",
        "q": phone_name,
        "sort": "price_asc",
        "limit": 5
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        print(
            "Algeria price status:",
            response.status_code
        )

        print(
            "Algeria price response:",
            response.text[:2000]
        )

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            for key in [
                "data",
                "products",
                "results",
                "items"
            ]:

                value = data.get(key)

                if isinstance(value, list):
                    return value

        return []

    except Exception as error:

        print(
            "Algeria price error:",
            error
        )

        return []


def format_algeria_prices(phone_name):

    products = search_algeria_prices(phone_name)

    if not products:

        return (
            "🇩🇿 السعر في الجزائر: "
            "غير متوفر حاليًا."
        )

    lines = [
        "\n🇩🇿 عروض وأسعار الجزائر:"
    ]

    count = 0

    for product in products:

        if not isinstance(product, dict):
            continue

        name = get_value(
            product,
            [
                "name",
                "title",
                "product_name"
            ],
            phone_name
        )

        price = get_value(
            product,
            [
                "price",
                "priceDzd",
                "price_dzd",
                "priceMinor"
            ],
            "غير متوفر"
        )

        store = get_value(
            product,
            [
                "store",
                "store_name",
                "seller",
                "shop",
                "merchant"
            ],
            "غير متوفر"
        )

        location = get_value(
            product,
            [
                "location",
                "city",
                "wilaya",
                "store_location"
            ],
            "غير متوفر"
        )

        product_url = get_value(
            product,
            [
                "url",
                "product_url",
                "link"
            ],
            ""
        )

        # بعض APIs تخزن السعر بوحدة أصغر
        if isinstance(price, (int, float)):

            if "priceMinor" in product:

                price = price / 100

            price_text = f"{price:,.0f} دج"

        else:

            price_text = str(price)

        lines.append(
            f"\n📱 {name}"
            f"\n💰 السعر: {price_text}"
            f"\n🏪 المتجر: {store}"
        )

        if location != "غير متوفر":

            lines.append(
                f"\n📍 الموقع: {location}"
            )

        if product_url:

            lines.append(
                f"\n🔗 {product_url}"
            )

        count += 1

        if count >= 5:
            break

    if count == 0:

        return (
            "🇩🇿 السعر في الجزائر: "
            "غير متوفر حاليًا."
        )

    return "\n".join(lines)


# =====================================
# Phone information
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

    ram = get_value(
        device,
        [
            "ram",
            "memory"
        ]
    )

    release = get_value(
        device,
        [
            "release_date",
            "released"
        ]
    )

    imei = get_value(
        device,
        [
            "imei"
        ],
        "غير متوفر"
    )

    match = get_value(
        device,
        [
            "match_certainty"
        ],
        "غير متوفر"
    )

    return (
        f"📱 {name}\n\n"
        f"🏢 الشركة: {brand}\n"
        f"🔢 الموديل: {model}\n"
        f"🎯 دقة المطابقة: {match}\n\n"
        f"📺 الشاشة: {screen}\n"
        f"📸 الكاميرا: {camera}\n"
        f"🔋 البطارية: {battery}\n"
        f"⚙️ المعالج: {processor}\n"
        f"🧠 RAM: {ram}\n"
        f"💾 التخزين: {storage}\n"
        f"📅 الإصدار: {release}\n"
        f"🔐 IMEI: {imei}\n"
    )


# =====================================
# Image
# =====================================

def send_phone_image(chat_id, device, caption):

    # 1. Base64 داخل نتيجة البحث

    for key in [
        "main_image_b64",
        "image_b64",
        "thumbnail_b64"
    ]:

        image = decode_base64_image(
            device.get(key)
        )

        if image:

            print(
                "Image found:",
                key
            )

            if send_photo_bytes(
                chat_id,
                image,
                caption
            ):

                return True


    # 2. رابط صورة داخل نتيجة البحث

    for key in [
        "main_image",
        "main_image_url",
        "image_url",
        "thumbnail_url"
    ]:

        value = device.get(key)

        if (
            isinstance(value, str)
            and value.startswith("http")
        ):

            print(
                "Image URL found:",
                key
            )

            if send_photo_url(
                chat_id,
                value,
                caption
            ):

                return True


    # 3. Endpoint الصور

    device_id = device.get("id")

    if device_id:

        images = get_phone_images(
            device_id
        )

        print(
            "Images response:",
            images
        )

        if isinstance(images, dict):

            image_list = (
                images.get("images")
                or images.get("data")
                or images.get("results")
                or []
            )

        elif isinstance(images, list):

            image_list = images

        else:

            image_list = []


        for image_data in image_list:

            if not isinstance(
                image_data,
                dict
            ):

                continue


            for key in [
                "image_b64",
                "main_image_b64",
                "thumbnail_b64"
            ]:

                image = decode_base64_image(
                    image_data.get(key)
                )

                if image:

                    if send_photo_bytes(
                        chat_id,
                        image,
                        caption
                    ):

                        return True


            for key in [
                "image_url",
                "url",
                "thumbnail_url"
            ]:

                value = image_data.get(key)

                if (
                    isinstance(value, str)
                    and value.startswith("http")
                ):

                    if send_photo_url(
                        chat_id,
                        value,
                        caption
                    ):

                        return True


    return False


# =====================================
# Show phone
# =====================================

def show_phone(chat_id, device):

    send_message(
        chat_id,
        "⏳ جاري تجهيز معلومات الهاتف..."
    )

    if not isinstance(
        device,
        dict
    ):

        send_message(
            chat_id,
            "❌ بيانات الهاتف غير صحيحة."
        )

        return


    info = build_phone_info(
        device
    )


    # اسم الهاتف

    phone_name = get_value(
        device,
        ["name"],
        "هاتف"
    )


    # إضافة أسعار الجزائر

    try:

        algeria_prices = format_algeria_prices(
            phone_name
        )

        info += "\n" + algeria_prices

    except Exception as error:

        print(
            "Price formatting error:",
            error
        )

        info += (
            "\n🇩🇿 السعر في الجزائر: "
            "غير متوفر حاليًا."
        )


    # إرسال الصورة

    image_sent = send_phone_image(
        chat_id,
        device,
        info
    )


    # إذا لم توجد صورة

    if not image_sent:

        send_message(
            chat_id,
            info
        )


# =====================================
# Home
# =====================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return "SOK DZAYR is running!"


# =====================================
# Telegram Webhook
# =====================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
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
            "ابحث عن هاتف لمعرفة معلوماته التقنية "
            "وسعره في الجزائر إذا كان متوفرًا.",
            keyboard
        )

        return "OK"


    # =================================
    # SEARCH
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
            "Samsung Galaxy S24\n"
            "Xiaomi Redmi Note 13"
        )

        return "OK"


    # =================================
    # HELP
    # =================================

    if text == "ℹ️ المساعدة":

        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط «🔎 ابحث عن هاتف»\n"
            "2️⃣ اكتب اسم الهاتف\n"
            "3️⃣ اختر رقم الهاتف\n"
            "4️⃣ ستظهر المواصفات والصورة\n"
            "5️⃣ سيحاول البوت إظهار أسعار الجزائر"
        )

        return "OK"


    # =================================
    # STATE
    # =================================

    state = user_state.get(
        chat_id,
        {}
    )

    step = state.get(
        "step"
    )


    # =================================
    # SEARCH PHONE
    # =================================

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
                f"{index}. 📱 {name}"
                f" {brand}\n"
            )


        result_text += (
            "\n✍️ اكتب رقم الهاتف."
        )


        send_message(
            chat_id,
            result_text
        )

        return "OK"


    # =================================
    # CHOOSE PHONE
    # =================================

    if step == "choose":

        try:

            number = int(text)

        except ValueError:

            send_message(
                chat_id,
                "❌ اكتب رقمًا فقط، مثل: 1"
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


        device = devices[
            number - 1
        ]


        user_state[chat_id] = {
            "step": None
        }


        show_phone(
            chat_id,
            device
        )

        return "OK"


    # =================================
    # DEFAULT
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
