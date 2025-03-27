from datetime import timedelta
from http import HTTPStatus

from fastapi import FastAPI

from telegram_grupo_vip_bot import repository, utils

app = FastAPI()


@app.post('/webhook/stripe', status_code=HTTPStatus.OK)
async def webhook_stripe(body: dict):
    payment_id = body['payment']['id']
    create_signature(payment_id)
    return {'status': 'ok'}


def create_signature(payment_id):
    payment = repository.get_payment(payment_id)
    if payment is None:
        return
    bot = repository.get_bot_by_token(payment.bot_token)
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
