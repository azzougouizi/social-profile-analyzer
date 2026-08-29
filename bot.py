import os
import secrets
import requests
from flask import Flask, request, redirect

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET")

REDIRECT_URI = "https://social-profile-analyzer-0kea.onrender.com/tiktok/callback"

# Temporary storage for OAuth states
oauth_states = set()


@app.route("/", methods=["GET"])
def home():
    return """
    <h1>Social Profile Analyzer</h1>
    <p>Service is running.</p>
    <p><a href="/tiktok/login">Login with TikTok</a></p>
    """


@app.route("/tiktok/login", methods=["GET"])
def tiktok_login():
    state = secrets.token_urlsafe(32)
    oauth_states.add(state)

    url = (
        "https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        "&response_type=code"
        "&scope=user.info.basic"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )

    return redirect(url)


@app.route("/tiktok/callback", methods=["GET"])
def tiktok_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "TikTok authorization failed: no code received.", 400

    if not state or state not in oauth_states:
        return "Invalid OAuth state.", 400

    oauth_states.discard(state)

    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    response = requests.post(
        token_url,
        data={
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=15,
    )

    if response.status_code != 200:
        return "TikTok token exchange failed.", 400

    token_data = response.json()

    return f"""
    <h1>TikTok connected successfully</h1>
    <p>Your TikTok authorization was received.</p>
    <p>Access token received: {'yes' if token_data.get('access_token') else 'no'}</p>
    """


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if chat_id and text and BOT_TOKEN:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        if text == "/start":
            reply = (
                "Welcome to Social Profile Analyzer!\n\n"
                "Your Telegram bot is connected successfully."
            )
        else:
            reply = "Received: " + text

        requests.post(
            url,
            json={"chat_id": chat_id, "text": reply},
            timeout=10,
        )

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
