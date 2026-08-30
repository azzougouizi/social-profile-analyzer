import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

user_state = {}


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(url, json=data, timeout=15)


def search_phone(phone_name):
    url = "https://api.mobileapi.dev/devices/search/"

    params = {
        "key": MOBILE_API_KEY,
        "name": phone_name,
        "page": 1
    }

    response = requests.get(url, params=params, timeout=15)

    print("MobileAPI status:", response.status_code)
    print("MobileAPI response:", response.text[:2000])

    if response.status_code != 200:
        return None

    return response.json()


@app.route("/", methods=["GET"])
def home():
    return "SOK DZAYR Phone Bot is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return "OK"

    if text == "/start":
        keyboard = {
            "keyboard": [
                ["🔎 ابحث عن هاتف"],
                ["🔔 إنشاء تنبيه سعر"],
                ["📋 هواتفي المتابعة"],
                ["ℹ️ المساعدة"]
            ],
            "resize_keyboard": True
        }

        user_state[chat_id] = {"step": None}

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في SOK DZAYR 📱\n\n"
            "ابحث عن هاتف لمعرفة مواصفاته.",
            keyboard
        )

    elif text == "🔎 ابحث عن هاتف":
        user_state[chat_id] = {"step": "search"}

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف.\n\n"
            "مثال:\n"
            "iPhone 17 Pro\n"
            "Samsung Galaxy S24 Ultra"
        )

    elif text == "🔔 إنشاء تنبيه سعر":
        user_state[chat_id] = {"step": "alert_product"}

        send_message(
            chat_id,
            "📱 اكتب اسم الهاتف الذي تريد متابعة سعره."
        )

    elif text == "📋 هواتفي المتابعة":
        send_message(
            chat_id,
            "📋 لا توجد هواتف محفوظة حاليًا."
        )

    elif text == "ℹ️ المساعدة":
        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "🔎 ابحث عن هاتف\n"
            "اكتب اسم الهاتف وسأبحث عن مواصفاته.\n\n"
            "🔔 يمكنك لاحقًا إنشاء تنبيه للسعر."
        )

    else:
        state = user_state.get(chat_id, {})
        step = state.get("step")

        if step == "search":
            phone_name = text

            try:
                result = search_phone(phone_name)

                if result is None:
                    send_message(
                        chat_id,
                        "❌ حدث خطأ في الاتصال بخدمة معلومات الهواتف."
                    )
                    return "OK"

                devices = result.get("devices", [])

                if not devices:
                    send_message(
                        chat_id,
                        f"❌ لم أجد هاتفًا مطابقًا لـ:\n\n{phone_name}"
                    )
                    return "OK"

                device = devices[0]

                name = device.get("name", "غير معروف")
                manufacturer = device.get(
                    "manufacturer_name",
                    "غير معروف"
                )

                match = device.get(
                    "match_certainty",
                    "غير معروف"
                )

                description = device.get(
                    "description",
                    ""
                )

                storage = device.get(
                    "storage",
                    "غير معروف"
                )

                screen = device.get(
                    "screen_resolution",
                    "غير معروف"
                )

                camera = device.get(
                    "camera",
                    "غير معروف"
                )

                battery = device.get(
                    "battery_capacity",
                    "غير معروف"
                )

                hardware = device.get(
                    "hardware",
                    "غير معروف"
                )

                message_text = (
                    f"📱 {name}\n\n"
                    f"🏢 الشركة: {manufacturer}\n"
                    f"🎯 دقة المطابقة: {match}\n\n"
                    f"📺 الشاشة: {screen}\n"
                    f"📸 الكاميرا: {camera}\n"
                    f"🔋 البطارية: {battery}\n"
                    f"⚙️ المعالج/RAM: {hardware}\n"
                    f"💾 التخزين: {storage}\n"
                )

                if description:
                    message_text += (
                        f"\n📝 الوصف:\n{description}"
                    )

                send_message(chat_id, message_text)

            except Exception as error:
                print("Search error:", error)

                send_message(
                    chat_id,
                    "❌ حدث خطأ أثناء البحث. تحقق من Logs في Render."
                )

            user_state[chat_id] = {"step": None}

        elif step == "alert_product":
            user_state[chat_id] = {
                "step": "target_price",
                "product": text
            }

            send_message(
                chat_id,
                f"📱 الهاتف: {text}\n\n"
                "💰 اكتب السعر المستهدف بالدينار الجزائري.\n\n"
                "مثال: 100000"
            )

        elif step == "target_price":
            try:
                price = float(
                    text.replace(" ", "").replace(",", ".")
                )

                product = state.get("product", "الهاتف")

                user_state[chat_id] = {
                    "step": None,
                    "product": product,
                    "target_price": price
                }

                send_message(
                    chat_id,
                    f"✅ تم إنشاء التنبيه!\n\n"
                    f"📱 الهاتف: {product}\n"
                    f"🎯 السعر: {price:,.0f} دج\n\n"
                    "🔔 سنربط التنبيه بمصدر الأسعار في المرحلة القادمة."
                )

            except ValueError:
                send_message(
                    chat_id,
                    "❌ أدخل السعر بالأرقام فقط.\n\n"
                    "مثال: 100000"
                )

        else:
            send_message(
                chat_id,
                "اكتب /start لفتح القائمة الرئيسية."
            )

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

