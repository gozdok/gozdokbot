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
                        send
