from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException

from app import bots
from app import create_bot as create_new_bot
from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import actions_factory


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'configure_bot')
    def configure_bot(callback_query):
        reply_markup = {}
        active_bots = repository.get_active_bots(callback_query.message.chat.username)
        if active_bots:
            reply_markup['Trocar Token do Bot'] = {
                'callback_data': 'edit_bot_token',
            }
        inactive_bots = repository.get_inactive_bots(
            callback_query.message.chat.username
        )
        if inactive_bots:
            reply_markup['Adicionar Novo Bot'] = {
                'callback_data': 'create_bot'
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup, row_width=1)
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'edit_bot_token')
    def edit_bot_token(callback_query):
        reply_markup = {}
        for user_bot in repository.get_active_bots(
            callback_query.message.chat.username
        ):
            reply_markup[bots[user_bot.token].get_me().username] = {
                'callback_data': utils.create_actions_callback_data(
                    action='edit_bot_token',
                    e=user_bot.id,
                )
            }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Bots',
            reply_markup=quick_markup(reply_markup, row_width=1),
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
        old_bot = repository.get_bot(bot_id)
        old_user_bot = bots[old_bot.token]
        old_user_bot.remove_webhook()
        repository.edit_bot_token(bot_id, message.text)
        new_bot = repository.get_bot_by_token(message.text)
        try:
            create_new_bot(new_bot)
            bot.send_message(message.chat.id, 'Bot Configurado!')
        except (ApiTelegramException, ValueError):
            bot.send_message(message.chat.id, 'Token inválido')
            repository.edit_bot_token(bot_id, old_bot.token)
            create_new_bot(old_bot)
        start(message)

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
        inactive_bots = repository.get_inactive_bots(message.chat.username)
        repository.edit_bot_token(inactive_bots[0].id, message.text)
        new_bot = repository.get_bot_by_token(message.text)
        try:
            create_new_bot(new_bot)
            bot.send_message(message.chat.id, 'Bot Configurado!')
        except (ApiTelegramException, ValueError):
            bot.send_message(message.chat.id, 'Token inválido')
            repository.edit_bot_token(inactive_bots[0].id, '')
        start(message)
