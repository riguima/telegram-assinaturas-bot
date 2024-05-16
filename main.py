import re
from importlib import import_module

import telebot
from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Signature, User
from telegram_assinaturas_bot.utils import get_today_date

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
            'Minhas Assinaturas': {
                'callback_data': f'show_signature:{message.chat.username}'
            },
        }
        if message.chat.id in config['ADMINS']:
            options['Adicionar Categoria'] = {'callback_data': 'add_category'}
            options['Categorias'] = {'callback_data': 'show_categories'}
            options['Assinantes'] = {'callback_data': 'show_subscribers'}
            options['Adicionar Plano'] = {'callback_data': 'add_plan'}
            options['Planos'] = {'callback_data': 'show_plans'}
            options['Editar Mensagem de Plano'] = {
                'callback_data': 'edit_plan_message'
            }
            options['Adicionar Membro'] = {'callback_data': 'add_member'}
            options['Membros'] = {'callback_data': 'show_members'}
        bot.send_message(
            message.chat.id,
            'Ao adquirir sua assinatura, confira seu acesso na aba "Minhas Assinaturas" 🔍\n\n🚫 Proibido compartilhar a senha\n\nSe encontrar algum erro, entre em contato com o suporte 🛠️',
            reply_markup=quick_markup(options, row_width=1),
        )
    else:
        bot.send_message(
            message.chat.id,
            'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
        )


@bot.callback_query_handler(func=lambda c: c.data == 'show_subscribers')
def show_subscribers(callback_query):
    with Session() as session:
        users = session.scalars(select(User)).all()
        actives = 0
        plans = ''
        for user_model in users:
            query = (
                select(Signature)
                .where(Signature.due_date >= get_today_date())
                .where(Signature.user_id == user_model.id)
            )
            signatures_models = session.scalars(query).all()
            if signatures_models:
                actives += 1
                for signature_model in signatures_models:
                    if signature_model.plan.name in plans:
                        pattern = signature_model.plan.name + r': \d+'
                        actives_in_plan = int(
                            re.findall(
                                signature_model.plan.name + r': (\d+)', plans
                            )[0]
                        )
                        plans = re.sub(
                            pattern,
                            f'{signature_model.plan.name}: {actives_in_plan + 1}',
                            plans,
                        )
                    else:
                        plans += f'\n{signature_model.plan.name}: 1'
        bot.send_message(
            callback_query.message.chat.id,
            f'Número de Usuários: {len(users)}\nAtivos: {actives}\nInativos: {len(users) - actives}\n{plans}',
            reply_markup=quick_markup(
                {'Voltar': {'callback_data': 'return_to_main_menu'}}
            ),
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
