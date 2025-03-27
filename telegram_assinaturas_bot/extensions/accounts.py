from telebot.apihelper import ApiTelegramException
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import actions_factory
from telegram_assinaturas_bot.consts import MAX_OPTIONS_LENGTH


def init_bot(bot, bot_token, start):
    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_plan_accounts')
    )
    def show_plan_accounts(callback_query):
        data = actions_factory.parse(callback_query.data)
        reply_markup = {}
        for account in repository.get_plan_accounts(int(data['p'])):
            active_signatures = repository.get_active_account_signatures(account.id)
            label = f'Membros: {len(active_signatures)} '
            label += (
                account.message
                if len(account.message) < MAX_OPTIONS_LENGTH
                else account.message[: MAX_OPTIONS_LENGTH - 10] + '...'
            )
            reply_markup[label] = {
                'callback_data': utils.create_actions_callback_data(
                    action=data['argument'],
                    p=data['plan_id'],
                    s=data['signature_id'],
                    a=account.id,
                )
            }
        reply_markup['Voltar'] = {
            'callback_data': utils.create_categories_callback_data(
                label='Contas', action='show_plan_accounts'
            )
        }
        bot.send_message(
            callback_query.message.chat.id,
            'Contas',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='add_user_plan_menu')
    )
    def add_user_plan_menu(callback_query):
        data = actions_factory.parse(callback_query.data)
        reply_markup = {}
        for account in repository.get_plan_accounts(int(data['p'])):
            active_signatures = repository.get_active_account_signatures(account.id)
            label = f'Membros: {len(active_signatures)} '
            label += (
                account.message
                if len(account.message) < MAX_OPTIONS_LENGTH
                else account.message[: MAX_OPTIONS_LENGTH - 10] + '...'
            )
            reply_markup[label] = {
                'callback_data': utils.create_actions_callback_data(
                    action='add_user_plan',
                    u=data['u'],
                    a=account.id,
                )
            }
        reply_markup['Voltar'] = {
            'callback_data': utils.create_categories_callback_data(
                label='Contas',
                action='show_plan_accounts',
            )
        }
        bot.send_message(
            callback_query.message.chat.id,
            'Contas',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='show_account'))
    def show_account(callback_query):
        data = actions_factory.parse(callback_query.data)
        account = repository.get_account(int(data['a']))
        bot.send_message(
            callback_query.message.chat.id,
            account.message,
            reply_markup=quick_markup(
                {
                    'Editar Mensagem': {
                        'callback_data': utils.create_actions_callback_data(
                            action='edit_account_message',
                            a=account.id,
                        )
                    },
                    'Remover Conta': {
                        'callback_data': utils.create_actions_callback_data(
                            action='delete_account',
                            a=account.id,
                        )
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(config=actions_factory.filter(action='create_account'))
    def create_account(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id, 'Digite a mensagem para a conta'
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_account_message(m, int(data['p'])),
        )

    def on_account_message(message, plan_id):
        repository.create_account(bot_token, plan_id, message.text)
        bot.send_message(message.chat.id, 'Conta Adicionada!')
        start(message)

    @bot.callback_query_handler(
        config=actions_factory.filter(action='edit_account_message')
    )
    def edit_account_message(callback_query):
        data = actions_factory.parse(callback_query.data)
        account = repository.get_account(int(data['a']))
        bot.send_message(callback_query.message.chat.id, 'Mensagem Atual:')
        bot.send_message(callback_query.message.chat.id, account.message)
        bot.send_message(
            callback_query.message.chat.id,
            'Digite a nova mensagem da conta',
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_edit_account_message(m, int(data['a'])),
        )

    def on_edit_account_message(message, account_id):
        repository.edit_account_message(account_id, message.text)
        for signature in repository.get_account_signatures(account_id):
            if signature.user.chat_id:
                try:
                    bot.send_message(
                        signature.user.chat_id,
                        (
                            f'🚨 Atenção, {signature.user.username} 🚨\n'
                            f'🔒 A senha do {signature.plan.name} foi alterada.'
                            '\n👉 Acesse agora em "Minhas assinaturas" 💻'
                        ),
                    )
                except ApiTelegramException:
                    continue
        bot.send_message(message.chat.id, 'Conta Alterada!')
        start(message)

    @bot.callback_query_handler(config=actions_factory.filter(action='delete_account'))
    def delete_account(callback_query):
        data = actions_factory.parse(callback_query.data)
        repository.delete_account(int(data['a']))
        bot.send_message(callback_query.message.chat.id, 'Conta Removida!')
        start(callback_query.message)
