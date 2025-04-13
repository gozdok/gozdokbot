import telebot
import schedule
import threading
import time
import random
import json
from flask import Flask, request
from datetime import datetime
from telebot import types

# ==== Настройки ====
TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"
WEBHOOK_URL = "https://gozdokbot.onrender.com/"
TIMEZONE_OFFSET = 3

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== Хранилище уведомлений ====
try:
    with open("notifications.json", "r") as f:
        user_notifications = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    user_notifications = {}

def save_notifications():
    with open("notifications.json", "w") as f:
        json.dump(user_notifications, f, ensure_ascii=False, indent=2)

# ==== Отправка сообщений ====
def send_message(chat_id, text):
    bot.send_message(chat_id, text)

# ==== Уведомления ====
def send_scheduled_notifications():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    for user_id, notifications in user_notifications.items():
        for note in notifications:
            if note["time_type"] == "Точное время" and note["time"] == current_time:
                send_message(user_id, note["text"])
            elif note["time_type"] == "Случайное время":
                if "random_sent" not in note or note["random_sent"].get("date") != now.strftime("%Y-%m-%d"):
                    start, end = note["time"].split("-")
                    start_h, start_m = map(int, start.strip().split(":"))
                    end_h, end_m = map(int, end.strip().split(":"))
                    total_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
                    if total_minutes > 0:
                        offset = random.randint(0, total_minutes)
                        send_hour = (start_h * 60 + start_m + offset) // 60
                        send_min = (start_h * 60 + start_m + offset) % 60
                        if f"{send_hour:02}:{send_min:02}" == current_time:
                            send_message(user_id, note["text"])
                            note["random_sent"] = {"date": now.strftime("%Y-%m-%d")}
    save_notifications()

# ==== Планировщик ====
def schedule_tasks():
    schedule.every().day.at("09:00").do(lambda: send_message(312503925, "🌅 Утренний вектор:\n\nОпредели 1 основную задачу дня и запиши её."))
    schedule.every().day.at("22:00").do(lambda: send_message(312503925, "📝 Комментарий дня:\n\nЧто было хорошего сегодня?\nЧто бы ты хотел изменить завтра?"))
    schedule.every(1).minutes.do(send_scheduled_notifications)

def run_schedule():
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==== Состояния пользователей ====
user_states = {}

# ==== Команды ====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить", "Уведомления")
    bot.send_message(message.chat.id, "Привет! Я бот-наставник. Я буду присылать тебе напоминания каждый день 🧭", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Тест")
def test(msg):
    bot.send_message(msg.chat.id, "✅ Бот работает! Это тестовое сообщение.")

@bot.message_handler(func=lambda msg: msg.text == "Добавить")
def add_start(msg):
    user_states[msg.chat.id] = {"state": "choose_type"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Точное время", "Случайное время")
    bot.send_message(msg.chat.id, "Выбери тип времени:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["Точное время", "Случайное время"])
def choose_time_type(msg):
    state = user_states.get(msg.chat.id)
    if not state or state.get("state") != "choose_type":
        return
    state["time_type"] = msg.text
    state["state"] = "enter_time"
    bot.send_message(msg.chat.id, "Введи время (например, 14:30 или интервал 12:00-16:00):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("state") == "enter_time")
def enter_time(msg):
    user_states[msg.chat.id]["time"] = msg.text
    user_states[msg.chat.id]["state"] = "enter_text"
    bot.send_message(msg.chat.id, "Теперь введи текст уведомления:")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("state") == "enter_text")
def enter_text(msg):
    data = user_states.pop(msg.chat.id)
    user_id = str(msg.chat.id)
    notification = {
        "text": msg.text,
        "time_type": data["time_type"],
        "time": data["time"]
    }
    user_notifications.setdefault(user_id, []).append(notification)
    save_notifications()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить", "Уведомления")
    bot.send_message(msg.chat.id, "✅ Уведомление добавлено!", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Уведомления")
def list_notifications(msg):
    notes = user_notifications.get(str(msg.chat.id), [])
    if not notes:
        return bot.send_message(msg.chat.id, "❌ Уведомлений нет.")

    markup = types.InlineKeyboardMarkup()
    for i, note in enumerate(notes):
        btn = types.InlineKeyboardButton(text=f"{note['text']} ({note['time']})", callback_data=f"del_{i}")
        markup.add(btn)
    bot.send_message(msg.chat.id, "📋 Список уведомлений:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def delete_note(call):
    index = int(call.data.split("_")[1])
    user_id = str(call.message.chat.id)
    if user_id in user_notifications and index < len(user_notifications[user_id]):
        deleted = user_notifications[user_id].pop(index)
        save_notifications()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"🗑 Уведомление удалено: {deleted['text']}")

# ==== Webhook ====
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/set_webhook')
def set_webhook():
    bot.remove_webhook()
    result = bot.set_webhook(url=WEBHOOK_URL)
    return f"Webhook установлен: {result}"

@app.route('/')
def home():
    return "Бот работает!"

# ==== Запуск ====
if __name__ == '__main__':
    threading.Thread(target=run_schedule).start()
    app.run(host='0.0.0.0', port=8080)
