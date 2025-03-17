from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import (
    actions_factory,
)
from telegram_assinaturas_bot.consts import MAX_OPTIONS_LENGTH


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_subscribers')
    )
    def show_subscribers(callback_query):
        data = actions_factory.parse(callback_query.data)
        reply_markup = {}
        accounts = repository.get_plan_accounts(int(data['p']))
        actives = len(repository.get_active_plan_signatures(int(data['p'])))
        for account in accounts:
            label = (
                account.message
                if len(account.message) < MAX_OPTIONS_LENGTH
                else account.message[: MAX_OPTIONS_LENGTH - 10] + '...'
            )
            reply_markup[label] = utils.create_actions_callback_data(
                action='show_account_subscribers',
                a=account.id,
            )
        reply_markup['Voltar'] = utils.create_categories_callback_data(
            label='Assinantes',
            action='show_subscribers',
        )
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_account_subscribers')
    )
    def show_account_subscribers(callback_query):
        data = actions_factory.parse(callback_query.data)
        actives = 0
        users = ''
        for signature in repository.get_active_account_signatures(int(data['a'])):
            actives += 1
            users += f'@{signature.user.username}\n'
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}\n\n{users}',
            reply_markup=quick_markup(
                {
                    'Voltar': utils.create_categories_callback_data(
                        label='Planos',
                        action='show_subscribers',
                    ),
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'show_bots_subscribers')
    def show_bots_subscribers(callback_query):
        before_due_date_bots = repository.get_before_due_date_bots()
        after_due_date_bots = repository.get_after_due_date_bots()
        users = ''
        actives = 0
        for before_due_date_bot in before_due_date_bots:
            actives += 1
            if before_due_date_bot.username not in users:
                users += f'@{before_due_date_bot.username}\n'
        bot.send_message(
            callback_query.message.chat.id,
            (
                f'Ativos: {len(before_due_date_bots)}\n'
                f'Inativos: {len(after_due_date_bots)}\n\n{users}',
            ),
            reply_markup=quick_markup(
                {
                    'Voltar': {'callback_data': 'show_main_menu'}
                },
                row_width=1,
            ),
        )
