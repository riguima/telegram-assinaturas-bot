import os
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import mercadopago
import qrcode
from httpx import get, post
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
)
from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.utils import get_today_date


def init_bot(bot, bot_username, start):
    @bot.callback_query_handler(config=actions_factory.filter(action='show_signature'))
    def show_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        user = repository.get_user_by_username(bot_username, data['u'])
        signatures = repository.get_active_signatures(user.id)
        if signatures:
            send_signature_menu(callback_query.message, signatures)
        else:
            bot.send_message(
                callback_query.message.chat.id,
                'Você não possui uma assinatura ativa',
                reply_markup=quick_markup(
                    {
                        'Comprar acesso': {
                            'callback_data': utils.create_categories_callback_data(
                                label='Escolha o plano',
                                action='ask_cpf_cnpj',
                            ),
                        },
                        'Voltar': {'callback_data': 'show_main_menu'},
                    },
                    row_width=1,
                ),
            )

    def send_signature_menu(message, signatures):
        reply_markup = {}
        for signature in signatures:
            reply_markup[utils.get_signature_text(signature)] = {
                'callback_data': utils.create_actions_callback_data(
                    action='show_signature_message',
                    s=signature.id,
                )
            }
        reply_markup['Comprar acesso'] = {'callback_data': 'sign'}
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_signature_message')
    )
    def show_signature_message(callback_query):
        data = actions_factory.parse(callback_query.data)
        signature = repository.get_signature(int(data['s']))
        try:
            message = (
                f'{utils.get_signature_text(signature, with_due_date=True)}\n\n'
                f'{signature.account.message}'
            )
        except AttributeError:
            message = utils.get_signature_text(signature, with_due_date=True)
        bot.send_message(
            callback_query.message.chat.id,
            message,
            reply_markup=quick_markup({
                'Voltar': {'callback_data': 'show_main_menu'},
            }),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='ask_cpf_cnpj'))
    def ask_cpf_cnpj(callback_query):
        data = actions_factory.parse(callback_query.data)
        user = repository.get_user_by_username(
            bot_username,
            callback_query.message.chat.username,
        )
        if user.cpf_cnpj is None:
            bot.send_message(callback_query.message.chat.id, 'Digite seu CPF/CNPJ')
            bot.register_next_step_handler(
                callback_query.message,
                lambda m: on_cpf_cnpj(m, user.id, int(data['p'])),
            )
        else:
            sign(callback_query.message, int(data['p']))

    def on_cpf_cnpj(message, user_id, plan_id):
        repository.edit_user_cpf_cnpj(user_id, message.text)
        bot.send_message(message.chat.id, 'Digite o seu Email')
        bot.register_next_step_handler(message, lambda m: on_email(m, user_id, plan_id))

    def on_email(message, user_id, plan_id):
        repository.edit_user_email(user_id, message.text)
        sign(message, plan_id)

    def sign(message, plan_id):
        user = repository.get_user_by_username(bot_username, message.chat.username)
        gateway = repository.get_setting(bot_username, 'Gateway')
        plan = repository.get_plan(plan_id)
        if gateway == 'Mercado Pago':
            qr_code, payment_id = get_mercadopago_qrcode(user, plan)
        else:
            qr_code, payment_id = get_asaas_qrcode(user, plan)
        bot.send_message(
            message.chat.id,
            'Realize o pagamento para ativar o plano',
        )
        bot.send_message(message.chat.id, 'Chave Pix abaixo:')
        bot.send_message(message.chat.id, qr_code)
        qr_code = qrcode.make(qr_code)
        qr_code_filename = f'{uuid4()}.png'
        qr_code.save(qr_code_filename)
        bot.send_photo(
            message.chat.id,
            open(Path(qr_code_filename).absolute(), 'rb'),
        )
        os.remove(Path(qr_code_filename).absolute())
        repository.create_payment(
            bot_username=bot_username,
            chat_id=message.chat.id,
            user_id=user.id,
            payment_id=payment_id,
            gateway=gateway,
        )

    def get_mercadopago_qrcode(user, plan):
        mercado_pago_sdk = mercadopago.SDK(
            repository.get_setting(bot_username, 'Access Token')
        )
        due_date = utils.get_today_date() + timedelta(days=plan.days)
        payment_data = {
            'transaction_amount': plan.value,
            'description': (
                f'{plan.name}'
                f' - {plan.days} Dias'
                f' - R${plan.value:.2f}'
                f' - Vencimento: {(due_date):%d/%m/%Y}'
                f' - {user.username}'
            ),
            'payment_method_id': 'pix',
            'installments': 1,
            'payer': {
                'email': user.email,
            },
        }
        response = mercado_pago_sdk.payment().create(payment_data)['response']
        return (
            response['point_of_interaction']['transaction_data']['qr_code'],
            response['id'],
        )

    def get_asaas_qrcode(user, plan):
        access_token = repository.get_setting(bot_username, 'Access Token')
        due_date = utils.get_today_date() + timedelta(days=plan.days)
        customer_response = get(
            f'{config["ASAAS_API_HOST"]}/v3/customers',
            params={
                'cpfCnpj': user.cpf_cnpj,
            },
            headers={
                'access_token': access_token,
            },
        ).json()
        if customer_response['data']:
            customer_response = customer_response['data'][0]
        else:
            customer_response = post(
                f'{config["ASAAS_API_HOST"]}/v3/customers',
                json={
                    'name': user.name,
                    'cpfCnpj': user.cpf_cnpj,
                    'email': user.email,
                },
                headers={'access_token': access_token},
            ).json()
        payment_data = {
            'customer': customer_response['id'],
            'dueDate': get_today_date().strftime('%Y-%m-%d'),
            'billingType': 'PIX',
            'value': plan.value,
            'description': (
                f'{plan.name}'
                f' - {plan.days} Dias'
                f' - R${plan.value:.2f}'
                f' - Vencimento: {(due_date):%d/%m/%Y}'
                f' - {user.username}'
            ),
        }
        payment_response = post(
            f'{config["ASAAS_API_HOST"]}/v3/payments',
            json=payment_data,
            headers={'access_token': access_token},
        ).json()
        qr_code_response = get(
            f'{config["ASAAS_API_HOST"]}/v3/payments/{payment_response["id"]}/pixQrCode',
            headers={'access_token': access_token},
        ).json()
        return (
            qr_code_response['payload'],
            payment_response['id'],
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='cancel_signature')
    )
    def cancel_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_signature(int(data['s']))
        bot.send_message(callback_query.message.chat.id, 'Assinatura Cancelada!')
        start(callback_query.message)
