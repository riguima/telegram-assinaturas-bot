from datetime import datetime

from pytz import timezone

from telegram_grupo_vip_bot.callbacks_datas import actions_factory


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_signature_text(signature, plan, with_due_date=False):
    message = get_plan_text(plan)
    if with_due_date:
        message += f'\n\nVencimento do plano: {signature.due_date:%d/%m/%Y}'
    return message


def get_plan_text(plan):
    intervals = {
        'day': 'Dias',
        'month': 'Meses',
        'year': 'Anos',
    }
    if plan['interval'] != 'year':
        return (
            f'{plan["interval_count"]} {intervals[plan["interval"]]} - '
            f'R${plan["amount"]:.2f}'.replace('.', ',')
        )
    else:
        return f'Vitalício - R${plan["amount"]:.2f}'.replace('.', ',')


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
