from datetime import timedelta

from sqlalchemy import select

from main import bot, start
from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.extensions.signatures import mercado_pago_sdk
from telegram_assinaturas_bot.models import Account, Payment, Plan, Signature
from telegram_assinaturas_bot.utils import get_today_date

if __name__ == '__main__':
    with Session() as session:
        while True:
            for payment in session.scalars(select(Payment)).all():
                response = mercado_pago_sdk.payment().get(
                    int(payment.payment_id)
                )['response']
                if response['status'] == 'approved':
                    message = bot.send_message(
                        int(payment.chat_id),
                        'Pagamento confirmado, confira seu acesso em "Minhas Assinaturas"',
                    )
                    query = select(Plan).where(
                        Plan.value == response['transaction_amount']
                    )
                    plan_model = session.scalars(query).first()
                    query = select(Account).where(
                        Account.category_id == plan_model.category_id
                    )
                    account = None
                    for account_model in session.scalars(query).all():
                        if account_model.users_number > len(
                            account_model.users
                        ):
                            account = account_model
                    if account is None:
                        if plan_model.accounts:
                            signatures_number = plan_model.accounts[0].signatures_number
                        else:
                            signatures_number = 1
                        account_model = Account(
                            plan_id=plan_model.id,
                            message='Conta Inativa',
                            signatures_number=signatures_number,
                        )
                        session.add(account_model)
                        session.commit()
                        session.flush()
                        account = account_model
                        for admin in config['ADMINS']:
                            bot.send_message(
                                admin,
                                f'Nova conta adicionada! - {plan_model.name}',
                            )
                    signature_model = Signature(
                        user=payment.user,
                        payment_id=payment.payment_id,
                        plan=plan_model,
                        due_date=get_today_date()
                        + timedelta(days=plan_model.days),
                        account=account,
                    )
                    session.add(signature_model)
                    session.delete(payment)
                    session.commit()
                    start(message)
