import os
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import mercadopago
import qrcode
from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Payment, Plan, Signature, User
from telegram_assinaturas_bot.utils import (get_categories_reply_markup,
                                            get_today_date)

mercado_pago_sdk = mercadopago.SDK(config['MERCADO_PAGO_ACCESS_TOKEN'])


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: 'show_signature:' in c.data)
    def show_signature(callback_query):
        with Session() as session:
            username = callback_query.data.split(':')[-1]
            query = select(User).where(User.username == username)
            user_model = session.scalars(query).first()
            query = (
                select(Signature)
                .where(Signature.due_date >= get_today_date())
                .where(Signature.user_id == user_model.id)
            )
            signatures_models = session.scalars(query).all()
            if signatures_models:
                send_signature_menu(callback_query.message, signatures_models)
            else:
                bot.send_message(
                    callback_query.message.chat.id,
                    'Você não possui uma assinatura ativa',
                    reply_markup=quick_markup(
                        {
                            'Comprar acesso': {'callback_data': 'sign'},
                            'Voltar': {'callback_data': 'return_to_main_menu'},
                        },
                        row_width=1,
                    ),
                )

    def send_signature_menu(message, signatures_models):
        reply_markup = {}
        for signature_model in signatures_models:
            reply_markup[
                f'Status: Ativa - {signature_model.plan.name} - {signature_model.plan.days} Dias - R${signature_model.plan.value:.2f}'.replace(
                    '.', ','
                )
            ] = {
                'callback_data': f'show_signature_message:{signature_model.id}'
            }
        reply_markup['Comprar acesso'] = {'callback_data': 'sign'}
        reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'show_signature_message:' in c.data
    )
    def show_signature_message(callback_query):
        signature_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            signature_model = session.get(Signature, signature_id)
            bot.send_message(
                callback_query.message.chat.id,
                f'Status: Ativa - {signature_model.plan.name} - {signature_model.plan.days} Dias - R${signature_model.plan.value:.2f}\nVencimento do plano: {signature_model.due_date:%d/%m/%Y}\n\n{signature_model.plan.message}',
                reply_markup=quick_markup(
                    {
                        'Voltar': {'callback_data': 'return_to_main_menu'},
                    }
                ),
            )

    @bot.callback_query_handler(func=lambda c: c.data == 'sign')
    def sign(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha o plano',
            reply_markup=quick_markup(
                get_categories_reply_markup('sign'),
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'sign:' in c.data)
    def sign_action(callback_query):
        with Session() as session:
            plan_id = int(callback_query.data.split(':')[-1])
            plan_model = session.get(Plan, plan_id)
            payment_data = {
                'transaction_amount': plan_model.value,
                'description': f'{plan_model.name} - {plan_model.days} Dias - R${plan_model.value:.2f} - Vencimento: {(get_today_date() + timedelta(days=plan_model.days)).strftime("%d/%m/%Y")} - {callback_query.message.chat.username}',
                'payment_method_id': 'pix',
                'installments': 1,
                'payer': {
                    'email': config['PAYER_EMAIL'],
                },
            }
            response = mercado_pago_sdk.payment().create(payment_data)[
                'response'
            ]
            qr_code = response['point_of_interaction']['transaction_data'][
                'qr_code'
            ]
            bot.send_message(
                callback_query.message.chat.id,
                'Realize o pagamento para ativar o plano',
            )
            bot.send_message(
                callback_query.message.chat.id, 'Chave Pix abaixo:'
            )
            bot.send_message(callback_query.message.chat.id, qr_code)
            qr_code = qrcode.make(qr_code)
            qr_code_filename = f'{uuid4()}.png'
            qr_code.save(qr_code_filename)
            bot.send_photo(
                callback_query.message.chat.id,
                open(Path(qr_code_filename).absolute(), 'rb'),
            )
            os.remove(Path(qr_code_filename).absolute())
            with Session() as session:
                query = select(User).where(
                    User.username == callback_query.message.chat.username
                )
                user_model = session.scalars(query).first()
                payment = Payment(
                    chat_id=callback_query.message.chat.id,
                    user=user_model,
                    payment_id=str(response['id']),
                )
                session.add(payment)
                session.commit()

    @bot.callback_query_handler(func=lambda c: 'cancel_signature:' in c.data)
    def cancel_signature(callback_query):
        with Session() as session:
            signature_id = int(callback_query.data.split(':')[-1])
            signature_model = session.get(Signature, signature_id)
            session.delete(signature_model)
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Assinatura Cancelada!'
            )
            start(callback_query.message)
