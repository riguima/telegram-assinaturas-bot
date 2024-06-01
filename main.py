from importlib import import_module

import telebot
import toml
from sqlalchemy import select
from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Account, Plan, Signature, User
from telegram_assinaturas_bot.utils import (get_categories_reply_markup,
                                            get_today_date)

bot = telebot.TeleBot(config['BOT_TOKEN'])


@bot.message_handler(commands=['start', 'help', 'menu'])
def start(message):
    if message.chat.username:
        with Session() as session:
            query = select(User).where(User.username == message.chat.username)
            user_model = session.scalars(query).first()
            if user_model is None:
                user_model = User(
                    username=message.chat.username,
                    chat_id=str(message.chat.id),
                )
                session.add(user_model)
                session.commit()
                session.flush()
            elif user_model.chat_id is None:
                user_model.chat_id = str(message.chat.id)
                session.commit()
        options = {
            'Minhas Assinaturas': {
                'callback_data': f'show_signature:{message.chat.username}'
            },
        }
        if message.chat.id in config['ADMINS']:
            options['Enviar Mensagem'] = {'callback_data': 'send_message'}
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


@bot.callback_query_handler(func=lambda c: c.data == 'send_message')
def send_message(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Escolha uma opção',
        reply_markup=quick_markup(
            {
                'Enviar Para Todos os Membros': {
                    'callback_data': 'send_message_for_all_members'
                },
                'Enviar Somente Para Assinantes': {
                    'callback_data': 'send_message_for_subscribers'
                },
                'Enviar Para Membros de Plano': {
                    'callback_data': 'send_message_for_plan_members'
                },
            },
            row_width=1,
        ),
    )


@bot.callback_query_handler(
    func=lambda c: c.data == 'send_message_for_all_members'
)
def send_message_for_all_members(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Envie as mensagens que deseja enviar para todos os membros, utilize as tags: {nome}, digite /stop para parar',
    )
    bot.register_next_step_handler(
        callback_query.message, on_message_for_all_members
    )


def on_message_for_all_members(message, for_send_messages=[]):
    if message.text == '/stop':
        sending_message = bot.send_message(
            message.chat.id, 'Enviando Mensagens...'
        )
        with Session() as session:
            for member in session.scalars(select(User)).all():
                for for_send_message in for_send_messages:
                    try:
                        bot.send_message(
                            int(member.chat_id),
                            for_send_message.text.format(nome=member.username),
                        )
                    except ApiTelegramException:
                        continue
        bot.delete_message(message.chat.id, sending_message.id)
        bot.send_message(message.chat.id, 'Mensagens Enviadas!')
        start(message)
    else:
        for_send_messages.append(message)
        bot.register_next_step_handler(
            message, lambda m: on_message_for_all_members(m, for_send_messages)
        )


@bot.callback_query_handler(
    func=lambda c: c.data == 'send_message_for_subscribers'
)
def send_message_for_subscribers(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Envie as mensagens que deseja enviar para todos os membros ativos, utilize as tags: {nome}, digite /stop para parar',
    )
    bot.register_next_step_handler(
        callback_query.message, on_message_for_subscribers
    )


def on_message_for_subscribers(message, for_send_messages=[]):
    if message.text == '/stop':
        sending_message = bot.send_message(
            message.chat.id, 'Enviando Mensagens...'
        )
        with Session() as session:
            for member in session.scalars(select(User)).all():
                query = (
                    select(Signature)
                    .where(Signature.user_id == member.id)
                    .where(Signature.due_date >= get_today_date())
                )
                if session.scalars(query).all():
                    for for_send_message in for_send_messages:
                        try:
                            bot.send_message(
                                int(member.chat_id),
                                for_send_message.text.format(
                                    nome=member.username
                                ),
                            )
                        except ApiTelegramException:
                            continue
        bot.delete_message(message.chat.id, sending_message.id)
        bot.send_message(message.chat.id, 'Mensagens Enviadas!')
        start(message)
    else:
        for_send_messages.append(message)
        bot.register_next_step_handler(
            message, lambda m: on_message_for_subscribers(m, for_send_messages)
        )


@bot.callback_query_handler(
    func=lambda c: c.data == 'send_message_for_plan_members'
)
def send_message_for_plan_members(callback_query):
    bot.send_message(
        callback_query.message.chat.id,
        'Escolha o Plano',
        reply_markup=quick_markup(
            get_categories_reply_markup('send_message_for_plan_members'),
            row_width=1,
        ),
    )


@bot.callback_query_handler(
    func=lambda c: 'send_message_for_plan_members:' in c.data
)
def send_message_for_plan_members_action(callback_query):
    plan_id = int(callback_query.data.split(':')[-1])
    bot.send_message(
        callback_query.message.chat.id,
        'Envie as mensagens que deseja enviar para os membros desse plano, utilize as tags: {nome}, digite /stop para parar',
    )
    bot.register_next_step_handler(
        callback_query.message,
        lambda m: on_message_for_plan_members(m, plan_id),
    )


def on_message_for_plan_members(message, plan_id, for_send_messages=[]):
    if message.text == '/stop':
        sending_message = bot.send_message(
            message.chat.id, 'Enviando Mensagens...'
        )
        with Session() as session:
            for member in session.scalars(select(User)).all():
                query = (
                    select(Signature)
                    .where(Signature.user_id == member.id)
                    .where(Signature.plan_id == plan_id)
                    .where(Signature.due_date >= get_today_date())
                )
                if session.scalars(query).all():
                    for for_send_message in for_send_messages:
                        try:
                            bot.send_message(
                                int(member.chat_id),
                                for_send_message.text.format(
                                    nome=member.username
                                ),
                            )
                        except ApiTelegramException:
                            continue
        bot.delete_message(message.chat.id, sending_message.id)
        bot.send_message(message.chat.id, 'Mensagens Enviadas!')
        start(message)
    else:
        for_send_messages.append(message)
        bot.register_next_step_handler(
            message,
            lambda m: on_message_for_plan_members(
                m, plan_id, for_send_messages
            ),
        )


@bot.callback_query_handler(func=lambda c: c.data == 'show_subs')
def show_subscribers(callback_query):
    with Session() as session:
        users = session.scalars(select(User)).all()
        actives = 0
        plan_actives = {}
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
                if plan_actives.get(signature_model.plan.name):
                    plan_actives[signature_model.plan.name] += 1
                else:
                    plan_actives[signature_model.plan.name] = 1
        plan_message = ''
        for plan_name, active in plan_actives.items():
            plan_message += f'{plan_name}: {active}\n'
        bot.send_message(
            callback_query.message.chat.id,
            f'Número de Usuários: {len(users)}\nAtivos: {actives}\nInativos: {len(users) - actives}\n\n{plan_message}',
            reply_markup=quick_markup(
                get_categories_reply_markup('show_subs_of_plan'), row_width=1
            ),
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
        reply_markup['Voltar'] = {
            'callback_data': 'return_to_categories_menu:show_subs_of_plan'
        }
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
                    'Voltar': {
                        'callback_data': 'return_to_categories_menu:show_subs_of_plan'
                    },
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
