from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Account
from telegram_assinaturas_bot.utils import get_categories_reply_markup


def init_bot(bot, start):
    @bot.callback_query_handler(
        func=lambda c: 'show_accounts_of_plan:' in c.data
    )
    def show_accounts_of_plan(callback_query):
        plan_id, action = callback_query.data.split(':')[1:3]
        args = callback_query.data.split(':')[3:]
        with Session() as session:
            reply_markup = {}
            query = select(Account).where(Account.plan_id == int(plan_id))
            for account_model in session.scalars(query).all():
                label = f'Membros: {len(account_model.signatures)} '
                label += (
                    account_model.message
                    if len(account_model.message) < 50
                    else account_model.message[:40] + '...'
                )
                reply_markup[label] = {
                    'callback_data': ':'.join([action, *args, str(account_model.id)]),
                }
            reply_markup['Voltar'] = {
                'callback_data': 'return_to_categories_menu:show_accounts_of_plan'
            }
            bot.send_message(
                callback_query.message.chat.id,
                'Contas',
                reply_markup=quick_markup(reply_markup, row_width=1),
            )

    @bot.callback_query_handler(func=lambda c: c.data == 'add_account')
    def add_account(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Selecione um plano',
            reply_markup=quick_markup(
                get_categories_reply_markup('choose_account_plan'), row_width=1
            ),
        )

    @bot.callback_query_handler(
        func=lambda c: 'choose_account_plan:' in c.data
    )
    def choose_account_plan(callback_query):
        plan_id = int(callback_query.data.split(':')[-1])
        bot.send_message(
            callback_query.message.chat.id, 'Digite a mensagem para a conta'
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_account_message(m, plan_id)
        )

    def on_account_message(message, plan_id):
        with Session() as session:
            account_model = Account(
                plan_id=plan_id,
                message=message.text,
            )
            session.add(account_model)
            session.commit()
            bot.send_message(message.chat.id, 'Conta Adicionada!')
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_accounts')
    def show_accounts(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Contas',
            reply_markup=quick_markup(
                get_categories_reply_markup(
                    'show_accounts_of_plan', 'show_account'
                ),
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: 'show_account:' in c.data)
    def show_account(callback_query):
        account_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            account_model = session.get(Account, account_id)
            bot.send_message(
                callback_query.message.chat.id,
                account_model.message,
                reply_markup=quick_markup(
                    {
                        'Editar Mensagem': {
                            'callback_data': f'edit_account_message:{account_model.id}'
                        },
                        'Remover Conta': {
                            'callback_data': f'remove_account:{account_model.id}'
                        },
                        'Voltar': {'callback_data': 'return_to_main_menu'},
                    },
                    row_width=1,
                ),
            )

    @bot.callback_query_handler(
        func=lambda c: 'edit_account_message:' in c.data
    )
    def edit_account_message(callback_query):
        account_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            account_model = session.get(Account, account_id)
            bot.send_message(callback_query.message.chat.id, 'Mensagem Atual:')
            bot.send_message(
                callback_query.message.chat.id, account_model.message
            )
            bot.send_message(
                callback_query.message.chat.id,
                'Digite a nova mensagem da conta',
            )
            bot.register_next_step_handler(
                callback_query.message,
                lambda m: on_edit_account_message(m, account_id),
            )

    def on_edit_account_message(message, account_id):
        with Session() as session:
            account_model = session.get(Account, account_id)
            account_model.message = message.text
            account_model.password = message.text
            session.commit()
            bot.send_message(message.chat.id, 'Conta Alterada!')
            start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'remove_account')
    def remove_account(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Contas',
            reply_markup=quick_markup(
                get_categories_reply_markup(
                    'show_accounts_of_plan', 'remove_account'
                ),
                row_width=1,
            ),
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
