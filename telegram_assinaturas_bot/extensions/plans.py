from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Plan


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'add_plan')
    def add_plan(callback_query):
        bot.send_message(
            callback_query.message.chat.id, 'Digite nome para o plano'
        )
        bot.register_next_step_handler(callback_query.message, on_plan_name)

    def on_plan_name(message):
        bot.send_message(message.chat.id, 'Digite o valor para o plano')
        bot.register_next_step_handler(
            message, lambda m: on_plan_value(m, message.text)
        )

    def on_plan_value(message, plan_name):
        try:
            bot.send_message(
                message.chat.id, 'Digite a quantidade de dias do plano'
            )
            bot.register_next_step_handler(
                message,
                lambda m: on_plan_days(
                    m, plan_name, float(message.text.replace('.', ','))
                ),
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 19,99',
            )
            start(message)

    def on_plan_days(message, plan_name, plan_value):
        try:
            bot.send_message(message.chat.id, 'Digite a mensagem para o plano')
            bot.register_next_step_handler(
                message,
                lambda m: on_plan_message(
                    m, plan_name, plan_value, int(message.text)
                ),
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
            start(message)

    def on_plan_message(message, plan_name, plan_value, plan_days):
        with Session() as session:
            plan_model = Plan(
                value=plan_value,
                name=plan_name,
                message=message.text,
                days=plan_days,
            )
            session.add(plan_model)
            session.commit()
            bot.send_message(message.chat.id, 'Plano Adicionado!')
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_plans')
    def show_plans(callback_query):
        reply_markup = {}
        with Session() as session:
            for plan_model in session.scalars(select(Plan)).all():
                reply_markup[
                    f'{plan_model.name} - {plan_model.days} Dias - R${plan_model.value:.2f}'.replace(
                        '.', ','
                    )
                ] = {'callback_data': f'show_plan:{plan_model.id}'}
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(func=lambda c: 'show_plan:' in c.data)
    def show_plan_action(callback_query):
        plan_id = callback_query.data.split(':')[-1]
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Remover Plano': {
                        'callback_data': f'remove_plan:{plan_id}'
                    },
                    'Voltar': {'callback_data': 'return_to_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'remove_plan:' in c.data)
    def remove_plan_action(callback_query):
        with Session() as session:
            plan_id = int(callback_query.data.split(':')[-1])
            plan_model = session.get(Plan, plan_id)
            session.delete(plan_model)
            session.commit()
            bot.send_message(callback_query.message.chat.id, 'Plano Removido!')
            start(callback_query.message)
