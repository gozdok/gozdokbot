import telebot
import schedule
import threading
import time
import random
from flask import Flask, request
from datetime import datetime

# ==== Настройки ====
TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"
CHAT_ID = 312503925
WEBHOOK_URL = "https://gozdokbot.onrender.com/"
TIMEZONE_OFFSET = 3

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_notifications = []

# ==== Уведомления ====
def send_message(text):
    bot.send_message(CHAT_ID, text)

def morning_vector():
    send_message("""\U0001F305 Утренний вектор:
Определи 1 основную задачу дня и запиши её.
Что самое важное ты хочешь сделать сегодня?""")

def focus_session():
    send_message("""\u23F1 25 минут фокуса:
Запусти таймер на 25 минут и работай только над одной задачей.
После — сделай 5 минут перерыв.""")

def one_minute_silence():
    send_message("""\U0001F92B 1 минута тишины:
Закрой глаза. Сделай глубокий вдох. Просто посиди в тишине одну минуту.
Позволь себе немного покоя.""")

def five_min_rule():
    send_message("""\U0001F590 Правило 5 минут:
Если есть задача, которую откладываешь — начни с 5 минут.
Заведи таймер и просто начни. Потом решишь, продолжать ли.""")

def daily_reflection():
    send_message("""\U0001F4DD Комментарий дня:
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

def run_schedule():
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==== Кнопки и команды ====
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить уведомление", "Уведомления")
    bot.send_message(
        message.chat.id,
        "Привет! Я бот-наставник. Я буду присылать тебе напоминания каждый день \U0001F9ED",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "Тест")
def test_button(message):
    bot.send_message(message.chat.id, "\u2705 Бот работает! Это тестовое сообщение.")

@bot.message_handler(func=lambda message: message.text == "Уведомления")
def show_notifications(message):
    if not user_notifications:
        bot.send_message(message.chat.id, "У тебя пока нет пользовательских уведомлений.")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    for idx, notif in enumerate(user_notifications):
        btn = telebot.types.InlineKeyboardButton(
            text=f"{notif['text']} в {notif['time']}",
            callback_data=f"delete_notif_{idx}"
        )
        markup.add(btn)

    bot.send_message(message.chat.id, "Выбери уведомление для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_notif_"))
def delete_notification(call):
    idx = int(call.data.split("_")[-1])
    try:
        notif = user_notifications.pop(idx)
        bot.answer_callback_query(call.id, "Уведомление удалено.")
        bot.send_message(call.message.chat.id, f"\u274C Уведомление «{notif['text']}» удалено.")
    except IndexError:
        bot.answer_callback_query(call.id, "Ошибка: уведомление не найдено.")

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
    threading.Thread(target=run_schedule).start()
    app.run(host='0.0.0.0', port=8080)
