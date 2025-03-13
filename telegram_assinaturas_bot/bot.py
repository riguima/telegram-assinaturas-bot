from importlib import import_module

from telebot.custom_filters import AdvancedCustomFilter
from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.config import config


class CallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call, config):
        return config.check(query=call)


def init_bot(bot, bot_username):
    @bot.message_handler(commands=['start', 'help', 'menu'])
    def start(message):
        if message.chat.username:
            repository.create_update_user(
                bot_username, message.chat.username, str(message.chat.id)
            )
            bot.send_message(
                message.chat.id,
                repository.get_setting(
                    bot_username,
                    'Mensagem Menu',
                    default='Altere a mensagem do menu para ser mostrada aqui',
                ),
                reply_markup=quick_markup(get_menu_options(message), row_width=1),
            )
        else:
            bot.send_message(
                message.chat.id,
                'Adicione um arroba para sua conta do Telegram para utilizar esse bot',
            )

    def get_menu_options(message):
        options = {
            'Minhas Assinaturas': {
                'callback_data': utils.create_actions_callback_data(
                    action='show_signature', u=message.chat.username
                )
            },
        }
        if message.chat.id in config['ADMINS']:
            options['Gateway de Pagamento'] = {
                'callback_data': 'change_payment_gateway'
            }
            options['Enviar Mensagem'] = {'callback_data': 'send_message'}
            options['Editar Mensagem do Menu'] = {'callback_data': 'edit_menu_message'}
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
            options['Adicionar Membro'] = {'callback_data': 'create_user'}
            options['Membros'] = {'callback_data': 'show_users'}
        return options

    @bot.callback_query_handler(func=lambda c: c.data == 'edit_menu_message')
    def edit_menu_message(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Envie a mensagem que vai ficar no menu\n\nTags: {nome}',
        )
        bot.register_next_step_handler(callback_query.message, on_menu_message)

    def on_menu_message(message):
        repository.set_setting(bot_username, 'Mensagem Menu', message.text)
        bot.send_message(message.chat.id, 'Mensagem Editada!')
        start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_main_menu')
    def show_main_menu(callback_query):
        start(callback_query.message)

    def load_extensions(bot):
        for extension in config['EXTENSIONS']:
            extension_module = import_module(extension)
            extension_module.init_bot(bot, bot_username, start)

    load_extensions(bot, bot_username)
    bot.add_custom_filter(CallbackFilter())
    bot.remove_webhook()
    bot.set_webhook(url=f'{config["WEBHOOK_HOST"]}/update/{bot_username}')
