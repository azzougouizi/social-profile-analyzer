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
