from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
)


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'send_message')
    def send_message(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Enviar Para Todos os Membros': {
                        'callback_data': utils.create_actions_callback_data(
                            action='send_message',
                            e='all_users',
                        )
                    },
                    'Enviar Somente Para Assinantes': {
                        'callback_data': utils.create_actions_callback_data(
                            action='send_message',
                            e='subscribers',
                        )
                    },
                    'Enviar Para Membros de Plano': {
                        'callback_data': utils.create_categories_callback_data(
                            label='Escolha o Plano',
                            action='send_message',
                            argument='plan_users',
                        ),
                    },
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='send_message'))
    def send_message_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Envie as mensagens que deseja repassar, /stop para parar',
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_message(m, data['e'], data['p'], data['u']),
        )

    def on_message(message, argument, plan_id=None, username=None, messages_ids=[]):
        if message.text == '/stop':
            sending_message = bot.send_message(message.chat.id, 'Enviando Mensagens...')
            users = {
                'all_users': lambda: repository.get_users(bot_token),
                'subscribers': lambda: repository.get_subscribers(bot_token),
                'plan_users': lambda: repository.get_plan_users(int(plan_id)),
                'user': lambda: list(
                    repository.get_user_by_username(bot_token, username)
                ),
            }
            for user in users[argument]():
                try:
                    if user.chat_id:
                        bot.copy_messages(
                            int(user.chat_id),
                            message.chat.id,
                            messages_ids,
                        )
                except ApiTelegramException:
                    pass
            bot.delete_message(message.chat.id, sending_message.id)
            bot.send_message(message.chat.id, 'Mensagens Enviadas!')
            start(message)
        else:
            messages_ids.append(message.id)
            bot.register_next_step_handler(
                message,
                lambda m: on_message(
                    m,
                    argument,
                    plan_id=plan_id,
                    username=username,
                    messages_ids=messages_ids,
                ),
            )
