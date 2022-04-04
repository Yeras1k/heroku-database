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


def addstic(usernick, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers + {int(stickers)} WHERE nick = {usernick}")
    db_connection.commit()


def minusstic(usernick, stickers):
    db_object.execute(f"UPDATE users SET stickers = stickers - {int(stickers)} WHERE nick = {usernick}")
    db_connection.commit()


@bot.message_handler(commands=["show"])
def show(message):
    user_id = message.from_user.id
    username = message.from_user.username
    db_object.execute(f"SELECT stickers FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    bot.reply_to(message, f"{username}:  {result[:-1]}")


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


@bot.message_handlers(content_types=['text'])
def get_text_messages(message):
    if message.text == '+':
        bot.send_message(message.chat.id, 'Введите имя ученика')

        @bot.message_handlers(content_types=['text'])
        def get_text_messages2(message2):
            user_nick = message2.text
            db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
            result1 = db_object.fetchone()
            if not result1:
                bot.send_message(message2.chat.id, 'Такого ученика нет')
            else:
                bot.send_message(message2.chat.id, 'Введите количество стикров для добавления')

                @bot.message_handler(content_types=['text'])
                def get_text_messages3(message3):
                    addstic(usernick=user_nick, stickers=message3.text)

    if message.text == '-':
        bot.send_message(message.chat.id, 'Введите имя ученика')

        @bot.message_handlers(content_types=['text'])
        def get_text_messages2(message2):
            user_nick = message2.text
            db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
            result2 = db_object.fetchone()
            if not result2:
                bot.send_message(message2.chat.id, 'Такого ученика нет')
            else:
                bot.send_message(message2.chat.id, 'Введите имя ученика')

                @bot.message_handler(content_types=['text'])
                def get_text_messages3(message3):
                    minusstic(usernick=user_nick, stickers=message3.text)

    if message.text.lower() == 'all':
        user_id = message.from_user.id
        if user_id == 956153880 or user_id == 581490657:
            bot.send_message(message.chat.id, 'Список:')
            db_object.execute("SELECT username, stickers FROM users")
            result = db_object.fetchall()
            for i in result:
                bot.send_message(message.chat.id, f"{i[0] + i[1]}")
        else:
            bot.send_message(message.chat.id, 'У вас недостаточно прав')


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
