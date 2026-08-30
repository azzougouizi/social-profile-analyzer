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

    try:
        requests.post(url, json=data, timeout=15)
    except Exception as error:
        print("Telegram error:", error)


def search_phone(phone_name):
    url = "https://api.mobileapi.dev/devices/search/"

    params = {
        "key": MOBILE_API_KEY,
        "name": phone_name,
        "page": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

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

        user_state[chat_id] = {
            "step": None
        }

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في SOK DZAYR 📱\n\n"
            "يمكنك البحث عن أي هاتف ومعرفة معلوماته.",
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
            "iPhone 17 Pro\n"
            "Samsung Galaxy S24 Ultra"
        )

        return "OK"

    if text == "🔔 إنشاء تنبيه سعر":

        user_state[chat_id] = {
            "step": "alert_product"
        }

        send_message(
            chat_id,
            "📱 اكتب اسم الهاتف الذي تريد متابعة سعره."
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
            "ℹ️ المساعدة\n\n"
            "🔎 ابحث عن هاتف:\n"
            "اكتب اسم الهاتف وسأبحث عن معلوماته.\n\n"
            "🔔 تنبيه السعر:\n"
            "يمكنك إنشاء تنبيه، وسنضيف مراقبة الأسعار لاحقًا."
        )

        return "OK"

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
                    f"❌ لم أجد هاتفًا باسم:\n\n{phone_name}\n\n"
                    "جرّب اسمًا آخر مثل:\n"
                    "iPhone 15\n"
                    "Samsung Galaxy S24"
                )

                user_state[chat_id] = {
                    "step": None
                }

                return "OK"

            device = devices[0]

            name = device.get(
                "name",
                "غير معروف"
            )

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

            message_text = (
                f"📱 {name}\n\n"
                f"🏢 الشركة: {manufacturer}\n"
                f"🎯 دقة المطابقة: {match}\n"
            )

            if description:
                message_text += (
                    f"\n📝 الوصف:\n{description}\n"
                )

            message_text += (
                "\n📋 تم العثور على الهاتف بنجاح.\n"
                "سنضيف التفاصيل الإضافية في التطوير القادم."
            )

            send_message(
                chat_id,
                message_text
            )

        except Exception as error:

            print("Search error:", error)

            send_message(
                chat_id,
                "❌ حدث خطأ أثناء البحث.\n"
                "تحقق من Logs في Render."
            )

        user_state[chat_id] = {
            "step": None
        }

        return "OK"

    if step == "alert_product":

        user_state[chat_id] = {
            "step": "target_price",
            "product": text
        }

        send_message(
            chat_id,
            f"📱 الهاتف: {text}\n\n"
            "💰 اكتب السعر المستهدف بالدينار الجزائري.\n\n"
            "مثال:\n"
            "100000"
        )

        return "OK"

    if step == "target_price":

        try:

            price = float(
                text.replace(" ", "")
            )

            product = state.get(
                "product",
                "الهاتف"
            )

            user_state[chat_id] = {
                "step": None,
                "product": product,
                "target_price": price
            }

            send_message(
                chat_id,
                f"✅ تم إنشاء التنبيه!\n\n"
                f"📱 الهاتف: {product}\n"
                f"🎯 السعر المستهدف: {price:,.0f} دج\n\n"
                "🔔 سنربط مراقبة السعر بمصدر الأسعار لاحقًا."
            )

        except ValueError:

            send_message(
                chat_id,
                "❌ أدخل السعر بالأرقام فقط.\n\n"
                "مثال:\n"
                "100000"
            )

        return "OK"

    send_message(
        chat_id,
        "اكتب /start لفتح القائمة الرئيسية."
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
