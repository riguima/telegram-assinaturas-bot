from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Account, Category

account_data = {}


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'add_account')
    def add_account(callback_query):
        reply_markup = {}
        with Session() as session:
            for category_model in session.scalars(select(Category)).all():
                reply_markup[category_model.name] = {
                    'callback_data': f'choose_account_category:{category_model.id}'
                }
        reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Selecione a categoria',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'choose_account_category:' in c.data
    )
    def choose_account_category(callback_query):
        category_id = int(callback_query.data.split(':')[-1])
        account_data[callback_query.message.chat.username] = {
            'category_id': category_id
        }
        bot.send_message(
            callback_query.message.chat.id, 'Digite o Login da conta'
        )
        bot.register_next_step_handler(
            callback_query.message, on_account_login
        )

    def on_account_login(message):
        account_data[message.chat.username]['login'] = message.text
        bot.send_message(message.chat.id, 'Digite a Senha da conta')
        bot.register_next_step_handler(message, on_account_password)

    def on_account_password(message):
        account_data[message.chat.username]['password'] = message.text
        bot.send_message(
            message.chat.id,
            'Digite o número de acessos limitados a essa conta',
        )
        bot.register_next_step_handler(message, on_account_users_number)

    def on_account_users_number(message):
        with Session() as session:
            try:
                account_model = Account(
                    category_id=account_data[message.chat.username][
                        'category_id'
                    ],
                    login=account_data[message.chat.username]['login'],
                    password=account_data[message.chat.username]['password'],
                    users_number=int(message.text),
                )
                session.add(account_model)
                session.commit()
                bot.send_message(message.chat.id, 'Conta Adicionada!')
            except ValueError:
                bot.send_message(
                    'Valor inválido, digite como no exemplo: 10 ou 15'
                )
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_accounts')
    def show_accounts(callback_query):
        with Session() as session:
            reply_markup = {}
            for account_model in session.scalars(select(Account)).all():
                reply_markup[account_model.login] = {
                    'callback_data': f'show_account:{account_model.id}'
                }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
            bot.send_message(
                callback_query.message.chat.id,
                'Contas',
                reply_markup=quick_markup(reply_markup, row_width=1),
            )

    @bot.callback_query_handler(func=lambda c: 'show_account:' in c.data)
    def show_category(callback_query):
        account_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            account_model = session.get(Account, account_id)
            bot.send_message(
                callback_query.message.chat.id,
                f'Login: {account_model.login}\nSenha: {account_model.password}\nCategoria: {account_model.category.name}',
                reply_markup=quick_markup(
                    {
                        'Editar': {
                            'callback_data': f'edit_account:{account_model.id}'
                        },
                        'Remover Categoria': {
                            'callback_data': f'remove_account:{account_model.id}'
                        },
                        'Voltar': {'callback_data': 'return_to_main_menu'},
                    },
                    row_width=1,
                ),
            )

    @bot.callback_query_handler(func=lambda c: 'edit_account:' in c.data)
    def edit_account(callback_query):
        account_id = int(callback_query.data.split(':')[-1])
        bot.send_message(
            callback_query.message.chat.id, 'Digite o Login da conta'
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_account_login(m, account_id),
        )

    def on_edit_account_login(message, account_id):
        bot.send_message(message.chat.id, 'Digite a Senha da conta')
        bot.register_next_step_handler(
            message,
            lambda m: on_edit_account_password(m, account_id, message.text),
        )

    def on_edit_account_password(message, account_id, login):
        with Session() as session:
            account_model = session.get(Account, account_id)
            account_model.login = login
            account_model.password = message.text
            session.commit()
            bot.send_message(message.chat.id, 'Conta Alterada!')
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'remove_account')
    def remove_account(callback_query):
        with Session() as session:
            reply_markup = {}
            for account_model in session.scalars(select(Account)).all():
                reply_markup[account_model.login] = {
                    'callback_data': f'remove_account:{account_model.id}'
                }
            reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma Conta',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(func=lambda c: 'remove_account:' in c.data)
    def remove_account_action(callback_query):
        account_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            account_model = session.get(Account, account_id)
            session.delete(account_model)
            session.commit()
            bot.send_message(callback_query.message.chat.id, 'Conta Removida!')
            start(callback_query.message)
