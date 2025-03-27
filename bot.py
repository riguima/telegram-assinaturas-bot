from importlib import import_module

import toml
from telebot import TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot.util import quick_markup

from telegram_grupo_vip_bot import repository, utils
from telegram_grupo_vip_bot.config import config

bot = TeleBot(config['BOT_TOKEN'])


class CallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call, config):
        return config.check(query=call)


@bot.message_handler(commands=['start', 'help', 'menu'])
def start(message):
    if message.chat.username:
        repository.create_update_user(
            username=message.chat.username,
            name=message.chat.first_name,
            chat_id=str(message.chat.id),
        )
        bot.send_message(
            message.chat.id,
            config.get(
                'Mensagem Menu',
                'Altere a mensagem do menu para ser mostrada aqui',
            ),
            reply_markup=quick_markup(
                get_menu_options(message),
                row_width=1
            ),
        )
    else:
        bot.send_message(
            message.chat.id,
            'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
        )


def get_menu_options(message):
    options = {}
    options['Minhas Assinaturas'] = {
        'callback_data': utils.create_actions_callback_data(
            action='show_signature', u=message.chat.username
        )
    }
    if message.chat.username in config['ADMINS']:
        options['Enviar Mensagem'] = {'callback_data': 'send_message'}
        options['Editar Mensagem do Menu'] = {'callback_data': 'edit_menu_message'}
        options['Adicionar Membro'] = {'callback_data': 'create_user'}
        options['Membros'] = {'callback_data': 'show_users'}
        options['Assinantes'] = {'callback_data': 'show_subscribers'}
        options['Adicionar Plano'] = {'callback_data': 'create_plan'}
        options['Planos'] = {
            'callback_data': utils.create_plans_callback_data(
                action='show_plan',
            )
        }
    return options


@bot.callback_query_handler(func=lambda c: c.data == 'edit_menu_message')
def edit_menu_message(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Envie a mensagem que vai ficar no menu\n\nTags: {nome}',
    )
    bot.register_next_step_handler(callback_query.message, on_menu_message)


def on_menu_message(message):
    config['Mensagem Menu'] = message.text
    toml.dump(config, open('.config.toml', 'w', encoding='utf-8'))
    bot.send_message(message.chat.id, 'Mensagem Editada!')
    start(message)


@bot.callback_query_handler(func=lambda c: c.data == 'show_main_menu')
def show_main_menu(callback_query):
    start(callback_query.message)


def load_extensions():
    for extension in config['EXTENSIONS']:
        extension_module = import_module(extension)
        extension_module.init_bot(bot, start)


if __name__ == '__main__':
    load_extensions()
    bot.add_custom_filter(CallbackFilter())
    bot.infinity_polling()
