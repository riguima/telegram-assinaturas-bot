from http import HTTPStatus
from datetime import timedelta

import telebot
from fastapi import FastAPI

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.bot import init_bot

app = FastAPI()
bots = {}


def create_bot(bot):
    bots[bot.token] = telebot.TeleBot(bot.token, threaded=False)
    init_bot(bots[bot.token], bot.username, bot.token)


for bot in repository.get_bots():
    create_bot(bot)


@app.post('/{token}')
async def update(token: str, update: dict):
    if bots.get(token) is None:
        create_bot(repository.get_bot_by_token(token))
    bot = bots[token]
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])


@app.post('/webhook/asaas', status_code=HTTPStatus.OK)
async def webhook_asaas(body: dict):
    payment_id = body['payment']['id']
    create_signature(payment_id)
    return {'status': 'ok'}


@app.post('/webhook/mercado-pago', status_code=HTTPStatus.OK)
async def webhook_mercado_pago(body: dict):
    if body.get('action') != 'payment.updated':
        return {'status': 'ok'}
    payment_id = body['data']['id']
    create_signature(payment_id)
    return {'status': 'ok'}


def create_signature(payment_id):
    payment = repository.get_payment(payment_id, 'mercado-pago')
    if payment is None:
        return
    bot = repository.get_bot_by_username(payment.bot_username)
    bot = bots[bot.token]
    bot.send_message(
        int(payment.chat_id),
        (
            'Pagamento confirmado, Aguardando liberação...\n\n'
            f'Nº Transação: {payment.payment_id}'
        ),
    )
    plan = repository.get_payment_plan(payment.id)
    repository.create_signature(
        bot_username=payment.bot_username,
        user_id=payment.user_id,
        plan_id=payment.plan_id,
        due_date=utils.get_today_date() + timedelta(days=plan.days),
        payment_id=payment_id,
    )
    repository.delete_payment(payment.id)
