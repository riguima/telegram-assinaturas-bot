from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Category


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'show_categories')
    def show_categories(callback_query):
        with Session() as session:
            reply_markup = {}
            for category in session.scalars(select(Category)).all():
                reply_markup[category.name] = {
                    'callback_data': f'show_category:{category.id}'
                }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
            bot.send_message(
                callback_query.message.chat.id,
                'Categorias',
                reply_markup=quick_markup(reply_markup, row_width=1),
            )

    @bot.callback_query_handler(func=lambda c: 'show_category:' in c.data)
    def show_category(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            category_model = session.get(Category, category_id)
            bot.send_message(
                callback_query.message.chat.id,
                f'Nome: {category_model.name}\nSubcategoria de: {category_model.parent_category_name}\nSubcategoria: {category_model.child_category_name}',
                reply_markup=quick_markup(
                    {
                        'Editar Nome': {
                            'callback_data': f'edit_category_name:{category_model.id}'
                        },
                        'Editar Categoria Pai': {
                            'callback_data': f'edit_parent_category_name:{category_model.id}'
                        },
                        'Remover Categoria': {
                            'callback_data': f'remove_category:{category_model.id}'
                        },
                        'Voltar': {'callback_data': 'return_to_main_menu'},
                    },
                    row_width=1,
                ),
            )

    @bot.callback_query_handler(func=lambda c: 'edit_category_name:' in c.data)
    def edit_category_name(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        bot.send_message(
            callback_query.message.chat.id, 'Digite o nome da categoria'
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_category_name(m, category_id)
        )

    def on_category_name(message, category_id):
        with Session() as session:
            category_model = session.get(Category, category_id)
            category_model.name = message.text
            session.commit()
            bot.send_message(message.chat.id, 'Nome da Categoria Alterada!')
            start(message)

    @bot.callback_query_handler(
        func=lambda c: 'edit_parent_category_name:' in c.data
    )
    def edit_parent_category_name(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            reply_markup = {}
            for category_model in session.scalars(select(Category)).all():
                if category_model.name != category_model.parent_category_name:
                    reply_markup[category_model.name] = {
                        'callback_data': f'edit_parent_category_name_action:{category_id}:{category_model.id}'
                    }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha a Categoria Pai',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'edit_parent_category_name_action:' in c.data
    )
    def edit_parent_category_name_action(callback_query):
        category_id, child_category_id = callback_query.data.split(':')[1:]
        with Session() as session:
            category_model = session.get(Category, int(category_id))
            child_category_model = session.get(
                Category, int(child_category_id)
            )
            category_model.parent_category_name = child_category_model.name
            child_category_model.child_category_name = category_model.name
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Categoria Pai Alterada!'
            )
            start(callback_query.message)

    @bot.callback_query_handler(func=lambda c: c.data == 'remove_category')
    def remove_category(callback_query):
        with Session() as session:
            reply_markup = {}
            for category_model in session.scalars(select(Category)).all():
                reply_markup[category_model.name] = {
                    'callback_data': f'remove_category:{category_model.id}'
                }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma Categoria',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(func=lambda c: 'remove_category:' in c.data)
    def remove_category_action(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            category_model = session.get(Category, category_id)
            session.delete(category_model)
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Categoria Removida!'
            )
            start(callback_query.message)
