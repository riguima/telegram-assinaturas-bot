from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Category, Plan
from telegram_assinaturas_bot.utils import get_categories_reply_markup

plan_data = {}


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: 'show_categories:' in c.data)
    def show_categories(callback_query):
        reply_markup = {}
        category_id = int(callback_query.data.split(':')[1])
        action = callback_query.data.split(':')[2]
        args = callback_query.data.split(':')[3:]
        with Session() as session:
            category_model = session.get(Category, category_id)
            for child_category_model in session.scalars(
                select(Category)
            ).all():
                if (
                    child_category_model.parent_category_name
                    == category_model.name
                ):
                    reply_markup['🗂 ' + child_category_model.name] = {
                        'callback_data': f'show_categories:{child_category_model.id}:'
                        + ':'.join([action, *args])
                    }
            for plan_model in category_model.plans:
                reply_markup[
                    f'{plan_model.name} - {plan_model.days} Dias - R${plan_model.value:.2f}'.replace(
                        '.', ','
                    )
                ] = {
                    'callback_data': ':'.join(
                        [action, str(plan_model.id), *args]
                    )
                }
            reply_markup['Voltar'] = {
                'callback_data': f'return_to_categories_menu:{action}'
            }
            bot.send_message(
                callback_query.message.chat.id,
                'Escolha uma opção',
                reply_markup=quick_markup(reply_markup, row_width=1),
            )

    @bot.callback_query_handler(
        func=lambda c: 'return_to_categories_menu:' in c.data
    )
    def return_to_categories_menu(callback_query):
        action = callback_query.data.split(':')[-1]
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(
                get_categories_reply_markup(action), row_width=1
            ),
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'add_plan')
    def add_plan(callback_query):
        with Session() as session:
            reply_markup = {}
            for category_model in session.scalars(select(Category)).all():
                reply_markup[category_model.name] = {
                    'callback_data': f'choose_plan_category:{category_model.id}'
                }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma categoria para o plano',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'choose_plan_category:' in c.data
    )
    def choose_plan_category(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        plan_data[callback_query.message.chat.username] = {
            'category_id': category_id
        }
        bot.send_message(
            callback_query.message.chat.id, 'Digite nome para o plano'
        )
        bot.register_next_step_handler(callback_query.message, on_plan_name)

    def on_plan_name(message):
        plan_data[message.chat.username]['plan_name'] = message.text
        bot.send_message(message.chat.id, 'Digite o valor para o plano')
        bot.register_next_step_handler(message, on_plan_value)

    def on_plan_value(message):
        try:
            plan_data[message.chat.username]['plan_value'] = float(
                message.text.replace(',', '.')
            )
            bot.send_message(
                message.chat.id, 'Digite a quantidade de dias do plano'
            )
            bot.register_next_step_handler(message, on_plan_days)
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 19,99',
            )
            start(message)

    def on_plan_days(message):
        try:
            data = plan_data[message.chat.username]
            with Session() as session:
                category_model = session.get(Category, data['category_id'])
                plan_model = Plan(
                    value=data['plan_value'],
                    name=data['plan_name'],
                    days=int(message.text),
                    category=category_model,
                )
                session.add(plan_model)
                session.commit()
                bot.send_message(message.chat.id, 'Plano Adicionado!')
            start(message)
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'edit_plan_message')
    def edit_plan_message(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(
                get_categories_reply_markup('edit_plan_message'), row_width=1
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'edit_plan_message:' in c.data)
    def edit_plan_message_action(callback_query):
        plan_id = int(callback_query.data.split(':')[-1])
        bot.send_message(
            callback_query.message.chat.id, 'Digite a mensagem para o plano'
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_edit_plan_message(m, plan_id)
        )

    def on_edit_plan_message(message, plan_id):
        with Session() as session:
            plan_model = session.get(Plan, plan_id)
            plan_model.message = message.text
            session.commit()
            bot.send_message(message.chat.id, 'Mensagem Editada!')
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_plans')
    def show_plans(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(
                get_categories_reply_markup('show_plan'), row_width=1
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'show_plan:' in c.data)
    def show_plan_action(callback_query):
        plan_id = callback_query.data.split(':')[-1]
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Editar Plano': {'callback_data': f'edit_plan:{plan_id}'},
                    'Remover Plano': {
                        'callback_data': f'remove_plan:{plan_id}'
                    },
                    'Voltar': {'callback_data': 'return_to_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'remove_plan:' in c.data)
    def remove_plan(callback_query):
        with Session() as session:
            plan_id = int(callback_query.data.split(':')[-1])
            plan_model = session.get(Plan, plan_id)
            session.delete(plan_model)
            session.commit()
            bot.send_message(callback_query.message.chat.id, 'Plano Removido!')
            start(callback_query.message)

    @bot.callback_query_handler(func=lambda c: 'edit_plan:' in c.data)
    def edit_plan(callback_query):
        plan_id = int(callback_query.data.split(':')[-1])
        bot.send_message(
            callback_query.message.chat.id, 'Digite o nome para o plano'
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_plan_name(m, plan_id),
        )

    def on_edit_plan_name(message, plan_id):
        with Session() as session:
            plan_model = session.get(Plan, plan_id)
            plan_model.name = message.text
            session.commit()
            bot.send_message(message.chat.id, 'Digite o valor do plano')
            bot.register_next_step_handler(
                message, lambda m: on_edit_plan_value(m, plan_id)
            )

    def on_edit_plan_value(message, plan_id):
        try:
            with Session() as session:
                plan_model = session.get(Plan, plan_id)
                plan_model.value = float(message.text.replace(',', '.'))
                session.commit()
                bot.send_message(message.chat.id, 'Plano Editado!')
                start(message)
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 19,90',
            )
            start(message)
