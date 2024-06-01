from datetime import timedelta

from sqlalchemy import select

from main import bot, start
from telegram_assinaturas_bot.config import config
from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.extensions.signatures import mercado_pago_sdk
from telegram_assinaturas_bot.models import Payment, Plan, Signature
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
                        f'Pagamento confirmado, Aguardando liberação...\n\nNº Transação: {payment.payment_id}',
                    )
                    query = select(Plan).where(
                        Plan.value == response['transaction_amount']
                    )
                    plan_model = session.scalars(query).first()
                    signature_model = Signature(
                        user=payment.user,
                        payment_id=payment.payment_id,
                        plan=plan_model,
                        due_date=get_today_date()
                        + timedelta(days=plan_model.days),
                    )
                    session.add(signature_model)
                    session.delete(payment)
                    session.commit()
                    for admin in config['ADMINS']:
                        bot.send_message(
                            admin,
                            f'Nova Assinatura: {payment.user.username} - {plan_model.name}',
                        )
                    start(message)
