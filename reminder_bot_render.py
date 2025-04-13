import telebot
import schedule
import threading
import time
import random
from flask import Flask, request
from datetime import datetime

# ==== Настройки ====
TOKEN = "7762206409:AAFePy9OGuJWG-HxB48JRoKc1f6VFa4IRYc"
WEBHOOK_URL = "https://gozdokbot.onrender.com/"
TIMEZONE_OFFSET = 3

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== Хранилище уведомлений ====
# Структура: { chat_id: [ { 'text': ..., 'time': ..., 'type': ... }, ... ] }
user_reminders = {}

# ==== Отправка уведомлений ====
def send_message(chat_id, text):
    bot.send_message(chat_id, text)

# ==== Планировщик задач ====
def schedule_tasks():
    while True:
        now = datetime.utcnow()
        for chat_id, reminders in user_reminders.items():
            for reminder in reminders:
                if reminder['type'] == 'fixed':
                    # Проверка времени с учётом смещения
                    reminder_time = datetime.strptime(reminder['time'], "%H:%M")
                    if now.hour == (reminder_time.hour - TIMEZONE_OFFSET) % 24 and now.minute == reminder_time.minute:
                        send_message(chat_id, reminder['text'])
                elif reminder['type'] == 'random':
                    if 'sent_today' not in reminder:
                        start_hour, end_hour = map(int, reminder['time'].split('-'))
                        reminder['random_hour'] = random.randint(start_hour, end_hour - 1)
                        reminder['random_minute'] = random.randint(0, 59)
                        reminder['sent_today'] = False
                    if (now.hour == (reminder['random_hour'] - TIMEZONE_OFFSET) % 24 and
                        now.minute == reminder['random_minute'] and
                        not reminder['sent_today']):
                        send_message(chat_id, reminder['text'])
                        reminder['sent_today'] = True
        # Сброс флагов в полночь
        if now.hour == 0 and now.minute == 0:
            for reminders in user_reminders.values():
                for r in reminders:
                    r.pop('sent_today', None)
        time.sleep(60)

# ==== Обработчики состояний ====
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in user_reminders:
        user_reminders[chat_id] = []

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить уведомление", "Уведомления")
    bot.send_message(chat_id, "Привет! Я бот-наставник. Готов помогать каждый день!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Тест")
def test(message):
    bot.send_message(message.chat.id, "✅ Бот работает!")

@bot.message_handler(func=lambda m: m.text == "Добавить уведомление")
def add_notification(message):
    user_states[message.chat.id] = {'step': 'choose_type'}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Точное время", "Случайное время")
    bot.send_message(message.chat.id, "Выбери тип времени:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Точное время", "Случайное время"])
def time_type(message):
    state = user_states.get(message.chat.id)
    if not state or state.get('step') != 'choose_type':
        return

    state['type'] = 'fixed' if message.text == "Точное время" else 'random'
    state['step'] = 'enter_time'

    text = "Введи время в формате ЧЧ:ММ (например, 14:30):" if state['type'] == 'fixed' else "Введи промежуток в формате ЧЧ-ЧЧ (например, 12-20):"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'enter_time')
def enter_time(message):
    state = user_states[message.chat.id]
    time_input = message.text

    try:
        if state['type'] == 'fixed':
            datetime.strptime(time_input, "%H:%M")
        else:
            start, end = map(int, time_input.split('-'))
            assert 0 <= start < end <= 23
    except:
        bot.send_message(message.chat.id, "Неверный формат времени. Попробуй снова.")
        return

    state['time'] = time_input
    state['step'] = 'enter_text'
    bot.send_message(message.chat.id, "Теперь введи текст уведомления:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'enter_text')
def enter_text(message):
    state = user_states[message.chat.id]
    chat_id = message.chat.id

    new_reminder = {
        'type': state['type'],
        'time': state['time'],
        'text': message.text
    }

    user_reminders[chat_id].append(new_reminder)
    user_states.pop(chat_id)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить уведомление", "Уведомления")
    bot.send_message(chat_id, "Уведомление добавлено!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Уведомления")
def show_notifications(message):
    chat_id = message.chat.id
    reminders = user_reminders.get(chat_id, [])

    if not reminders:
        bot.send_message(chat_id, "У тебя пока нет уведомлений.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, r in enumerate(reminders):
        btn_text = f"{i+1}. {r['text']} ({r['time']})"
        markup.add(btn_text)
    markup.add("Назад")
    bot.send_message(chat_id, "Список уведомлений:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("Назад"))
def go_back(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Тест", "Добавить уведомление", "Уведомления")
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text.startswith(f"{i+1}.") for i in range(20)))
def delete_reminder(message):
    chat_id = message.chat.id
    idx = int(message.text.split(".")[0]) - 1
    if 0 <= idx < len(user_reminders[chat_id]):
        deleted = user_reminders[chat_id].pop(idx)
        bot.send_message(chat_id, f"Удалено: {deleted['text']} ({deleted['time']})")
        show_notifications(message)

# ==== Webhook ====
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    result = bot.set_webhook(url=WEBHOOK_URL)
    return f"Webhook установлен: {result}"

@app.route('/')
def home():
    return "Бот работает!"

# ==== Запуск ====
if __name__ == '__main__':
    threading.Thread(target=schedule_tasks).start()
    app.run(host='0.0.0.0', port=8080)
