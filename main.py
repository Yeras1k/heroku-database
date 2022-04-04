import os
import telebot
from aiogram import types
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


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = ["Профиль", "Сменить ник"]
    buttons = ["Добавить стикеры", "Отнять стикеры"]
    btn3 = types.KeyboardButton("Все данные")
    markup.add(btn1, *buttons, btn3)

    user_id = message.from_user.id
    username = message.from_user.username
    usernick = message.from_user.first_name
    bot.reply_to(message, f"Hello, {username}!")

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, stickers, nick) VALUES (%i, %s, %i, %s)",
                          (user_id, username, 0, usernick))
        db_connection.commit()


@bot.message_handler(content_types=['text'])
def func(message):

    if (message.text == "Профиль"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Главное меню")
        markup.add(back)
        user_id = message.from_user.id
        username = message.from_user.username
        db_object.execute(f"SELECT stickers FROM users WHERE id = {user_id}")
        result = db_object.fetchone()

        bot.reply_to(message.chat.id, f"{username}:  {result}")

    elif (message.text == "Добавить стикеры"):
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Главное меню")
        markup1.add(back)
        bot.send_message(message.chat.id, "Введите ник ученика")

        @bot.message_handler(content_types=['text'])
        def get_text_messages4(message2):
            user_nick = message2.text
            db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
            result1 = db_object.fetchone()
            if not result1:
                bot.send_message(message2.chat.id, 'Такого ученика нет')
            else:
                bot.send_message(message2.chat.id, "Введите количество стикеров")

                @bot.message_handler(content_types=['text'])
                def get_text_messages3(message3):
                    bal = message3.text
                    addstic(usernick=result1, stickers=bal)

    elif (message.text == "Отнять стикеры"):
        @bot.message_handler(content_types=['text'])
        def get_text_messages4(message4):
            user_nick = message4.text
            db_object.execute(f"SELECT nick FROM users WHERE nick = {user_nick}")
            result1 = db_object.fetchone()
            if not result1:
                bot.send_message(message4.chat.id, 'Такого ученика нет')
            else:
                bot.send_message(message4.chat.id, "Введите количество стикеров")

                @bot.message_handler(content_types=['text'])
                def get_text_messages5(message5):
                    bal = message5.text
                    minusstic(usernick=result1, stickers=bal)

    elif (message.text == "Главное меню"):
        bot.send_message(message.chat.id, text="Вы вернулись в главное меню")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Профиль")
        buttons = ["Добавить стикеры", "Отнять стикеры"]
        btn3 = types.KeyboardButton("Все данные")
        markup.add(btn1, *buttons, btn3)

    elif (message.text == "Все данные"):
        user_id = message.from_user.id
        if user_id == 956153880 or user_id == 581490657:
            bot.send_message(message.chat.id, 'Список:')
            db_object.execute("SELECT username, stickers FROM users")
            result = db_object.fetchall()
            for i in result:
                bot.send_message(message.chat.id, f"{i[0], i[1]}")
        else:
            bot.send_message(message.chat.id, 'У вас недостаточно прав')

    elif (message.text == "Сменить ник"):
        bot.send_message(message.chat.id, "Введите новый ник")

        @bot.message_handler(content_types=['text'])
        def get_text_messages2(message2):
            user_id = message2.from_user.id
            db_object.execute(f"UPDATE users SET nick = {message2.text} WHERE id = {user_id}")
            db_connection.commit()
            bot.send_message(message.chat.id, "Ник успешно сменен")


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
