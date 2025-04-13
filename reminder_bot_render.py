
import telebot
import schedule
import threading
import time
import random
from datetime import datetime
from flask import Flask

# ==== Настройки ====
TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"  # Токен бота
CHAT_ID = 312503925  # Твой chat_id
TIMEZONE_OFFSET = 3  # Смещение по времени для Москвы (UTC+3)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== Уведомления ====

def send_message(text):
    bot.send_message(CHAT_ID, text)

# Утренний вектор (в 9:00)
def morning_vector():
    send_message("🌅 Утренний вектор:

Определи 1 основную задачу дня и запиши её.
Что самое важное ты хочешь сделать сегодня?")

# 25 минут на задачу (между 15:00 и 20:00)
def focus_session():
    send_message("⏱ 25 минут фокуса:

Запусти таймер на 25 минут и работай только над одной задачей.
После — сделай 5 минут перерыв.")

# Одна минута тишины (между 12:00 и 20:00)
def one_minute_silence():
    send_message("🤫 1 минута тишины:

Закрой глаза. Сделай глубокий вдох. Просто посиди в тишине одну минуту.
Позволь себе немного покоя.")

# Правило 5 минут (между 12:00 и 20:00)
def five_min_rule():
    send_message("🖐 Правило 5 минут:

Если есть задача, которую откладываешь — начни с 5 минут.
Заведи таймер и просто начни. Потом решишь, продолжать ли.")

# Комментарий дня (в 22:00)
def daily_reflection():
    send_message("📝 Комментарий дня:

Что было хорошего сегодня?
Что бы ты хотел изменить завтра?
Запиши 1-2 мысли.")

# ==== Расписание задач ====

def schedule_tasks():
    schedule.every().day.at("09:00").do(morning_vector)
    schedule.every().day.at("22:00").do(daily_reflection)
    
    # Случайное время для задач между 12:00 и 20:00
    random_times = set()
    while len(random_times) < 3:
        hour = random.randint(12, 19)
        minute = random.randint(0, 59)
        random_times.add(f"{hour:02}:{minute:02}")
    times = list(random_times)
    
    schedule.every().day.at(times[0]).do(one_minute_silence)
    schedule.every().day.at(times[1]).do(five_min_rule)
    schedule.every().day.at(times[2]).do(focus_session)

# ==== Кнопка "Тест" ====

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("Тест"))
    bot.send_message(message.chat.id, "Привет! Я бот-наставник. Я буду присылать тебе напоминания каждый день 🧭", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Тест")
def test_button(message):
    bot.send_message(message.chat.id, "✅ Бот работает! Это тестовое сообщение.")

# ==== Планировщик в потоке ====

def run_schedule():
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==== Flask-сервер для Render ====

@app.route('/')
def home():
    return "Бот запущен и работает!"

@app.route('/ping')
def ping():
    return "pong"

# ==== Запуск ====

if __name__ == "__main__":
    threading.Thread(target=run_schedule).start()  # Планировщик в отдельном потоке
    bot.polling(none_stop=True)  # Запуск Telegram-бота
