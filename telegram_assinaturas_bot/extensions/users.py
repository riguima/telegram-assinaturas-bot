from datetime import timedelta

from telebot.util import quick_markup

from app import bots
from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
)
from telegram_assinaturas_bot.config import config


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'create_user')
    def add_user(callback_query):
        bot.send_message(callback_query.message.chat.id, 'Digite o arroba do membro')
        bot.register_next_step_handler(callback_query.message, on_username)

    def on_username(message):
        repository.create_user(
            bot_token=bot_token,
            username=message.text,
        )
        bot.send_message(message.chat.id, 'Membro Adicionado!')
        start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_users')
    def show_users(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Membros',
            reply_markup=quick_markup(
                {
                    'Buscar Membros': {
                        'callback_data': utils.create_actions_callback_data(
                            action='show_users',
                            e='search',
                        ),
                    },
                    'Ver Membros': {
                        'callback_data': utils.create_actions_callback_data(
                            action='show_users',
                            e='all',
                        ),
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='show_users'))
    def show_users_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        if data['e'] == 'search':
            bot.send_message(
                callback_query.message.chat.id,
                'Digite o termo para busca',
            )
            bot.register_next_step_handler(
                callback_query.message,
                on_search_term,
            )
        else:
            send_users_message(
                callback_query.message,
                repository.get_users(bot_token),
            )

    def on_search_term(message):
        options = {}
        options['Buscar Membros'] = {
            'callback_data': utils.create_actions_callback_data(
                action='show_users',
                e='search',
            ),
        }
        send_users_message(
            message,
            repository.search_users(bot_token, message.text),
            options,
        )

    def send_users_message(message, users, options={}):
        for user in users:
            options[user.username] = {
                'callback_data': utils.create_actions_callback_data(
                    action='show_user',
                    u=user.username,
                ),
            }
        options['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            message.chat.id,
            'Membros',
            reply_markup=quick_markup(options, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='show_user'))
    def show_user_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        user = repository.get_user_by_username(bot_token, data['u'])
        reply_markup = {}
        if bot_token == config['BOT_TOKEN']:
            reply_markup['Adicionar Bots'] = {
                'callback_data': utils.create_actions_callback_data(
                    action='add_user_bot',
                    u=user.username,
                ),
            }
        else:
            for signature in repository.get_active_signatures(user.id):
                reply_markup[utils.get_signature_text(signature)] = {
                    'callback_data': utils.create_actions_callback_data(
                        action='show_user_signature',
                        s=signature.id,
                    )
                }
            reply_markup['Adicionar Plano'] = {
                'callback_data': utils.create_categories_callback_data(
                    label='Escolha a Conta',
                    action='add_user_plan_menu',
                    argument=user.username,
                ),
            }
        reply_markup['Enviar Mensagem'] = {
            'callback_data': utils.create_actions_callback_data(
                action='send_message',
                e='user',
                u=user.username,
            )
        }
        reply_markup['Remover Membro'] = {
            'callback_data': utils.create_actions_callback_data(
                action='delete_user',
                u=user.username,
            )
        }
        reply_markup['Voltar'] = {'callback_data': 'show_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_user_signature')
    )
    def show_user_signature(callback_query):
        data = actions_factory.parse(callback_query.data)
        signature = repository.get_signature(int(data['s']))
        bot.send_message(
            callback_query.message.chat.id,
            utils.get_signature_text(signature, with_due_date=True),
            reply_markup=quick_markup(
                {
                    'Escolher Conta': {
                        'callback_data': utils.create_actions_callback_data(
                            action='show_plan_accounts',
                            e='choose_account',
                            p=signature.plan_id,
                            s=signature.id,
                        ),
                    },
                    'Cancelar Assinatura': {
                        'callback_data': utils.create_actions_callback_data(
                            action='cancel_signature',
                            s=int(data['s']),
                        )
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='choose_account'))
    def choose_account(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Adicionar Conta ao Plano': {
                        'callback_data': utils.create_actions_callback_data(
                            action='add_account_in_plan',
                            s=data['s'],
                            p=data['p'],
                        )
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='add_account_in_plan')
    )
    def add_account_in_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.edit_signature_account(int(data['s']), int(data['p']))
        bot.send_message(callback_query.message.chat.id, 'Conta Adicionada!')
        start(callback_query.message)

    @bot.callback_query_handler(config=actions_factory.filter(action='add_user_plan'))
    def add_user_plan(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Digite a quantidade de dias de acesso',
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_signatures_days(m, data['u'], int(data['a'])),
        )

    def on_signatures_days(message, username, account_id):
        try:
            user = repository.get_user_by_username(bot_token, username)
            account = repository.get_account(account_id)
            plan = repository.get_plan_from_account(account_id)
            repository.create_signature(
                bot_token=bot_token,
                user_id=user.id,
                plan_id=plan.id,
                account_id=account.id,
                due_date=utils.get_today_date() + timedelta(days=int(message.text)),
            )
            if user.chat_id:
                bot.send_message(
                    int(user.chat_id),
                    (
                        f'Olá, {user.username}.\n\n'
                        f'Adicionado {int(message.text)} dias para o plano '
                        f'{plan.name}.\n\nDigite /start e clique em '
                        '"Minhas assinaturas" para ter acesso a nova senha.'
                    ),
                )
            bot.send_message(message.chat.id, 'Membro Adicionado a Conta!')
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
        start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='add_user_bot'))
    def add_user_bot(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Digite a quantidade de bots que o admin poderá adicionar',
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_bots_number(m, data['u'])
        )

    def on_bots_number(message, username):
        try:
            bot.send_message(message.chat.id, 'Digite o número de dias de acesso dos bots')
            bot.register_next_step_handler(
                message,
                lambda m: on_bots_days(m, username, int(message.text))
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )

    def on_bots_days(message, username, bots_number):
        for _ in range(bots_number):
            repository.create_bot(
                username=username,
                token='',
                due_date=utils.get_today_date() + timedelta(days=int(message.text)),
            )
        bot.send_message(message.chat.id, 'Bots Adicionados!')
        start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='delete_user'))
    def delete_user_action(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_user_by_username(bot_token, data['u'])
        bot.send_message(callback_query.message.chat.id, 'Membro Removido!')
        start(callback_query.message)
