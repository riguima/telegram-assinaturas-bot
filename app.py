from http import HTTPStatus

import telebot
from fastapi import FastAPI, Request
from rich import print

from telegram_assinaturas_bot import repository
from telegram_assinaturas_bot.bot import init_bot

app = FastAPI()
bots = {}


def create_bot(bot):
    bots[bot.username] = telebot.TeleBot(bot.token)
    init_bot(bots[bot.username], bot.username)


for bot in repository.get_bots():
    create_bot(bot)


@app.post('/update/{username}', status_code=HTTPStatus.OK)
def update(username: str, request: Request):
    if bots.get(username) is None:
        create_bot(repository.get_bot_by_username(username))
    bot = bots[username]
    data = request.json()
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return {'status': 'ok'}


@app.post('/webhook/asaas', status_code=HTTPStatus.OK)
def webhook_asaas(request: Request):
    print(request.json())
    return {'status': 'ok'}


@app.post('/webhook/mercado-pago', status_code=HTTPStatus.OK)
def webhook_mercado_pago(request: Request):
    print(request.json())
    return {'status': 'ok'}
