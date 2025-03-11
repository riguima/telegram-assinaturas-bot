import os
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import mercadopago
import qrcode
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
)
from telegram_assinaturas_bot.config import config


def init_bot(bot, start):
    @bot.callback_query_handler(config=actions_factory.filter(action='show_signature'))
    def show_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        user = repository.get_user_by_username(data['u'])
        signatures = repository.get_active_signatures(user.id)
        if signatures:
            send_signature_menu(callback_query.message, signatures)
        else:
            bot.send_message(
                callback_query.message.chat.id,
                'Você não possui uma assinatura ativa',
                reply_markup=quick_markup(
                    {
                        'Comprar acesso': utils.create_categories_callback_data(
                            label='Escolha o plano',
                            action='sign',
                        ),
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

    @bot.callback_query_handler(config=actions_factory.filter(action='sign'))
    def sign(callback_query):
        data = actions_factory.parse(callback_query.data)
        checkout = repository.get_setting('Checkout')
        plan = repository.get_plan(int(data['p']))
        if checkout == 'Mercado Pago':
            qr_code, payment_id = get_mercadopago_qrcode(plan)
        else:
            qr_code, payment_id = get_asaas_qrcode(plan)
        bot.send_message(
            callback_query.message.chat.id,
            'Realize o pagamento para ativar o plano',
        )
        bot.send_message(callback_query.message.chat.id, 'Chave Pix abaixo:')
        bot.send_message(callback_query.message.chat.id, qr_code)
        qr_code = qrcode.make(qr_code)
        qr_code_filename = f'{uuid4()}.png'
        qr_code.save(qr_code_filename)
        bot.send_photo(
            callback_query.message.chat.id,
            open(Path(qr_code_filename).absolute(), 'rb'),
        )
        os.remove(Path(qr_code_filename).absolute())
        user = repository.get_user_by_username(callback_query.message.chat.username)
        repository.add_payment(
            chat_id=callback_query.message.chat.id,
            user_id=user.id,
            payment_id=payment_id,
        )

    def get_mercadopago_qrcode(plan, username):
        mercado_pago_sdk = mercadopago.SDK(
            repository.get_setting('Mercado Pago Access Token')
        )
        due_date = utils.get_today_date() + timedelta(days=plan.days)
        payment_data = {
            'transaction_amount': plan.value,
            'description': (
                f'{plan.name}'
                f' - {plan.days} Dias'
                f' - R${plan.value:.2f}'
                f' - Vencimento: {(due_date):%d/%m/%Y}'
                f' - {username}'
            ),
            'payment_method_id': 'pix',
            'installments': 1,
            'payer': {
                'email': config['PAYER_EMAIL'],
            },
        }
        response = mercado_pago_sdk.payment().create(payment_data)['response']
        return response['point_of_interaction']['transaction_data']['qr_code']

    def get_asaas_qrcode(plan, username):
        mercado_pago_sdk = mercadopago.SDK(
            repository.get_setting('Mercado Pago Access Token')
        )
        due_date = utils.get_today_date() + timedelta(days=plan.days)
        payment_data = {
            'transaction_amount': plan.value,
            'description': (
                f'{plan.name}'
                f' - {plan.days} Dias'
                f' - R${plan.value:.2f}'
                f' - Vencimento: {(due_date):%d/%m/%Y}'
                f' - {username}'
            ),
            'payment_method_id': 'pix',
            'installments': 1,
            'payer': {
                'email': config['PAYER_EMAIL'],
            },
        }
        response = mercado_pago_sdk.payment().create(payment_data)['response']
        return response['point_of_interaction']['transaction_data']['qr_code']

    @bot.callback_query_handler(config=actions_factory.filter('cancel_signature'))
    def cancel_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_signature(int(data['s']))
        bot.send_message(callback_query.message.chat.id, 'Assinatura Cancelada!')
        start(callback_query.message)