writing{variant="document" id="58321"}
```python
import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MOBILE_API_KEY = os.environ.get("MOBILE_API_KEY")

user_state = {}


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(url, json=data, timeout=15)


def search_phone(phone_name):
    url = "https://api.mobileapi.dev/devices/search/"

    params = {
        "key": MOBILE_API_KEY,
        "name": phone_name,
        "page": 1
    }

    response = requests.get(url, params=params, timeout=15)

    print("MobileAPI status:", response.status_code)
    print("MobileAPI response:", response.text[:2000])

    if response.status_code != 200:
        return None

    return response.json()


@app.route("/", methods=["GET"])
def home():
    return "SOK DZAYR Phone Bot is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return "OK"

    if text == "/start":
        keyboard = {
            "keyboard": [
                ["🔎 ابحث عن هاتف"],
                ["🔔 إنشاء تنبيه سعر"],
                ["📋 هواتفي المتابعة"],
                ["ℹ️ المساعدة"]
            ],
            "resize_keyboard": True
        }

        user_state[chat_id] = {"step": None}

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في SOK DZAYR 📱\n\n"
            "ابحث عن هاتف لمعرفة مواصفاته.",
            keyboard
        )

    elif text == "🔎 ابحث عن هاتف":
        user_state[chat_id] = {"step": "search"}

        send_message(
            chat_id,
            "🔎 اكتب اسم الهاتف.\n\n"
            "مثال:\n"
            "iPhone 17 Pro\n"
            "Samsung Galaxy S24 Ultra"
        )

    elif text == "🔔 إنشاء تنبيه سعر":
        user_state[chat_id] = {"step": "alert_product"}

        send_message(
            chat_id,
            "📱 اكتب اسم الهاتف الذي تريد متابعة سعره."
        )

    elif text == "📋 هواتفي المتابعة":
        send_message(
            chat_id,
            "📋 لا توجد هواتف محفوظة حاليًا."
        )

    elif text == "ℹ️ المساعدة":
        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "🔎 ابحث عن هاتف\n"
            "اكتب اسم الهاتف وسأبحث عن مواصفاته.\n\n"
            "🔔 يمكنك لاحقًا إنشاء تنبيه للسعر."
        )

    else:
        state = user_state.get(chat_id, {})
        step = state.get("step")

        if step == "search":
            phone_name = text

            try:
                result = search_phone(phone_name)

                if result is None:
                    send_message(
                        chat_id,
                        "❌ حدث خطأ في الاتصال بخدمة معلومات الهواتف."
                    )
                    return "OK"

                devices = result.get("devices", [])

                if not devices:
                    send_message(
                        chat_id,
                        f"❌ لم أجد هاتفًا مطابقًا لـ:\n\n{phone_name}"
                    )
                    return "OK"

                device = devices[0]

                name = device.get("name", "غير معروف")
                manufacturer = device.get(
                    "manufacturer_name",
                    "غير معروف"
                )

                match = device.get(
                    "match_certainty",
                    "غير معروف"
                )

                description = device.get(
                    "description",
                    ""
                )

                storage = device.get(
                    "storage",
                    "غير معروف"
                )

                screen = device.get(
                    "screen_resolution",
                    "غير معروف"
                )

                camera = device.get(
                    "camera",
                    "غير معروف"
                )

                battery = device.get(
                    "battery_capacity",
                    "غير معروف"
                )

                hardware = device.get(
                    "hardware",
                    "غير معروف"
                )

                message_text = (
                    f"📱 {name}\n\n"
                    f"🏢 الشركة: {manufacturer}\n"
                    f"🎯 دقة المطابقة: {match}\n\n"
                    f"📺 الشاشة: {screen}\n"
                    f"📸 الكاميرا: {camera}\n"
                    f"🔋 البطارية: {battery}\n"
                    f"⚙️ المعالج/RAM: {hardware}\n"
                    f"💾 التخزين: {storage}\n"
                )

                if description:
                    message_text += (
                        f"\n📝 الوصف:\n{description}"
                    )

                send_message(chat_id, message_text)

            except Exception as error:
                print("Search error:", error)

                send_message(
                    chat_id,
                    "❌ حدث خطأ أثناء البحث. تحقق من Logs في Render."
                )

            user_state[chat_id] = {"step": None}

        elif step == "alert_product":
            user_state[chat_id] = {
                "step": "target_price",
                "product": text
            }

            send_message(
                chat_id,
                f"📱 الهاتف: {text}\n\n"
                "💰 اكتب السعر المستهدف بالدينار الجزائري.\n\n"
                "مثال: 100000"
            )

        elif step == "target_price":
            try:
                price = float(
                    text.replace(" ", "").replace(",", ".")
                )

                product = state.get("product", "الهاتف")

                user_state[chat_id] = {
                    "step": None,
                    "product": product,
                    "target_price": price
                }

                send_message(
                    chat_id,
                    f"✅ تم إنشاء التنبيه!\n\n"
                    f"📱 الهاتف: {product}\n"
                    f"🎯 السعر: {price:,.0f} دج\n\n"
                    "🔔 سنربط التنبيه بمصدر الأسعار في المرحلة القادمة."
                )

            except ValueError:
                send_message(
                    chat_id,
                    "❌ أدخل السعر بالأرقام فقط.\n\n"
                    "مثال: 100000"
                )

        else:
            send_message(
                chat_id,
                "اكتب /start لفتح القائمة الرئيسية."
            )

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
