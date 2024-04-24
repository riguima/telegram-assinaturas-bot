from importlib import import_module

import telebot
from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import User

bot = telebot.TeleBot(config['BOT_TOKEN'])


@bot.message_handler(commands=['start', 'help', 'menu'])
def start(message):
    if message.chat.username:
        with Session() as session:
            query = select(User).where(User.username == message.chat.username)
            user_model = session.scalars(query).first()
            if user_model is None:
                user_model = User(username=message.chat.username)
                session.add(user_model)
                session.commit()
                session.flush()
        options = {
            'Minha Assinatura': {
                'callback_data': f'show_signature:{message.chat.username}'
            },
        }
        if message.chat.id in config['ADMINS']:
            options['Adicionar Plano'] = {'callback_data': 'add_plan'}
            options['Planos'] = {'callback_data': 'show_plans'}
            options['Editar Mensagem de Plano'] = {
                'callback_data': 'edit_plan_message'
            }
            options['Adicionar Membro'] = {'callback_data': 'add_member'}
            options['Membros'] = {'callback_data': 'show_members'}
        bot.send_message(
            message.chat.id,
            'Sites compatíveis: Freepik, Baixardesign e Designi.\nPara realizar o download do arquivo desejado basta enviar o link do arquivo.\n\nOBS:\n- Enviar um link por vez.\n- Para habilitar o menú digite: /menu\n- Em caso de erro contate o suporte.',
            reply_markup=quick_markup(options, row_width=1),
        )
    else:
        bot.send_message(
            message.chat.id,
            'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
        )


@bot.callback_query_handler(func=lambda c: c.data == 'return_to_main_menu')
def return_to_main_menu(callback_query):
    start(callback_query.message)


def load_extensions():
    for extension in config['EXTENSIONS']:
        extension_module = import_module(extension)
        extension_module.init_bot(bot, start)


if __name__ == '__main__':
    load_extensions()
    bot.infinity_polling()
