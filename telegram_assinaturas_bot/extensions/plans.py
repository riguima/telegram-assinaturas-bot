from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import actions_factory


def init_bot(bot, bot_username, start):
    @bot.callback_query_handler(config=actions_factory.filter(action='show_plan'))
    def show_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Editar Plano': {
                        'callback_data': utils.create_actions_callback_data(
                            action='edit_plan',
                            p=data['p'],
                        ),
                    },
                    'Editar Mensagem do Plano': {
                        'callback_data': utils.create_actions_callback_data(
                            action='edit_plan_message',
                            p=data['p'],
                        )
                    },
                    'Remover Plano': {
                        'callback_data': utils.create_actions_callback_data(
                            action='remove_plan',
                            p=data['p'],
                        ),
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'create_plan')
    def create_plan(callback_query):
        reply_markup = {}
        for category in repository.get_categories(bot_username):
            reply_markup[f'🗂 {category.name}'] = {
                'callback_data': utils.create_actions_callback_data(
                    action='choose_plan_category',
                    c=category.id,
                )
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma categoria para o plano',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='choose_plan_category')
    )
    def choose_plan_category(callback_query):
        data = actions_factory.parse(callback_query.data)
        plan_data = {'category_id': int(data['c'])}
        bot.send_message(callback_query.message.chat.id, 'Digite nome para o plano')
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_plan_name(m, plan_data)
        )

    def on_plan_name(message, plan_data):
        plan_data['name'] = message.text
        bot.send_message(message.chat.id, 'Digite o valor para o plano')
        bot.register_next_step_handler(message, lambda m: on_plan_value(m, plan_data))

    def on_plan_value(message, plan_data):
        try:
            plan_data['value'] = float(message.text.replace(',', '.'))
            bot.send_message(message.chat.id, 'Digite a quantidade de dias do plano')
            bot.register_next_step_handler(
                message, lambda m: on_plan_days(m, plan_data)
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 19,99',
            )
            start(message)

    def on_plan_days(message, plan_data):
        try:
            repository.create_plan(
                bot_username=bot_username,
                value=plan_data['value'],
                name=plan_data['name'],
                days=int(message.text),
                category_id=plan_data['category_id'],
            )
            bot.send_message(message.chat.id, 'Plano Adicionado!')
            start(message)
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
            start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='edit_plan'))
    def edit_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(callback_query.message.chat.id, 'Digite o nome para o plano')
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_plan_name(m, int(data['p'])),
        )

    def on_edit_plan_name(message, plan_id):
        repository.edit_plan_name(plan_id, message.text)
        bot.send_message(message.chat.id, 'Digite o valor do plano')
        bot.register_next_step_handler(
            message, lambda m: on_edit_plan_value(m, plan_id)
        )

    def on_edit_plan_value(message, plan_id):
        try:
            repository.edit_plan_value(plan_id, float(message.text.replace(',', '.')))
            bot.send_message(message.chat.id, 'Plano Editado!')
            start(message)
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 19,90',
            )
            start(message)

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_plan_message')
    )
    def edit_plan_message(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id, 'Digite a mensagem para o plano'
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_edit_plan_message(m, int(data['p']))
        )

    def on_edit_plan_message(message, plan_id):
        repository.edit_plan_message(plan_id, message.text)
        bot.send_message(message.chat.id, 'Mensagem Editada!')
        start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='remove_plan'))
    def delete_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.remove_plan(int(data['p']))
        bot.send_message(callback_query.message.chat.id, 'Plano Removido!')
        start(callback_query.message)
