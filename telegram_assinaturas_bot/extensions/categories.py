from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
    categories_factory,
)


def init_bot(bot, bot_username, start):
    def get_subscribers_label():
        users = repository.get_users(bot_username)
        actives, plan_actives = get_subscribers_count(
            repository.get_accounts(bot_username)
        )
        plan_message = ''
        for plan_name, active in plan_actives.items():
            plan_message += f'{plan_name}: {active}\n'
        return (
            f'Número de Usuários - {len(users)}\n'
            f'Ativos - {actives}\n'
            f'Inativos - {len(users) - actives}\n\n'
            f'{plan_message}'
        )

    def get_subscribers_count(accounts):
        actives = 0
        plan_subscribers = {}
        for account in accounts:
            for signature in account.signatures:
                if signature.due_date >= utils.get_today_date():
                    if plan_subscribers.get(signature.plan.name):
                        plan_subscribers[signature.plan.name] += 1
                    else:
                        plan_subscribers[signature.plan.name] = 1
                    actives += 1
        return actives, plan_subscribers

    @bot.callback_query_handler(config=categories_factory.filter())
    def show_categories_menu(callback_query):
        data = categories_factory.parse(callback_query.data)
        reply_markup = {}
        if data['category_id']:
            categories = repository.get_subcategories(
                bot_username, int(data['category_id'])
            )
        else:
            categories = repository.get_main_categories(bot_username)
        for category in categories:
            reply_markup['🗂 ' + category.name] = {
                'callback_data': utils.create_categories_callback_data(
                    action=data['action'],
                    argument=data['argument'],
                    category_id=category.id,
                ),
            }
        for plan in repository.get_plans_with_category(int(data['category_id'])):
            reply_markup[utils.get_plan_text(plan)] = {
                'callback_data': utils.create_actions_callback_data(
                    action=data['action'],
                    e=data['argument'],
                    p=plan.id,
                ),
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        if data['label'] == 'subscribers':
            label = get_subscribers_label()
        else:
            label = data['label']
        bot.send_message(
            callback_query.message.chat.id,
            label,
            reply_markup=quick_markup(
                reply_markup,
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'create_category')
    def create_category(callback_query):
        bot.send_message(callback_query.message.chat.id, 'Digite o nome da categoria')
        bot.register_next_step_handler(callback_query.message, on_add_category_name)

    def on_add_category_name(message):
        reply_markup = {}
        for category in repository.get_main_categories(bot_username):
            reply_markup[category.name] = {
                'callback_data': utils.create_actions_callback_data(
                    action='create_category',
                    c=category.id,
                    e=message.text,
                )
            }
        reply_markup['Nenhuma'] = {
            'callback_data': utils.create_actions_callback_data(
                action='create_category',
                c=0,
                e=message.text,
            )
        }
        bot.send_message(
            message.chat.id,
            'Subcategoria de',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='create_category'))
    def create_category_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        parent_category = repository.get_category(int(data['c']))
        if parent_category:
            parent_category_name = parent_category.name
        else:
            parent_category_name = 'Nenhuma'
        repository.create_category(bot_username, parent_category_name, data['e'])
        bot.send_message(callback_query.message.chat.id, 'Categoria Adicionada!')
        start(callback_query.message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_categories')
    def show_categories(callback_query):
        reply_markup = {}
        for category in repository.get_categories(bot_username):
            reply_markup[category.name] = {
                'callback_data': utils.create_actions_callback_data(
                    action='show_category',
                    c=category.id,
                )
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Categorias',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='show_category'))
    def show_category(callback_query):
        data = actions_factory.parse(callback_query.data)
        category = repository.get_category(int(data['c']))
        subcategories = repository.get_subcategories(bot_username, int(data['c']))
        child_categories = ', '.join([c.name for c in subcategories])
        bot.send_message(
            callback_query.message.chat.id,
            (
                f'Nome: {category.name}\n'
                f'Subcategoria de: {category.parent_category_name}\n'
                f'Subcategorias: {child_categories}'
            ),
            reply_markup=quick_markup(
                {
                    'Editar Nome': {
                        'callback_data': utils.create_actions_callback_data(
                            action='edit_category_name',
                            c=category.id,
                        ),
                    },
                    'Editar Subcategoria De': {
                        'callback_data': utils.create_actions_callback_data(
                            action='edit_parent_category',
                            c=category.id,
                        ),
                    },
                    'Remover Categoria': {
                        'callback_data': utils.create_actions_callback_data(
                            action='delete_category',
                            c=category.id,
                        )
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_category_name')
    )
    def edit_category_name(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(callback_query.message.chat.id, 'Digite o nome da categoria')
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_category_name(m, int(data['c']))
        )

    def on_category_name(message, category_id):
        repository.edit_category_name(category_id, message.text)
        bot.send_message(message.chat.id, 'Nome da Categoria Alterada!')
        start(message)

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_parent_category')
    )
    def edit_parent_category(callback_query):
        data = actions_factory.parse(callback_query.data)
        reply_markup = {}
        for parent_category in repository.get_categories_except(
            bot_username, int(data['c'])
        ):
            reply_markup[parent_category.name] = {
                'callback_data': utils.create_actions_callback_data(
                    action='edit_parent_category_action',
                    c=data['c'],
                    e=parent_category.id,
                )
            }
        reply_markup['Nenhuma'] = {
            'callback_data': utils.create_actions_callback_data(
                action='edit_parent_category_action',
                c=data['c'],
                e=0,
            )
        }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha a Categoria',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_parent_category_action')
    )
    def edit_parent_category_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.edit_parent_category(
            int(data['c']),
            int(data['e']),
        )
        bot.send_message(callback_query.message.chat.id, 'Categoria Alterada!')
        start(callback_query.message)

    @bot.callback_query_handler(config=actions_factory.filter(action='delete_category'))
    def delete_category_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_category(int(data['c']))
        bot.send_message(callback_query.message.chat.id, 'Categoria Removida!')
        start(callback_query.message)
