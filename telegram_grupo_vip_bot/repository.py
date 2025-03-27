from datetime import datetime

from pytz import timezone
from sqlalchemy import select

from telegram_grupo_vip_bot import models
from telegram_grupo_vip_bot.database import Session


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_users():
    with Session() as session:
        return session.scalars(select(models.User)).all()


def search_users(search):
    with Session() as session:
        query = select(models.User).where(
            models.User.username.ilike(f'%{search}%')
        )
        return session.scalars(query).all()


def create_user(username):
    with Session() as session:
        user = models.User(username=username)
        session.add(user)
        session.commit()


def create_update_user(username, name, chat_id):
    with Session() as session:
        query = select(models.User).where(
            models.User.username == username
        )
        user_model = session.scalars(query).first()
        if user_model is None:
            user_model = models.User(
                username=username,
                name=name,
                chat_id=chat_id,
            )
            session.add(user_model)
            session.commit()
        else:
            user_model.chat_id = chat_id
            user_model.name = name
            session.commit()


def get_user_by_username(username):
    with Session() as session:
        query = select(models.User).where(
            models.User.username == username
        )
        return session.scalars(query).first()


def edit_user_cpf_cnpj(user_id, cpf_cnpj):
    with Session() as session:
        user = session.get(models.User, user_id)
        user.cpf_cnpj = cpf_cnpj
        session.commit()


def edit_user_email(user_id, email):
    with Session() as session:
        user = session.get(models.User, user_id)
        user.email = email
        session.commit()


def delete_user_by_username(username):
    with Session() as session:
        query = select(models.User).where(
            models.User.username == username
        )
        user = session.scalars(query).first()
        session.delete(user)
        session.commit()


def get_active_signatures():
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.due_date >= get_today_date(),
        )
        return session.scalars(query).all()


def get_active_user_signatures(user_id):
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.user_id == user_id,
            models.Signature.due_date >= get_today_date(),
        )
        return session.scalars(query).all()


def get_active_plan_user_signatures(user_id, plan_id):
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.user_id == user_id,
            models.Signature.plan_id == plan_id,
            models.Signature.due_date >= get_today_date(),
        )
        return session.scalars(query).all()


def get_active_plan_signatures(plan_id):
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.plan_id == plan_id,
            models.Signature.due_date >= get_today_date(),
        )
        return session.scalars(query).all()


def get_signature(signature_id):
    with Session() as session:
        return session.get(models.Signature, signature_id)


def edit_signature_account(signature_id, account_id):
    with Session() as session:
        signature = session.get(models.Signature, signature_id)
        signature.account_id = account_id
        session.commit()


def create_signature(
    user_id, plan_id, due_date, payment_id=None
):
    with Session() as session:
        signature = models.Signature(
            user_id=user_id,
            plan_id=plan_id,
            due_date=due_date,
            payment_id=payment_id,
        )
        session.add(signature)
        session.commit()


def delete_signature(signature_id):
    with Session() as session:
        signature = session.get(models.Signature, signature_id)
        session.delete(signature)
        session.commit()


def get_plans():
    with Session() as session:
        return session.scalars(select(models.Plan)).all()


def get_plan(plan_id):
    with Session() as session:
        return session.get(models.Plan, plan_id)


def create_plan(value, name, days, message):
    with Session() as session:
        plan = models.Plan(
            value=value,
            name=name,
            days=days,
            message=message,
        )
        session.add(plan)
        session.commit()


def edit_plan_message(plan_id, message):
    with Session() as session:
        plan = session.get(models.Plan, plan_id)
        plan.message = message
        session.commit()


def delete_plan(plan_id):
    with Session() as session:
        plan = session.get(models.Plan, plan_id)
        session.delete(plan)
        session.commit()


def edit_plan_name(plan_id, name):
    with Session() as session:
        plan_model = session.get(models.Plan, plan_id)
        plan_model.name = name
        session.commit()


def edit_plan_value(plan_id, value):
    with Session() as session:
        plan_model = session.get(models.Plan, plan_id)
        plan_model.value = value
        session.commit()


def get_payment(payment_id):
    with Session() as session:
        query = select(models.Payment).where(
            models.Payment.payment_id == payment_id,
        )
        return session.scalars(query).first()


def get_payment_plan(payment_id):
    with Session() as session:
        return session.get(models.Payment, payment_id).plan


def create_payment(chat_id, user_id, payment_id, plan):
    with Session() as session:
        payment = models.Payment(
            chat_id=chat_id,
            user_id=user_id,
            payment_id=payment_id,
            plan=plan,
        )
        session.add(payment)
        session.commit()


def delete_payment(payment_id):
    with Session() as session:
        payment = session.get(models.Payment, payment_id)
        session.delete(payment)
        session.commit()


def get_subscribers():
    with Session() as session:
        query = (
            select(models.User)
            .join(models.Signature)
            .where(
                models.Signature.due_date >= get_today_date(),
            )
        )
        return session.scalars(query).all()
