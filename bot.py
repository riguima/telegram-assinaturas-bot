from importlib import import_module

import toml
from sqlalchemy import select
from telebot import TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot.util import quick_markup, update_types

from telegram_grupo_vip_bot.callbacks_datas import actions_factory
from telegram_grupo_vip_bot import utils
from telegram_grupo_vip_bot.config import config
from telegram_grupo_vip_bot.database import Session
from telegram_grupo_vip_bot.models import User

bot = TeleBot(config['BOT_TOKEN'])


class CallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call, config):
        return config.check(query=call)


@bot.message_handler(commands=['start', 'help', 'menu'])
def start(message):
    with Session() as session:
        if message.chat.username:
            query = select(User).where(
                User.username == message.chat.username
            )
            user_model = session.scalars(query).first()
            if user_model is None:
                user_model = User(
                    username=message.chat.username,
                    chat_id=str(message.chat.id),
                )
                session.add(user_model)
                session.commit()
            else:
                user_model.chat_id = str(message.chat.id)
                user_model.name = message.chat.first_name
                session.commit()
            bot.send_message(
                message.chat.id,
                config.get(
                    'MENU_MESSAGE',
                    'Altere a mensagem do menu para ser mostrada aqui',
                ).format(nome=message.chat.first_name),
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
        options['Selecionar Grupo/Canal'] = {'callback_data': 'choose_group_channel'}
        options['Editar Mensagem do Menu'] = {'callback_data': 'edit_menu_message'}
    return options


@bot.callback_query_handler(func=lambda c: c.data == 'choose_group_channel')
def choose_group_channel(callback_query):
    reply_markup = {}
    for group in config['GROUPS']:
        reply_markup[group['name']] = {
            'callback_data': utils.create_actions_callback_data(
                action='choose_group_channel',
                e=group['chat_id']
            ),
        }
    reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
    bot.send_message(
        callback_query.message.chat.id,
        'Escolha um Grupo/Canal',
        reply_markup=quick_markup(reply_markup, row_width=1),
    )


@bot.callback_query_handler(config=actions_factory.filter(action='choose_group_channel'))
def choose_group_channel_action(callback_query):
    data = actions_factory.parse(callback_query.data)
    config['CHAT_ID'] = data['e']
    toml.dump(config, open('.config.toml', 'w', encoding='utf-8'))
    bot.send_message(callback_query.message.chat.id, 'Grupo Selecionado!')
    start(callback_query.message)


@bot.my_chat_member_handler()
def on_joined(message):
    new = message.new_chat_member
    if new.status == "administrator":
        config['GROUPS'].append({
            'name': message.chat.title,
            'chat_id': message.chat.id,
        })
        toml.dump(config, open('.config.toml', 'w', encoding='utf-8'))


@bot.callback_query_handler(func=lambda c: c.data == 'edit_menu_message')
def edit_menu_message(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Envie a mensagem que vai ficar no menu\n\nTags: {nome}',
    )
    bot.register_next_step_handler(callback_query.message, on_menu_message)


def on_menu_message(message):
    config['MENU_MESSAGE'] = message.text
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
    bot.infinity_polling(allowed_updates=update_types)
