import stripe
from sqlalchemy import select
from telebot.util import quick_markup

from telegram_grupo_vip_bot import utils
from telegram_grupo_vip_bot.callbacks_datas import (
    actions_factory,
)
from telegram_grupo_vip_bot.config import config
from telegram_grupo_vip_bot.database import Session
from telegram_grupo_vip_bot.models import Payment, Signature, User

stripe.api_key = config['STRIPE_API_KEY']


def init_bot(bot, start):
    @bot.callback_query_handler(config=actions_factory.filter(action='show_signature'))
    def show_signature(callback_query):
        with Session() as session:
            data = actions_factory.parse(callback_query.data)
            user = session.scalar(select(User).where(User.username == data['u']))
            query = select(Signature).where(
                Signature.due_date >= utils.get_today_date(),
                Signature.user_id == user.id,
            )
            signatures = session.scalars(query).all()
            if signatures:
                reply_markup = {}
                for signature in signatures:
                    plan = stripe.Plan.retrieve(signature.plan_id)
                    reply_markup[utils.get_signature_text(signature, plan)] = {
                        'callback_data': utils.create_actions_callback_data(
                            action='show_signature_message',
                            s=signature.id,
                        )
                    }
                reply_markup['Comprar acesso'] = {
                    'callback_data': 'sign',
                }
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
                                'callback_data': 'sign',
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
        with Session() as session:
            data = actions_factory.parse(callback_query.data)
            signature = session.get(Signature, int(data['s']))
            plan = stripe.Plan.retrieve(signature.plan_id)
            try:
                message = (
                    f'{utils.get_signature_text(signature, plan, with_due_date=True)}'
                )
            except AttributeError:
                message = utils.get_signature_text(signature, plan, with_due_date=True)
            user = session.get(User, signature.user_id)
            bot.send_message(
                callback_query.message.chat.id,
                message,
                reply_markup=quick_markup({
                    'Voltar': {
                        'callback_data': utils.create_actions_callback_data(
                            action='show_signature',
                            u=user.username,
                        )
                    }
                }),
            )

    @bot.callback_query_handler(func=lambda c: c.data == 'sign')
    def sign(callback_query):
        reply_markup = {}
        for plan in sorted(stripe.Plan.list()['data'], key=lambda p: p['amount']):
            reply_markup[utils.get_plan_text(plan)] = {
                'callback_data': utils.create_actions_callback_data(
                    action='choose_plan',
                    p=plan['id'],
                )
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='choose_plan'))
    def choose_plan(callback_query):
        with Session() as session:
            data = actions_factory.parse(callback_query.data)
            user = session.scalar(
                select(User)
                .where(User.username == callback_query.message.chat.username)
            )
            plan = stripe.Plan.retrieve(data['p'])
            payment = create_stripe_payment(user, plan)
            bot.send_message(
                callback_query.message.chat.id,
                f'Realize o pagamento para ativar o plano\n\nLink: {payment["url"]}',
            )
            payment = Payment(
                chat_id=callback_query.message.chat.id,
                user_id=user.id,
                payment_id=payment['id'],
                plan_id=data['p'],
            )
            session.add(payment)
            session.commit()

    def create_stripe_payment(user, plan):
        if plan['interval'] == 'month':
            payment = stripe.PaymentLink.create(
                line_items=[
                    {"price": plan['id'], "quantity": 1}
                ],
            )
        return payment

    @bot.callback_query_handler(
        config=actions_factory.filter(action='cancel_signature')
    )
    def cancel_signature(callback_query):
        with Session() as session:
            data = actions_factory.parse(callback_query.data)
            signature = session.get(Signature, int(data['s']))
            session.delete(signature)
            session.commit()
            bot.send_message(callback_query.message.chat.id, 'Assinatura Cancelada!')
            start(callback_query.message)
