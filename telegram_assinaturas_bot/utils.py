from datetime import datetime

from pytz import timezone

from telegram_assinaturas_bot import repository
from telegram_assinaturas_bot.callbacks_datas import actions_factory, categories_factory


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_signature_text(signature, with_due_date=False):
    plan = repository.get_plan(signature.plan_id)
    message = get_plan_text(plan)
    if with_due_date:
        message += f'\n\nVencimento do plano: {signature.due_date:%d/%m/%Y}'
    return message


def get_plan_text(plan):
    return f'{plan.name} - {plan.days} Dias - R${plan.value:.2f}'.replace('.', ',')


def create_actions_callback_data(**kwargs):
    arguments = [
        'action',
        'p',
        's',
        'a',
        'u',
        'c',
        'e',
    ]
    factory_arguments = {}
    for argument in arguments:
        factory_arguments[argument] = kwargs.get(argument, '')
    return actions_factory.new(**factory_arguments)


def create_categories_callback_data(**kwargs):
    arguments = [
        'label',
        'action',
        'argument',
        'category_id',
    ]
    factory_arguments = {}
    for argument in arguments:
        factory_arguments[argument] = kwargs.get(argument, '')
    return categories_factory.new(**factory_arguments)
