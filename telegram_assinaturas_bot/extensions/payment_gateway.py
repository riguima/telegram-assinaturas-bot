import os
from pathlib import Path

from telebot.util import quick_markup

from telegram_assinaturas_bot import repository, utils
from telegram_assinaturas_bot.callbacks_datas import actions_factory
from telegram_assinaturas_bot.config import config


def init_bot(bot, bot_username, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'change_payment_gateway')
    def change_payment_gateway(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(
                {
                    'Mercado Pago': {
                        'callback_data': utils.create_actions_callback_data(
                            action='configure_gateway',
                            e='mercado-pago',
                        ),
                    },
                    'Asaas': {
                        'callback_data': utils.create_actions_callback_data(
                            action='configure_gateway', e='asaas'
                        ),
                    },
                    'Voltar': {'callback_data': 'show_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='configure_gateway')
    )
    def configure_gateway(callback_query):
        data = actions_factory.parse(callback_query.data)
        bot.send_message(
            callback_query.message.chat.id,
            'Siga o passo a passo abaixo para configuração do webhook',
        )
        send_step_by_step_messages(callback_query.message, data['e'])
        images_path = Path('assets') / data['e']
        for filename in sorted(
            os.listdir(images_path), key=lambda p: int(p.split('.')[0])
        ):
            bot.send_photo(
                callback_query.message.chat.id, open(images_path / filename, 'rb')
            )
        bot.send_message(
            callback_query.message.chat.id,
            (
                'Copie essa url para o campo de url do webhook: '
                f'{config["WEBHOOK_HOST"]}/webhook/{data["e"]}'
            ),
        )
        bot.send_message(
            callback_query.message.chat.id,
            'Digite o Token/Chave de API para concluir a configuração',
        )
        bot.register_next_step_handler(
            callback_query.message, lambda m: on_access_token(m, data['e'])
        )

    def send_step_by_step_messages(message, gateway):
        if gateway == 'mercado_pago':
            bot.send_message(
                message.chat.id,
                (
                    'Acesse [Suas Integrações](https://www.mercadopago.com.br'
                    '/developers/panel/app) e crie um novo app'
                ),
                parse_mode='MarkdownV2',
            )
            bot.send_message(
                message.chat.id,
                (
                    'Acesse Webhooks no painel a esquerda, '
                    'depois clique em Configurar notificações, '
                    'configure como na imagem abaixo:'
                ),
            )
        else:
            bot.send_message(
                message.chat.id,
                (
                    'Dentro do Asaas, vai no menu no canto superior direito e selecione'
                    ' "Integrações", adicione um webhook e deixe como no exemplo '
                    'abaixo:'
                ),
            )

    def on_access_token(message, gateway):
        repository.set_setting(bot_username, 'Gateway', gateway)
        repository.set_setting(bot_username, 'Access Token', message.text)
        bot.send_message(message.chat.id, 'Gateway Configurado!')
        start(message)
