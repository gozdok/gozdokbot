import telebot
import schedule
import threading
import time
import random
import json
from flask import Flask, request
from datetime import datetime
from telebot import types
import os

# ==== Настройки ====
TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"
CHAT_ID = 312503925
WEBHOOK_URL = "https://gozdokbot.onrender.com/"  # Указан Render URL
TIMEZONE_OFFSET = 3
SAVE_FILE = "notifications.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_notifications = []
user_states = {}

# ==== Загрузка/Сохранение ====
def load_notifications():
    global user_notifications
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            user_notifications = json.load(f)

def save_notifications():
    with open(SAVE_FILE, 'w') as f:
        json.dump(user_notifications, f)

# ==== Уведомления ====
def send_message(text):
    bot.send_message(CHAT_ID, text)

def morning_vector():
    send_message("""🌅 Утренний вектор:
Определи 1 основную задачу дня и запиши её.
Что самое важное ты хочешь сделать сегодня?""")

def focus_session():
    send_message("""⏱ 25 минут фокуса:
Запусти таймер на 25 минут и работай только над одной задачей.
После — сделай 5 минут перерыв.""")

def one_minute_silence():
    send_message("""🤫 1 минута тишины:
Закрой глаза. Сделай глубокий вдох. Просто посиди в тишине одну минуту.
Позволь себе немного покоя.""")

def five_min_rule():
    send_message("""🖐 Правило 5 минут:
Если есть задача, которую откладываешь — начни с 5 минут.
Заведи таймер и просто начни. Потом решишь, продолжать ли.""")

def daily_reflection():
    send_message("""📝 Комментарий дня:
Что было хорошего сегодня?
Что бы ты хотел изменить завтра?
Запиши 1-2 мысли.""")

# ==== Расписание ====
def schedule_tasks():
    schedule.every().day.at("09:00").do(morning_vector)
    schedule.every().day.at("22:00").do(daily_reflection)

    random_times = set()
    while len(random_times) < 3:
        hour = random.randint(12, 19)
        minute = random.randint(0, 59)
        random_times.add(f"{hour:02}:{minute:02}")
    times = list(random_times)

    schedule.every().day.at(times[0]).do(one_minute_silence)
    schedule.every().day.at(times[1]).do(five_min_rule)
    schedule.every().day.at(times[2]).do(focus_session)

    for notif in user_notifications:
        if notif['type'] == 'exact':
            schedule.every().day.at(notif['time']).do(send_message, notif['text'])
        elif notif['type'] == 'random':
            hour_from, hour_to = map(int, notif['time'].split('-'))
            hour = random.randint(hour_from, hour_to - 1)
            minute = random.randint(0, 59)
            schedule.every().day.at(f"{hour:02}:{minute:02}").do(send_message, notif['text'])

def run_schedule():
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==== Интерфейс ====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Тест"))
    markup.add(types.KeyboardButton("Добавить уведомление"))
    markup.add(types.KeyboardButton("Уведомления"))
    bot.send_message(message.chat.id, "Привет! Я бот-наставник. Я буду присылать тебе напоминания каждый день 🧭", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Тест")
def test_button(message):
    bot.send_message(message.chat.id, "✅ Бот работает! Это тестовое сообщение.")

@bot.message_handler(func=lambda m: m.text == "Добавить уведомление")
def add_notification(message):
    user_states[message.chat.id] = {'step': 'choose_type'}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Точное время", "Случайное время")
    bot.send_message(message.chat.id, "Выбери тип времени:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Точное время", "Случайное время"])
def choose_time_type(message):
    state = user_states.get(message.chat.id)
    if not state or state['step'] != 'choose_type':
        return
    state['type'] = 'exact' if message.text == "Точное время" else 'random'
    state['step'] = 'enter_time'
    bot.send_message(message.chat.id, "Введи время (например: 14:30 или 12-18 для интервала):")

@bot.message_handler(func=lambda m: True)
def handle_add_notification(message):
    state = user_states.get(message.chat.id)
    if not state:
        return
    if state['step'] == 'enter_time':
        state['time'] = message.text
        state['step'] = 'enter_text'
        bot.send_message(message.chat.id, "Теперь введи текст уведомления:")
    elif state['step'] == 'enter_text':
        notif = {
            'type': state['type'],
            'time': state['time'],
            'text': message.text
        }
        user_notifications.append(notif)
        save_notifications()
        schedule.clear()
        schedule_tasks()
        user_states.pop(message.chat.id)
        bot.send_message(message.chat.id, "✅ Уведомление добавлено!")
    elif message.text == "Уведомления":
        if not user_notifications:
            bot.send_message(message.chat.id, "Нет активных уведомлений.")
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i, n in enumerate(user_notifications):
            markup.add(f"❌ {i+1}. {n['text']} ({n['time']})")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Вот список уведомлений:", reply_markup=markup)
    elif message.text.startswith("❌"):
        idx = int(message.text.split('.')[0][2:]) - 1
        if 0 <= idx < len(user_notifications):
            deleted = user_notifications.pop(idx)
            save_notifications()
            schedule.clear()
            schedule_tasks()
            bot.send_message(message.chat.id, f"Удалено: {deleted['text']}")
    elif message.text == "🔙 Назад":
        start(message)

# ==== Webhook ====
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    result = bot.set_webhook(url=WEBHOOK_URL)
    return f"Webhook установлен: {result}"

@app.route('/')
def home():
    return "Бот работает по Webhook!"

# ==== Запуск ====
if __name__ == '__main__':
    load_notifications()
    threading.Thread(target=run_schedule).start()
    app.run(host='0.0.0.0', port=8080)
