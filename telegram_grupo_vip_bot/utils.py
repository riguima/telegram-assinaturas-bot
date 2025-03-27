from datetime import datetime

from pytz import timezone

from telegram_grupo_vip_bot import repository
from telegram_grupo_vip_bot.callbacks_datas import actions_factory, plans_factory


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


def create_plans_callback_data(**kwargs):
    arguments = [
        'action',
        'argument',
    ]
    factory_arguments = {}
    for argument in arguments:
        factory_arguments[argument] = kwargs.get(argument, '')
    return plans_factory.new(**factory_arguments)


def create_actions_callback_data(**kwargs):
    arguments = [
        'action',
        'p',
        's',
        'u',
        'e',
    ]
    factory_arguments = {}
    for argument in arguments:
        factory_arguments[argument] = kwargs.get(argument, '')
    return actions_factory.new(**factory_arguments)
