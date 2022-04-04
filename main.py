import os
import telebot
from telebot import types
from aiogram import *
import psycopg2
import logging
from config import *
from flask import Flask, request

add_session = {}
minus_session = {}

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()

@bot.message_handler(func = lambda message: message.from_user in add_session)
def uchenik(message):
    current = add_session[message.from_user]
    current.append(message.text)
    da = current[0].split()
    user_nick = da[0]
    stickers = da[1]
    db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
    result1 = db_object.fetchone()
    if not result1:
        bot.send_message(message.chat.id, 'Такого ученика нет')
    else:
        addstic(user_nick, stickers)

@bot.message_handler(func = lambda message: message.from_user in minus_session)
def uchenik1(message):
    current = minus_session[message.from_user]
    current.append(message.text)
    da = current[0].split()
    user_nick = da[0]
    stickers = da[1]
    db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
    result1 = db_object.fetchone()
    if not result1:
        bot.send_message(message.chat.id, 'Такого ученика нет')
    else:
        minusstic(user_nick, stickers)


def addstic(usernick, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers + {int(stickers)} WHERE nick = {usernick}")
    db_connection.commit()


def minusstic(usernick, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers - {int(stickers)} WHERE nick = {usernick}")
    db_connection.commit()


@bot.message_handler(commands=["start"])
def start(message):
    usernick = message.from_user.first_name
    user_id = message.from_user.id
    username = message.from_user.username
    bot.reply_to(message, f"Hello, {message.from_user.first_name}!")

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, stickers, nick) VALUES (%s, %s, %i, %s)", \
                          (user_id, username, 0, usernick))
        db_connection.commit()


@bot.message_handler(commands=["stats"])
def get_stats(message):
    db_object.execute("SELECT * FROM users ORDER BY stickers DESC LIMIT 20")
    result = db_object.fetchall()

    if not result:
        bot.reply_to(message, "No data...")
    else:
        reply_message = "- Top stickers farmers:\n"
        for i, item in enumerate(result):
            reply_message += f"[{i + 1}] {item[1].strip()} ({item[0]}) : {item[2]} stickers.\n"
        bot.reply_to(message, reply_message)

@bot.message_handler(commands=["add"])
def get_adds(message):
    add_session[message.from_user] = []
    bot.send_message(message.chat.id, "Введите: НИК Число")

@bot.message_handler(commands=["minus"])
def get_minus(message):
    minus_session[message.from_user] = []
    bot.send_message(message.chat.id, "Введите: НИК Число")

def smena(nick, id):
    user_id = id
    db_object.execute(f"UPDATE users SET nick = {nick} WHERE id = {user_id}")
    db_connection.commit()

@bot.message_handler(content_types=["text"])
def message_from_user(message):
    if 'изменить ник' in message.text:
        id = message.from_user.id
        new = message.text[13:]
        smena(new, id)


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
