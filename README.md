# Reminder Bot for Telegram (Render Compatible)

This bot sends daily reminders using Telegram. It runs on a Flask server to stay alive on Render.com.

## Features
- Daily scheduled tasks with random times
- Inline button to test if the bot works
- Runs 24/7 using Render free web service

## Files
- `reminder_bot_render.py` - Main bot script
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Setup on Render.com
1. Upload this repo to GitHub
2. Create a new Web Service on Render.com
3. Set the start command: `python reminder_bot_render.py`
