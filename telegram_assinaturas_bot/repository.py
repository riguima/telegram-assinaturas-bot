from datetime import datetime

from pytz import timezone
from sqlalchemy import select

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import (
    Account,
    Category,
    Payment,
    Plan,
    Setting,
    Signature,
    User,
)


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_users():
    with Session() as session:
        return session.scalars(select(User)).all()


def search_users(search):
    with Session() as session:
        query = select(User).where(User.username.ilike(f'%{search}%'))
        return session.scalars(query).all()


def create_user(username):
    with Session() as session:
        user = User(username=username)
        session.add(user)
        session.commit()


def create_update_user(username, chat_id):
    with Session() as session:
        query = select(User).where(User.username == username)
        user_model = session.scalars(query).first()
        if user_model is None:
            user_model = User(
                username=username,
                chat_id=chat_id,
            )
            session.add(user_model)
            session.commit()
        elif user_model.chat_id is None:
            user_model.chat_id = chat_id
            session.commit()


def get_user_by_username(username):
    with Session() as session:
        query = select(User).where(User.username == username)
        return session.scalars(query).first()


def delete_user_by_username(username):
    with Session() as session:
        query = select(User).where(User.username == username)
        user = session.scalars(query).first()
        session.delete(user)
        session.commit()


def get_active_signatures(user_id):
    with Session() as session:
        query = (
            select(Signature)
            .where(Signature.user_id == user_id)
            .where(Signature.due_date >= get_today_date())
        )
        return session.scalars(query).all()


def get_active_plan_signatures(user_id, plan_id):
    with Session() as session:
        query = (
            select(Signature)
            .where(Signature.user_id == user_id)
            .where(Signature.plan_id == plan_id)
            .where(Signature.due_date >= get_today_date())
        )
        return session.scalars(query).all()


def get_active_account_signatures(account_id):
    with Session() as session:
        query = (
            select(Signature)
            .where(Signature.account_id == account_id)
            .where(Signature.due_date >= get_today_date())
        )
        return session.scalars(query).all()


def get_signature(signature_id):
    with Session() as session:
        return session.get(Signature, signature_id)


def get_account_signatures(account_id):
    with Session() as session:
        query = select(Signature).where(Signature.account_id == account_id)
        return session.scalars(query).all()


def edit_signature_account(signature_id, account_id):
    with Session() as session:
        signature = session.get(Signature, signature_id)
        account = session.get(Account, account_id)
        signature.account_id = account.id
        session.commit()


def create_signature(user_id, plan_id, account_id, due_date):
    with Session() as session:
        signature = Signature(
            user_id=user_id,
            plan_id=plan_id,
            account_id=account_id,
            due_date=due_date,
        )
        session.add(signature)
        session.commit()


def delete_signature(signature_id):
    with Session() as session:
        signature = session.get(Signature, signature_id)
        session.delete(signature)
        session.commit()


def get_accounts():
    with Session() as session:
        return session.scalars(select(Account)).all()


def get_plan_accounts(plan_id):
    with Session() as session:
        query = select(Account).where(Account.plan_id == int(plan_id))
        return session.scalars(query).all()


def get_plan_from_account(account_id):
    with Session() as session:
        account = session.get(Account, account_id)
        return account.plan


def get_account(account_id):
    with Session() as session:
        return session.get(Account, account_id)


def create_account(plan_id, message):
    with Session() as session:
        account_model = Account(
            plan_id=plan_id,
            message=message,
        )
        session.add(account_model)
        session.commit()


def edit_account_message(account_id, message):
    with Session() as session:
        account = session.get(Account, account_id)
        account.message = message
        session.commit()


def delete_account(account_id):
    with Session() as session:
        account = session.get(Account, account_id)
        session.delete(account)
        session.commit()


def get_categories():
    with Session() as session:
        return session.scalars(select(Category)).all()


def get_main_categories():
    with Session() as session:
        query = select(Category).where(Category.parent_category_name == 'Nenhuma')
        return session.scalars(query).all()


def get_category(category_id):
    with Session() as session:
        return session.get(Category, category_id)


def create_category(parent_category_name, name):
    with Session() as session:
        category_model = Category(
            parent_category_name=parent_category_name,
            name=name,
        )
        session.add(category_model)
        session.commit()


def get_subcategories(parent_category_id):
    with Session() as session:
        category = session.get(Category, parent_category_id)
        query = select(Category).where(Category.parent_category_name == category.name)
        return session.scalars(query).all()


def edit_category_name(category_id, name):
    with Session() as session:
        category = session.get(Category, category_id)
        category.name = name
        session.commit()


def edit_parent_category(category_id, parent_category_id):
    with Session() as session:
        category = session.get(Category, category_id)
        parent_category = session.get(Category, parent_category_id)
        if parent_category:
            category.parent_category_name = parent_category.name
        else:
            category.parent_category_name = 'Nenhuma'
        session.commit()


def get_categories_except(category_id):
    with Session() as session:
        category = session.get(Category, category_id)
        query = (
            select(Category)
            .where(Category.name != category.parent_category_name)
            .where(Category.name != category.name)
        )
        return session.scalars(query).all()


def delete_category(category_id):
    with Session() as session:
        category = session.get(Category, category_id)
        query = select(Category).where(Category.parent_category_name == category.name)
        for child_category_model in session.scalars(query).all():
            child_category_model.parent_category_name = 'Nenhuma'
        session.delete(category)
        session.commit()


def get_setting(name, default=''):
    with Session() as session:
        query = select(Setting).where(Setting.name == name)
        setting = session.scalars(query).first()
        return default if setting is None else setting.value


def set_setting(username, name, value):
    with Session() as session:
        query = (
            select(Setting)
            .where(Setting.username == username)
            .where(Setting.name == name)
        )
        setting = session.scalars(query).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(
                name=name,
                value=value,
            )
            session.add(setting)
        session.commit()


def get_plan(plan_id):
    with Session() as session:
        return session.get(Plan, plan_id)


def get_plans_with_category(category_id):
    with Session() as session:
        query = select(Plan).where(Plan.category_id == category_id)
        return session.scalars(query).all()


def create_plan(value, name, days, category_id):
    with Session() as session:
        plan = Plan(
            value=value,
            name=name,
            days=days,
            category_id=category_id,
        )
        session.add(plan)
        session.commit()


def edit_plan_message(plan_id, message):
    with Session() as session:
        plan = session.get(Plan, plan_id)
        plan.message = message
        session.commit()


def delete_plan(plan_id):
    with Session() as session:
        plan = session.get(Plan, plan_id)
        session.delete(plan)
        session.commit()


def edit_plan_name(plan_id, name):
    with Session() as session:
        plan_model = session.get(Plan, plan_id)
        plan_model.name = name
        session.commit()


def edit_plan_value(plan_id, value):
    with Session() as session:
        plan_model = session.get(Plan, plan_id)
        plan_model.value = value
        session.commit()


def create_payment(chat_id, user_id, payment_id):
    with Session() as session:
        payment = Payment(
            chat_id=chat_id,
            user_id=user_id,
            payment_id=payment_id,
        )
        session.add(payment)
        session.commit()


def get_subscribers():
    with Session() as session:
        query = (
            select(User).join(Signature).where(Signature.due_date >= get_today_date())
        )
        return session.scalars(query).all()
