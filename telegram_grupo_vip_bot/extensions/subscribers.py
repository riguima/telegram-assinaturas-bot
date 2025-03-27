from telebot.util import quick_markup

from telegram_grupo_vip_bot import repository, utils
from telegram_grupo_vip_bot.callbacks_datas import (
    actions_factory,
)


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'show_subscribers')
    def show_subscribers(callback_query):
        reply_markup = {}
        actives = len(repository.get_active_signatures())
        for plan in repository.get_plans():
            reply_markup[utils.get_plan_text(plan)] = {
                'callback_data': utils.create_actions_callback_data(
                    action='show_plan_subscribers',
                    p=plan.id,
                ),
            }
        reply_markup['Voltar'] = {
            'callback_data': utils.create_plans_callback_data(
                action='show_main_menu',
            )
        }
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        config=actions_factory.filter(action='show_plan_subscribers')
    )
    def show_plan_subscribers(callback_query):
        data = actions_factory.parse(callback_query.data)
        actives = 0
        users = ''
        for signature in repository.get_active_plan_signatures(int(data['p'])):
            actives += 1
            users += f'@{signature.user.username}\n'
        bot.send_message(
            callback_query.message.chat.id,
            f'Ativos: {actives}\n\n{users}',
            reply_markup=quick_markup(
                {
                    'Voltar': {
                        'callback_data': utils.create_plans_callback_data(
                            action='show_subscribers',
                        ),
                    }
                },
                row_width=1,
            ),
        )
