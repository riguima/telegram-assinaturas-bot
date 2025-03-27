import os
from pathlib import Path
from uuid import uuid4

import qrcode
from telebot.util import quick_markup

from telegram_grupo_vip_bot import repository, utils
from telegram_grupo_vip_bot.callbacks_datas import (
    actions_factory,
)


def init_bot(bot, start):
    @bot.callback_query_handler(config=actions_factory.filter(action='show_signature'))
    def show_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        user = repository.get_user_by_username(data['u'])
        signatures = repository.get_active_signatures(user.id)
        if signatures:
            reply_markup = {}
            for signature in signatures:
                reply_markup[utils.get_signature_text(signature)] = {
                    'callback_data': utils.create_actions_callback_data(
                        action='show_signature_message',
                        s=signature.id,
                    )
                }
            reply_markup['Comprar acesso'] = {'callback_data': 'ask_cpf_cnpj'}
            reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
            bot.send_message(
                callback_query.message.chat.id,
                'Escolha uma opção',
                reply_markup=quick_markup(reply_markup, row_width=1),
            )
        else:
            bot.send_message(
                callback_query.message.chat.id,
                'Você não possui uma assinatura ativa',
                reply_markup=quick_markup(
                    {
                        'Comprar acesso': {
                            'callback_data': utils.create_plans_callback_data(
                                action='ask_cpf_cnpj',
                            ),
                        },
                        'Voltar': {'callback_data': 'show_main_menu'},
                    },
                    row_width=1,
                ),
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
            callback_query.message.chat.username,
        )
        if user.cpf_cnpj is None or user.email is None:
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
        user = repository.get_user_by_username(message.chat.username)
        plan = repository.get_plan(plan_id)
        qr_code, payment_id = get_stripe_qrcode(user, plan)
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
            chat_id=message.chat.id,
            user_id=user.id,
            payment_id=payment_id,
            plan=plan,
        )

    def get_stripe_qrcode(user, plan):
        pass
        # due_date = utils.get_today_date() + timedelta(days=plan.days)
        # payment_data = {
        #    'transaction_amount': plan.value,
        #    'description': (
        #        f'{plan.name}'
        #        f' - {plan.days} Dias'
        #        f' - R${plan.value:.2f}'
        #        f' - Vencimento: {(due_date):%d/%m/%Y}'
        #        f' - {user.username}'
        #    ),
        #    'payment_method_id': 'pix',
        #    'installments': 1,
        #    'payer': {
        #        'email': user.email,
        #    },
        # }
        # response = mercado_pago_sdk.payment().create(payment_data)['response']
        # return (
        #    response['point_of_interaction']['transaction_data']['qr_code'],
        #    response['id'],
        # )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='cancel_signature')
    )
    def cancel_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_signature(int(data['s']))
        bot.send_message(callback_query.message.chat.id, 'Assinatura Cancelada!')
        start(callback_query.message)
