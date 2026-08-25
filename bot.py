import hmac
import os

from flask import Flask, abort, request
import telebot
from telebot import types
import json

from config import TOKEN, SECRET, OPERATORS


if not os.path.exists('data.json'):
    Data = {
        "storage": {
            "6": 0,
            "9": 0,
            "12": 0,
            "19": 0},
        "events": []
    }
else:
    with open('data.json', 'r', encoding='utf-8') as file:
        Data = json.load(file)


BOT_TOKEN = TOKEN
WEBHOOK_SECRET = SECRET
WEBHOOK_PATH = "/telegram/webhook"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)


def save_json():
    with open('data.json', 'w', encoding="utf-8") as f:
        json.dump(Data, f, ensure_ascii=False)


def get_operator_name(user_id: int):
    return OPERATORS.get(user_id)


@app.get("/healthz")
def healthz():
    return {"ok": True}, 200


@app.post(WEBHOOK_PATH)
def telegram_webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(secret, WEBHOOK_SECRET):
        abort(403)

    if request.headers.get("Content-Type", "").startswith("application/json"):
        json_string = request.get_data().decode("utf-8")
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200

    abort(400)


@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.reply_to(message, "Привет! Отправь ping")


@bot.message_handler(func=lambda message: bool(message.text))
def text_handler(message):
    print(message)
    text = message.text.strip().lower()

    if text == "ping":
        bot.send_message(message.chat.id, "pong")
