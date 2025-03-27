from importlib import import_module

from telebot.custom_filters import AdvancedCustomFilter
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.config import config


class CallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call, config):
        return config.check(query=call)


def init_bot(bot, bot_token):
    @bot.message_handler(commands=['start', 'help', 'menu'])
    def start(message):
        user_bot = repository.get_bot_by_token(bot_token)
        if user_bot.due_date and user_bot.due_date < utils.get_today_date():
            return
        if message.chat.username:
            is_admin = repository.is_admin(message.chat.username)
            if not is_admin and bot_token == config['BOT_TOKEN']:
                return
            repository.create_update_user(
                bot_token=bot_token,
                username=message.chat.username,
                name=message.chat.first_name,
                chat_id=str(message.chat.id),
            )
            bot.send_message(
                message.chat.id,
                repository.get_setting(
                    bot_token,
                    'Mensagem Menu',
                    default='Altere a mensagem do menu para ser mostrada aqui',
                ),
                reply_markup=quick_markup(
                    get_menu_options(message, is_admin),
                    row_width=1
                ),
            )
        else:
            bot.send_message(
                message.chat.id,
                'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
            )

    def get_menu_options(message, is_admin):
        options = {}
        if bot_token != config['BOT_TOKEN']:
            options['Minhas Assinaturas'] = {
                'callback_data': utils.create_actions_callback_data(
                    action='show_signature', u=message.chat.username
                )
            }
        if is_admin:
            default_options = {
                'Enviar Mensagem': {'callback_data': 'send_message'},
                'Editar Mensagem do Menu': {'callback_data': 'edit_menu_message'},
                'Adicionar Membro': {'callback_data': 'create_user'},
                'Membros': {'callback_data': 'show_users'},
            }
            if bot_token == config['BOT_TOKEN']:
                options['Configurar Bot'] = {
                    'callback_data': 'configure_bot',
                }
                user_bot = repository.get_bot_by_token(bot_token)
                if user_bot.username == message.chat.username:
                    options['Assinantes'] = {'callback_data': 'show_bots_subscribers'}
                    options.update(default_options)
            else:
                options['Gateway de Pagamento'] = {
                    'callback_data': 'change_payment_gateway'
                }
                options['Adicionar Conta'] = {
                    'callback_data': utils.create_categories_callback_data(
                        label='Selecione um Plano',
                        action='create_account',
                        argument='',
                    )
                }
                options['Contas'] = {
                    'callback_data': utils.create_categories_callback_data(
                        label='Contas',
                        action='show_plan_accounts',
                        argument='show_account',
                    )
                }
                options['Adicionar Categoria'] = {'callback_data': 'create_category'}
                options['Categorias'] = {'callback_data': 'show_categories'}
                options['Assinantes'] = {
                    'callback_data': utils.create_categories_callback_data(
                        label='subscribers',
                        action='show_subscribers',
                        argument='',
                    )
                }
                options['Adicionar Plano'] = {'callback_data': 'create_plan'}
                options['Planos'] = {
                    'callback_data': utils.create_categories_callback_data(
                        label='Planos',
                        action='show_plan',
                        argument='',
                    )
                }
                options.update(default_options)
        return options

    @bot.callback_query_handler(func=lambda c: c.data == 'edit_menu_message')
    def edit_menu_message(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Envie a mensagem que vai ficar no menu\n\nTags: {nome}',
        )
        bot.register_next_step_handler(callback_query.message, on_menu_message)

    def on_menu_message(message):
        repository.set_setting(bot_token, 'Mensagem Menu', message.text)
        bot.send_message(message.chat.id, 'Mensagem Editada!')
        start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_main_menu')
    def show_main_menu(callback_query):
        start(callback_query.message)

    def load_extensions():
        for extension in config['EXTENSIONS']:
            extension_module = import_module(extension)
            extension_module.init_bot(bot, bot_token, start)

    load_extensions()
    bot.add_custom_filter(CallbackFilter())
    bot.remove_webhook()
    bot.set_webhook(url=f'{config["WEBHOOK_HOST"]}/{bot_token}')
