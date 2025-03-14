from http import HTTPStatus

import telebot
from fastapi import FastAPI, Request
from rich import print

from telegram_assinaturas_bot import repository
from telegram_assinaturas_bot.bot import init_bot

app = FastAPI()
bots = {}


def create_bot(bot):
    bots[bot.token] = telebot.TeleBot(bot.token, threaded=False)
    init_bot(bots[bot.token], bot.username, bot.token)


for bot in repository.get_bots():
    create_bot(bot)


@app.post('/{token}/')
async def update(token: str, update: dict):
    if bots.get(token) is None:
        create_bot(repository.get_bot_by_token(token))
    bot = bots[token]
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])


@app.post('/webhook/asaas', status_code=HTTPStatus.OK)
async def webhook_asaas(request: Request):
    print(request.json())
    return {'status': 'ok'}


@app.post('/webhook/mercado-pago', status_code=HTTPStatus.OK)
async def webhook_mercado_pago(request: Request):
    print(request.json())
    return {'status': 'ok'}
