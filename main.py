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

def update_messages_count(username):
    db_object.execute(f"UPDATE users SET password = 'qwerty' WHERE name = {username}")
    db_connection.commit()

@bot.message_handler(commands=["start"])
def start(message):
    username = message.from_user.username
    bot.reply_to(message, f"Hello, {username}!")

    db_object.execute(f"SELECT name FROM users WHERE id = {username}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(name, password) VALUES (%s, %s)", (username, 'qwerty'))
        db_connection.commit()

    update_messages_count(username)

@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

