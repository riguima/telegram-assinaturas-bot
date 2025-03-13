from http import HTTPStatus

import telebot
from fastapi import FastAPI, Request

from telegram_assinaturas_bot import repository
from telegram_assinaturas_bot.bot import init_bot

app = FastAPI()
bots = {}


def add_bot(bot):
    bots[bot.username] = telebot.TeleBot(bot.token)
    init_bot(bots[bot.username], bot.username)


for bot in repository.get_bots():
    add_bot(bot)


@app.post('/update/{username}', status_code=HTTPStatus.OK)
def update(username: str, request: Request):
    if bots.get(username) is None:
        add_bot(repository.get_bot_by_username(username))
    bot = bots[username]
    data = request.json()
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
