from telebot.util import quick_markup

from telegram_grupo_vip_bot import repository, utils
from telegram_grupo_vip_bot.callbacks_datas import actions_factory, plans_factory


def init_bot(bot, start):
    @bot.callback_query_handler(config=plans_factory.filter())
    def show_plans_menu(callback_query):
        data = plans_factory.parse(callback_query.data)
        reply_markup = {}
        for plan in repository.get_plans():
            reply_markup[utils.get_plan_text(plan)] = {
                'callback_data': utils.create_actions_callback_data(
                    action=data['action'],
                    e=data['argument'],
                    p=plan.id,
                ),
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Planos',
            reply_markup=quick_markup(
                reply_markup,
                row_width=1,
            ),
        )

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
                    'Remover Plano': {
                        'callback_data': utils.create_actions_callback_data(
                            action='delete_plan',
                            p=data['p'],
                        ),
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(lambda c: c.data == 'create_plan')
    def create_plan(callback_query):
        bot.send_message(callback_query.message.chat.id, 'Digite nome para o plano')
        bot.register_next_step_handler(callback_query.message, on_plan_name)

    def on_plan_name(message):
        plan_data = {
            'name': message.text
        }
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
            plan_data['days'] = int(message.text)
            bot.send_message(message.chat.id, 'Digite a mensagem para o plano')
            bot.register_next_step_handler(
                message, lambda m: on_plan_message(m, plan_data)
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
            start(message)

    def on_plan_message(message, plan_data):
        repository.create_plan(
            value=plan_data['value'],
            name=plan_data['name'],
            days=plan_data['days'],
            message=message.text,
        )
        bot.send_message(message.chat.id, 'Plano Adicionado!')
        start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='edit_plan'))
    def edit_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup({
                'Editar Nome do Plano': {
                    'callback_data': utils.create_actions_callback_data(
                        action='edit_plan_name',
                        p=data['p'],
                    )
                },
                'Editar Valor do Plano': {
                    'callback_data': utils.create_actions_callback_data(
                        action='edit_plan_value',
                        p=data['p'],
                    )
                },
                'Editar Mensagem do Plano': {
                    'callback_data': utils.create_actions_callback_data(
                        action='edit_plan_message',
                        p=data['p'],
                    )
                },
            }, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='edit_plan_name'))
    def edit_plan_name(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(callback_query.message.chat.id, 'Digite o nome para o plano')
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_plan_name(m, int(data['p'])),
        )

    def on_edit_plan_name(message, plan_id):
        repository.edit_plan_name(plan_id, message.text)
        bot.send_message(message.chat.id, 'Nome Editado!')
        start(message)

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_plan_value')
    )
    def edit_plan_value(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id, 'Digite o valor do plano'
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_edit_plan_value(m, int(data['p']))
        )

    def on_edit_plan_value(message, plan_id):
        try:
            repository.edit_plan_value(plan_id, float(message.text.replace(',', '.')))
            bot.send_message(message.chat.id, 'Valor Editado!')
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

    @bot.callback_query_handler(config=actions_factory.filter(action='delete_plan'))
    def delete_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_plan(int(data['p']))
        bot.send_message(callback_query.message.chat.id, 'Plano Removido!')
        start(callback_query.message)
