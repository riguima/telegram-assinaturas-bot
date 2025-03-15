from telebot.util import quick_markup

from app import bots
from app import create_bot as create_new_bot
from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import actions_factory


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'configure_bot')
    def configure_bot(callback_query):
        reply_markup = {
            'Trocar Token do Bot': {
                'callback_data': 'edit_bot_token',
            },
        }
        without_configuration_bots = repository.get_inactive_bots(
            callback_query.message.chat.username
        )
        if without_configuration_bots:
            reply_markup['Adicionar Novo Bot'] = {
                'callback_data': 'create_bot'
            }
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup)
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'edit_bot_token')
    def edit_bot_token(callback_query):
        reply_markup = {}
        for user_bot in repository.get_active_bots(
            callback_query.message.chat.username
        ):
            reply_markup[user_bot.username] = {
                'callback_data': utils.create_actions_callback_data(
                    action='edit_bot_token',
                    e=user_bot.id,
                )
            }
        bot.send_message(
            callback_query.message.chat.id,
            'Bots',
            reply_markup=quick_markup(reply_markup),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='edit_bot_token'))
    def edit_bot_token_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(callback_query.message.chat.id, 'Digite o Token do bot')
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_bot_token(m, int(data['e'])),
        )

    def on_edit_bot_token(message, bot_id):
        old_user_bot = bots[repository.get_bot(bot_id).token]
        old_user_bot.remove_webhook()
        repository.edit_bot_token(bot_id, message.text)
        user_bot = repository.get_bot_by_token(message.text)
        create_new_bot(user_bot)

    @bot.callback_query_handler(func=lambda c: c.data == 'create_bot')
    def create_bot(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Digite o Token do bot',
        )
        bot.register_next_step_handler(
            callback_query.message,
            on_create_bot_token,
        )

    def on_create_bot_token(message):
        updated_bot = repository.create_bot(
            username=message.chat.username,
            token=message.text,
        )
        create_new_bot(updated_bot)
        bot.send_message(message.chat.id, 'Bot Configurado!')
        start(message)
