import hmac
import os

from datetime import datetime
from flask import Flask, abort, request
import telebot
from telebot import types
import json

from config import TOKEN, SECRET, OPERATORS, VALID_PLATES
# from budget import bg


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


def save_data():
    with open('data.json', 'w', encoding="utf-8") as f:
        json.dump(Data, f, ensure_ascii=False)


def get_operator_name(user_id: int):
    return OPERATORS.get(user_id)


def get_events():
    """
    История
    """
    cnt = 0
    text = f'*История*\n```'
    for event_date, event_time, name, roll, plate, now_value in reversed(Data["events"]):
        if cnt >= 10:
            break
        text += f'`{event_date} {roll} {int(plate):02} ({now_value:02}) {name}`\n'
        cnt += 1
    text += '```'
    return text


def get_plates():
    """
    Просто количество пластин которые остались
    """
    text_plates = '*Пластины:*\n'
    for i in Data["storage"]:
        text_plates += f'`{int(i):02} . . . . {Data["storage"][i]:02} шт.`\n'
    return text_plates


# # # #

def get_keyboard(roll: str):
    kb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text=plate, callback_data=f"plate:{roll}:{plate}")
        for plate in VALID_PLATES
    ]
    kb.add(*buttons)
    return kb

# # # #


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
    user_id = message.from_user.id
    bot.send_message(chat_id=message.chat.id,
                     text=f"Обратитесь к администратору\n"
                          f"telegram ID: `{user_id}`",
                     parse_mode="MarkdownV2")


@bot.message_handler(func=lambda message: bool(message.text))
def text_handler(message):
    user_id = message.from_user.id
    operator_name = get_operator_name(user_id)
    text = message.text.strip()

    print(f'{operator_name} | {user_id} | {text}')
    if not operator_name:
        bot.send_message(chat_id=message.chat.id,
                         text=f"Обратитесь к администратору\n"
                              f"telegram ID: `{user_id}`",
                         parse_mode="MarkdownV2")
        return
    if 'ПЦ' in text or 'ТРИО' in text:
        try:
            roll, plate = text.split()
        except ValueError:
            bot.send_message(chat_id=message.chat.id,
                             text="⚠️ Должно быть: ПЦ013 (Вал) 9 (пластина)")
            return
        if plate not in VALID_PLATES:
            bot.send_message(chat_id=message.chat.id,
                             text=f"⚠️ Такой пластины нет: {plate}")
            return
        old_value = Data["storage"][plate]
        now_value = old_value - 1
        Data["storage"][plate] = now_value
        event_time = datetime.now().strftime("%H:%M")
        event_date = datetime.now().strftime("%d.%m.%y")
        print(f'{event_date} | {operator_name} | {roll} | {plate} | {now_value}')
        Data["events"].append([event_date, event_time, operator_name, roll, plate, now_value])
        save_data()
        bot.send_message(chat_id=message.chat.id,
                         text=f"✅ Пластин ⌀{plate} осталось: {now_value} шт.")
        return
    elif text.startswith('add '):
        parts = text.split()
        if len(parts) != 3:
            bot.send_message(chat_id=message.chat.id,
                             text="⚠️ Формат: add 9 5")
            return

        _, plate, count_text = parts
        if plate not in VALID_PLATES:
            bot.send_message(chat_id=message.chat.id,
                             text=f"⚠️ Такой пластины нет: {plate}")
            return
        try:
            count = int(count_text)
        except Exception as ex:
            print(ex)
            bot.send_message(chat_id=message.chat.id,
                             text=f"⚠️ Не правильное количество!")
            return
        old_value = Data["storage"][plate]
        now_value = old_value + count
        Data["storage"][plate] = now_value
        event_time = datetime.now().strftime("%H:%M")
        event_date = datetime.now().strftime("%d.%m.%y")
        Data["events"].append([event_date, event_time, operator_name, f'Пришли {count} шт.', plate, now_value])
        save_data()
        bot.send_message(chat_id=message.chat.id,
                         text=f"✅ {operator_name} добавил {plate} теперь их {now_value} шт.")
        return

    elif text == '*':
        text_plates = get_plates()
        bot.send_message(chat_id=message.chat.id,
                         text=text_plates,
                         parse_mode="MarkdownV2")
        return
    elif text == '**':
        text_history = get_events()
        bot.send_message(chat_id=message.chat.id,
                         text=text_history,
                         parse_mode="MarkdownV2")
        return

    else:
        bot.send_message(
            message.chat.id,
            f"Какая пластина для ПЦ017?",
            reply_markup=get_keyboard('ПЦ017')
            )
        return


def answer_data(chat_id, operator_name, roll, plate):
    print(chat_id, f"✅ {operator_name} | {roll} ⌀{plate}")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    print("CALLBACK:", call.data)
    bot.answer_callback_query(call.id, "ok")


@bot.callback_query_handler(func=lambda call: call.data.startswith("plate:"))
def handle_plate_callback(call):
    print(call.data)
    _, roll, plate = call.data.split(":")
    user_id = call.from_user.id
    operator_name = get_operator_name(user_id)
    print(operator_name, user_id, roll, plate)

    answer_data(call.message.chat.id, operator_name, roll, plate)
    bot.answer_callback_query(call.id, f"Выбрана пластина {plate}")
