import os
import telebot
import psycopg2
import logging
from config import *
from flask import Flask, request

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()

def vse():
    db_object.execute(f"SELECT * FROM users")
    result = db_object.fetchone()
    bot.send_message(result)

def zhdat(user_id, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers + {int(stickers)} WHERE id = {user_id}")
    db_connection.commit()

def nezhdat(user_id, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers - {int(stickers)} WHERE id = {user_id}")
    db_connection.commit()

@bot.message_handler(commands=["show"])
def show(message):
    user_id = message.from_user.id
    username = message.from_user.username
    db_object.execute(f"SELECT stickers FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    bot.reply_to(message, f"{username}:  {result}")

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    bot.reply_to(message, f"Hello, {username}!")

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, stickers) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if "добавить" in message.text.lower():
        user_id = message.from_user.id
        stic = message.text[9:]
        zhdat(user_id=user_id, stickers=stic)
    if 'снизить' in message.text.lower():
        user_id = message.from_user.id
        stic = message.text[8:]
        nezhdat(user_id=user_id, stickers=stic)
    if 'показать всех' in message.text.lower():
        username = message.from_user.username
        if username == 'yeras1k' or username == 'b4kyt':
            vse()
        if username != 'yeras1k' and username != 'b4kyt':
            bot.reply_to(message, "У вас нет особых прав")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
