from datetime import datetime

from pytz import timezone
from sqlalchemy import select

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Category


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_categories_reply_markup(action, *args):
    reply_markup = {}
    with Session() as session:
        for category_model in session.scalars(select(Category)).all():
            if category_model.parent_category_name == 'Nenhuma':
                reply_markup['🗂 ' + category_model.name] = {
                    'callback_data': f'show_categories:{category_model.id}:'
                    + ':'.join([action, *args])
                }
        reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        return reply_markup
