import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    }, timeout=10)

@app.route("/", methods=["GET"])
def home():
    return "Social Profile Analyzer bot is running!"

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if chat_id and text:
        if text == "/start":
            send_message(
                chat_id,
                "Welcome to Social Profile Analyzer!\n\n"
                "Your Telegram bot is connected successfully."
            )
        else:
            send_message(chat_id, "Received: " + text)

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
