import os
import telebot
import logging
import psycopg2
from config import *
from flask import Flask, request


bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)


db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()


@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id
    username = message.from_user.username
    bot.reply_to(message, f"Hello, {message.from_user.first_name}!")
    bot.send_message(message.chat.id, f"Введите или нажмите на /help чтоб просмотреть все команды бота")
    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()
    if not result:
        db_object.execute(f"INSERT INTO users(id, username, stickers, nick) VALUES ('{user_id}', '{username}', "
                          f"0, '{username}')")
        db_connection.commit()


@bot.message_handler(commands=["help"])
def help1(message):
    bot.send_message(message.chat.id, "Все команды: \n"
                                      "1. /stats - просмотр своего количества стикеров \n"
                                      "2. newnick ... - вместо ... пишите свой новый ник \n"
                                      "3. stic ... - вместо ... напишите число(+добавить; -отнять) \n"
                                      "3. /statsall - просмотр всех учеников(только для учителя) \n"
                                      "4. edit ХХХ ... - изменение кол. стикеров ученика(+ и -)(только для учителя)\n"
                                      "5. /off - отключение для учеников 'стикеры ...'(только для учителя) ")


@bot.message_handler(commands=["statsall"])
def get_stats(message):
    db_object.execute("SELECT * FROM users ORDER BY stickers DESC LIMIT 20")
    result = db_object.fetchall()
    if message.from_user.id == 581490657 or message.from_user.id == 956153880:
        if not result:
            bot.reply_to(message, "No data...")
        else:
            reply_message = "- Top stickers farmers:\n"
            for i, item in enumerate(result):
                reply_message += f"[{i + 1}] {item[3].strip()} ({item[1].strip()}) : {item[2]} stickers.\n"
            bot.reply_to(message, reply_message)
    else:
        bot.send_message(message.chat.id, "Недостаточно прав")


@bot.message_handler(commands=["stats"])
def get_stats(message):
    user_id = message.from_user.id
    db_object.execute(f"SELECT * FROM users WHERE id = {user_id}")
    result = db_object.fetchall()

    if not result:
        bot.reply_to(message, "No data...")
    else:
        reply_message = "- Your stats:\n"
        for i, item in enumerate(result):
            reply_message += f"[{i + 1}] {item[3].strip()} ({item[1].strip()}) : {item[2]} stickers.\n"
        bot.reply_to(message, reply_message)


@bot.message_handler(content_types=["text"])
def message_from_user(message):
    if 'newnick' in message.text:
        userid = message.from_user.id
        new = message.text[8:]
        db_object.execute(f"UPDATE users SET nick = '{new}' WHERE id = {userid}")
        db_connection.commit()
        bot.send_message(message.chat.id, "Ник УСПЕШНО изменен")

    if 'stic' in message.text:
        stickers = message.text[5:]
        userid = message.from_user.id
        user_nick = message.from_user.username
        db_object.execute(f"UPDATE users SET stickers = stickers + {int(stickers)} WHERE id = {userid}")
        db_object.execute(f"SELECT stickers FROM users WHERE id = {userid}")
        c = db_object.fetchone()
        db_connection.commit()
        bot.send_message(message.chat.id,
                         f"Твоё({user_nick}) количество стикеров изменено на [{stickers}] и сейчас составляют [{c[0]}]")

    if 'data' in message.text:
        userid = message.from_user.id
        bot.send_message(message.chat.id, f'{chat.id}')
        
    if 'edit' in message.text:
        userid = message.from_user.id
        new = message.text[5:]
        a = new.split()
        user_nick = a[0]
        stickers = a[1]
        db_object.execute(f"SELECT nick FROM users WHERE nick = '{user_nick}'")
        result1 = db_object.fetchone()
        if not result1:
            bot.send_message(message.chat.id, 'Такого ученика нет, попробуйте снова')
        else:
            if userid == 581490657 or userid == 956153880:
                db_object.execute(f"UPDATE users SET stickers = stickers + {int(stickers)} WHERE nick = '{user_nick}'")
                db_object.execute(f"SELECT stickers FROM users WHERE nick = '{user_nick}'")
                c = db_object.fetchone()
                db_connection.commit()
                bot.send_message(message.chat.id,
                                 f"Количество стикеров для ({user_nick}) изменены "
                                 f"на [{stickers}] и составляют [{c[0]}]")
            else:
                bot.send_message(message.chat.id, "Недостаточно прав")


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
