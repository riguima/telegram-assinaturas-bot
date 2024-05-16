from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Category


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'add_category')
    def add_category(callback_query):
        bot.send_message(
            callback_query.message.chat.id, 'Digite o nome da categoria'
        )
        bot.register_next_step_handler(
            callback_query.message, on_add_category_name
        )

    def on_add_category_name(message):
        reply_markup = {}
        with Session() as session:
            query = select(Category).where(
                Category.parent_category_name == 'Nenhuma'
            )
            for category_model in session.scalars(query).all():
                reply_markup[category_model.name] = {
                    'callback_data': f'add_category:{category_model.id}:{message.text}'
                }
            reply_markup['Nenhuma'] = {
                'callback_data': f'add_category:0:{message.text}'
            }
        bot.send_message(
            message.chat.id,
            'Escolha uma Subcategoria',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(func=lambda c: 'add_category:' in c.data)
    def add_category_action(callback_query):
        parent_category_id, category_name = callback_query.data.split(':')[1:]
        with Session() as session:
            parent_category_model = session.get(
                Category, int(parent_category_id)
            )
            if parent_category_model:
                parent_category_name = parent_category_model.name
            else:
                parent_category_name = 'Nenhuma'
            category_model = Category(
                parent_category_name=parent_category_name,
                name=category_name,
            )
            session.add(category_model)
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Categoria Adicionada!'
            )
            start(callback_query.message)

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
            query = select(Category).where(
                Category.parent_category_name == category_model.name
            )
            child_categories = ', '.join(
                [c.name for c in session.scalars(query).all()]
            )
            bot.send_message(
                callback_query.message.chat.id,
                f'Nome: {category_model.name}\nSubcategoria de: {category_model.parent_category_name}\nSubcategorias: {child_categories}',
                reply_markup=quick_markup(
                    {
                        'Editar Nome': {
                            'callback_data': f'edit_category_name:{category_model.id}'
                        },
                        'Editar Subcategoria De': {
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
            category_model = session.get(Category, category_id)
            for parent_category_model in session.scalars(
                select(Category)
            ).all():
                if (
                    parent_category_model.name
                    != category_model.parent_category_name
                    and parent_category_model.name != category_model.name
                ):
                    reply_markup[parent_category_model.name] = {
                        'callback_data': f'edit_parent_category_name_action:{category_id}:{parent_category_model.id}'
                    }
            reply_markup['Nenhuma'] = {
                'callback_data': f'edit_parent_category_name_action:{category_id}:0'
            }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha a Categoria',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'edit_parent_category_name_action:' in c.data
    )
    def edit_parent_category_name_action(callback_query):
        category_id, parent_category_id = callback_query.data.split(':')[1:]
        with Session() as session:
            category_model = session.get(Category, int(category_id))
            parent_category_model = session.get(
                Category, int(parent_category_id)
            )
            if parent_category_model:
                category_model.parent_category_name = (
                    parent_category_model.name
                )
            else:
                category_model.parent_category_name = 'Nenhuma'
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Categoria Alterada!'
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
            query = select(Category).where(
                Category.parent_category_name == category_model.name
            )
            for child_category_model in session.scalars(query).all():
                child_category_model.parent_category_name = 'Nenhuma'
            session.delete(category_model)
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Categoria Removida!'
            )
            start(callback_query.message)
