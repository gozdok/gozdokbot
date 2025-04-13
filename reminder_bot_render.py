import telebot
import schedule
import threading
import time
import random
from flask import Flask, request
from datetime import datetime

TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"
CHAT_ID = 312503925
WEBHOOK_URL = "https://gozdokbot.onrender.com/"
TIMEZONE_OFFSET = 3

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_states = {}
user_notifications = {}

def get_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("Тест"),
        telebot.types.KeyboardButton("Добавить уведомление"),
        telebot.types.KeyboardButton("Уведомления")
    )
    return markup

def send_message(text):
    bot.send_message(CHAT_ID, text)

def morning_vector():
    send_message("🌅 Утренний вектор:\nОпредели 1 основную задачу дня и запиши её.\nЧто самое важное ты хочешь сделать сегодня?")

def focus_session():
    send_message("⏱ 25 минут фокуса:\nЗапусти таймер на 25 минут и работай только над одной задачей.\nПосле — сделай 5 минут перерыв.")

def one_minute_silence():
    send_message("🤫 1 минута тишины:\nЗакрой глаза. Сделай глубокий вдох. Просто посиди в тишине одну минуту.\nПозволь себе немного покоя.")

def five_min_rule():
    send_message("🖐 Правило 5 минут:\nЕсли есть задача, которую откладываешь — начни с 5 минут.\nЗаведи таймер и просто начни.")

def daily_reflection():
    send_message("📝 Комментарий дня:\nЧто было хорошего сегодня?\nЧто бы ты хотел изменить завтра?\nЗапиши 1-2 мысли.")

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

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот-наставник. Я буду присылать тебе напоминания каждый день 🧭", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "Тест")
def test_button(message):
    bot.send_message(message.chat.id, "✅ Бот работает! Это тестовое сообщение.")

@bot.message_handler(func=lambda msg: msg.text == "Добавить уведомление")
def add_notification(message):
    user_states[message.chat.id] = {"step": "choose_time_type"}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Точное время", "Случайное время")
    bot.send_message(message.chat.id, "Выбери тип времени для уведомления:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["Точное время", "Случайное время"])
def choose_time_type(message):
    state = user_states.get(message.chat.id)
    if not state:
        return
    state["time_type"] = message.text
    state["step"] = "enter_text"
    bot.send_message(message.chat.id, "Введи текст уведомления:")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "enter_text")
def enter_text(message):
    user_states[message.chat.id]["text"] = message.text
    time_type = user_states[message.chat.id]["time_type"]
    if time_type == "Точное время":
        bot.send_message(message.chat.id, "Введи время в формате ЧЧ:ММ (например, 14:30):")
    else:
        bot.send_message(message.chat.id, "Введи диапазон времени (например, 12:00-18:00):")
    user_states[message.chat.id]["step"] = "enter_time"

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "enter_time")
def enter_time(message):
    state = user_states[message.chat.id]
    text = state["text"]
    time_type = state["time_type"]

    if time_type == "Точное время":
        time_str = message.text
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return bot.send_message(message.chat.id, "Неверный формат времени. Попробуй снова.")
        schedule.every().day.at(time_str).do(lambda: bot.send_message(message.chat.id, text)).tag(f"user_{message.chat.id}")
        user_notifications.setdefault(message.chat.id, []).append({
            "text": text,
            "time": time_str,
            "interval": None
        })
    else:
        try:
            start_str, end_str = message.text.split("-")
            start = datetime.strptime(start_str.strip(), "%H:%M")
            end = datetime.strptime(end_str.strip(), "%H:%M")
        except ValueError:
            return bot.send_message(message.chat.id, "Неверный формат. Введи диапазон как ЧЧ:ММ-ЧЧ:ММ.")
        hour = random.randint(start.hour, end.hour)
        minute = random.randint(0, 59)
        time_str = f"{hour:02}:{minute:02}"
        schedule.every().day.at(time_str).do(lambda: bot.send_message(message.chat.id, text)).tag(f"user_{message.chat.id}")
        user_notifications.setdefault(message.chat.id, []).append({
            "text": text,
            "time": time_str,
            "interval": f"{start_str.strip()} - {end_str.strip()}"
        })

    bot.send_message(message.chat.id, "✅ Уведомление добавлено!", reply_markup=get_main_menu())
    user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda msg: msg.text == "Уведомления")
def show_notifications(message):
    notifs = user_notifications.get(message.chat.id, [])
    if not notifs:
        return bot.send_message(message.chat.id, "У тебя пока нет уведомлений.", reply_markup=get_main_menu())

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for idx, notif in enumerate(notifs):
        label = f"{idx+1}. {notif['time']} — {notif['text'][:20]}"
        markup.add(label)
    markup.add("Назад")
    user_states[message.chat.id] = {"step": "choose_to_delete"}
    bot.send_message(message.chat.id, "Твои уведомления. Нажми, чтобы удалить:", reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "choose_to_delete")
def delete_notification(message):
    if message.text == "Назад":
        user_states.pop(message.chat.id, None)
        return bot.send_message(message.chat.id, "Возвращаюсь в меню.", reply_markup=get_main_menu())

    notifs = user_notifications.get(message.chat.id, [])
    try:
        idx = int(message.text.split(".")[0]) - 1
        notif = notifs.pop(idx)
        schedule.clear(f"user_{message.chat.id}")
        for n in notifs:
            schedule.every().day.at(n["time"]).do(lambda: bot.send_message(message.chat.id, n["text"])).tag(f"user_{message.chat.id}")
        bot.send_message(message.chat.id, f"🗑 Уведомление удалено.", reply_markup=get_main_menu())
    except:
        bot.send_message(message.chat.id, "Не получилось определить уведомление. Попробуй снова.")

    user_states.pop(message.chat.id, None)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    success = bot.set_webhook(url=WEBHOOK_URL)
    return f"Webhook установлен: {success}"

@app.route('/')
def home():
    return "Бот работает по Webhook!"

if __name__ == '__main__':
    threading.Thread(target=run_schedule).start()
    app.run(host='0.0.0.0', port=8080)
