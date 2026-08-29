import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# حفظ مؤقت للمنتجات التي يبحث عنها المستخدمون
user_state = {}


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(url, json=data, timeout=10)


@app.route("/", methods=["GET"])
def home():
    return "Algeria Price Tracker Bot is running!"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return "OK"

    # بدء البوت
    if text == "/start":
        keyboard = {
            "keyboard": [
                ["🔎 ابحث عن منتج"],
                ["🔔 إنشاء تنبيه سعر"],
                ["📋 منتجاتي المتابعة"],
                ["ℹ️ المساعدة"]
            ],
            "resize_keyboard": True
        }

        user_state[chat_id] = {"step": None}

        send_message(
            chat_id,
            "🇩🇿 مرحبًا بك في بوت متابعة الأسعار!\n\n"
            "يمكنك البحث عن منتج وإنشاء تنبيه لسعره.",
            keyboard
        )

    elif text == "🔎 ابحث عن منتج":
        user_state[chat_id] = {"step": "search"}

        send_message(
            chat_id,
            "🔎 اكتب اسم المنتج الذي تبحث عنه.\n\n"
            "مثال: iPhone 15"
        )

    elif text == "🔔 إنشاء تنبيه سعر":
        user_state[chat_id] = {"step": "product_for_alert"}

        send_message(
            chat_id,
            "📦 اكتب اسم المنتج الذي تريد متابعة سعره."
        )

    elif text == "📋 منتجاتي المتابعة":
        send_message(
            chat_id,
            "📋 لا توجد منتجات محفوظة للمتابعة حتى الآن."
        )

    elif text == "ℹ️ المساعدة":
        send_message(
            chat_id,
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط 🔎 ابحث عن منتج\n"
            "2️⃣ اكتب اسم المنتج\n"
            "3️⃣ يمكنك لاحقًا إنشاء تنبيه للسعر\n\n"
            "🇩🇿 الأسعار ستكون بالدينار الجزائري."
        )

    else:
        state = user_state.get(chat_id, {})
        step = state.get("step")

        if step == "search":
            product = text

            user_state[chat_id] = {
                "step": None,
                "product": product
            }

            send_message(
                chat_id,
                f"🔎 تم تسجيل بحثك عن:\n\n📦 {product}\n\n"
                "🚧 ميزة جلب الأسعار من المتاجر ستتم إضافتها في المرحلة القادمة."
            )

        elif step == "product_for_alert":
            product = text

            user_state[chat_id] = {
                "step": "target_price",
                "product": product
            }

            send_message(
                chat_id,
                f"📦 المنتج: {product}\n\n"
                "💰 الآن اكتب السعر الذي تريد أن يتم تنبيهك عند الوصول إليه بالدينار الجزائري.\n\n"
                "مثال: 100000"
            )

        elif step == "target_price":
            try:
                price = float(text.replace(" ", "").replace(",", "."))

                product = state.get("product", "منتج")

                user_state[chat_id] = {
                    "step": None,
                    "product": product,
                    "target_price": price
                }

                send_message(
                    chat_id,
                    f"✅ تم إنشاء التنبيه!\n\n"
                    f"📦 المنتج: {product}\n"
                    f"🎯 السعر المطلوب: {price:,.0f} دج\n\n"
                    "🔔 سنستخدم مصدر أسعار مدعومًا لإرسال التنبيه عند توفر السعر المناسب."
                )

            except ValueError:
                send_message(
                    chat_id,
                    "❌ اكتب السعر بالأرقام فقط.\n\nمثال: 100000"
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
