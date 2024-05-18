from importlib import import_module

import telebot
import toml
from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Signature, User, Plan, Account
from telegram_assinaturas_bot.utils import get_categories_reply_markup, get_today_date

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
            options['Editar Mensagem do Menu'] = {
                'callback_data': 'edit_menu_message'
            }
            options['Adicionar Conta'] = {'callback_data': 'add_account'}
            options['Contas'] = {'callback_data': 'show_accounts'}
            options['Adicionar Categoria'] = {'callback_data': 'add_category'}
            options['Categorias'] = {'callback_data': 'show_categories'}
            options['Assinantes'] = {'callback_data': 'show_subs'}
            options['Adicionar Plano'] = {'callback_data': 'add_plan'}
            options['Planos'] = {'callback_data': 'show_plans'}
            options['Adicionar Membro'] = {'callback_data': 'add_member'}
            options['Membros'] = {'callback_data': 'show_members'}
        bot.send_message(
            message.chat.id,
            config['MENU_MESSAGE'],
            reply_markup=quick_markup(options, row_width=1),
        )
    else:
        bot.send_message(
            message.chat.id,
            'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
        )


@bot.callback_query_handler(func=lambda c: c.data == 'show_subs')
def show_subscribers(callback_query):
    with Session() as session:
        users = session.scalars(select(User)).all()
        actives = 0
        for user_model in users:
            query = (
                select(Signature)
                .where(Signature.due_date >= get_today_date())
                .where(Signature.user_id == user_model.id)
            )
            signatures_models = session.scalars(query).all()
            if signatures_models:
                actives += 1
        bot.send_message(
            callback_query.message.chat.id,
            f'Número de Usuários: {len(users)}\nAtivos: {actives}\nInativos: {len(users) - actives}',
            reply_markup=quick_markup(get_categories_reply_markup('show_subs_of_plan'), row_width=1),
        )


@bot.callback_query_handler(func=lambda c: 'show_subs_of_plan:' in c.data)
def show_subscribers_of_plan(callback_query):
    plan_id = int(callback_query.data.split(':')[-1])
    with Session() as session:
        actives = 0
        plan_model = session.get(Plan, plan_id)
        for signature_model in plan_model.signatures:
            if signature_model.due_date >= get_today_date():
                actives += 1
        reply_markup = {}
        query = select(Account).where(Account.plan_id == int(plan_id))
        for account_model in session.scalars(query).all():
            label = (
                account_model.message
                if len(account_model.message) < 50
                else account_model.message[:40] + '...'
            )
            reply_markup[label] = {
                'callback_data': f'show_account_subs:{account_model.id}'
            }
        reply_markup['Voltar'] = {'callback_data': 'return_to_categories_menu:show_subs_of_plan'}
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )


@bot.callback_query_handler(func=lambda c: 'show_account_subs:' in c.data)
def show_account_subscribers(callback_query):
    account_id = int(callback_query.data.split(':')[-1])
    with Session() as session:
        actives = 0
        account_model = session.get(Account, account_id)
        users = ''
        for signature_model in account_model.signatures:
            if signature_model.due_date >= get_today_date():
                actives += 1
                users += f'@{signature_model.user.username}\n'
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}\n\n{users}',
            reply_markup=quick_markup(
                {
                    'Voltar': {'callback_data': 'return_to_categories_menu:show_subs_of_plan'},
                },
                row_width=1,
            ),
        )


@bot.callback_query_handler(func=lambda c: c.data == 'edit_menu_message')
def edit_menu_message(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Envie a mensagem que vai ficar no menu\n\nTags: {nome}',
    )
    bot.register_next_step_handler(callback_query.message, on_menu_message)


def on_menu_message(message):
    global config
    config['MENU_MESSAGE'] = message.text
    toml.dump(config, open('.config.toml', 'w'))
    bot.send_message(message.chat.id, 'Mensagem Editada!')
    start(message)


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
