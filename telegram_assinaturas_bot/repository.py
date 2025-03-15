from datetime import datetime

from pytz import timezone
from sqlalchemy import select

from telegram_assinaturas_bot import models
from telegram_assinaturas_bot.database import Session


def get_today_date():
    return datetime.now(timezone('America/Sao_Paulo')).date()


def get_users(bot_token):
    with Session() as session:
        query = select(models.User).where(models.User.bot_token == bot_token)
        return session.scalars(query).all()


def search_users(bot_token, search):
    with Session() as session:
        query = select(models.User).where(
            models.User.bot_token, models.User.username.ilike(f'%{search}%')
        )
        return session.scalars(query).all()


def create_user(bot_token, username):
    with Session() as session:
        user = models.User(bot_token=bot_token, username=username)
        session.add(user)
        session.commit()


def create_update_user(bot_token, username, name, chat_id):
    with Session() as session:
        query = select(models.User).where(
            models.User.bot_token == bot_token, models.User.username == username
        )
        user_model = session.scalars(query).first()
        if user_model is None:
            user_model = models.User(
                bot_token=bot_token,
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


def get_user_by_username(bot_token, username):
    with Session() as session:
        query = select(models.User).where(
            models.User.bot_token == bot_token, models.User.username == username
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


def delete_user_by_username(bot_token, username):
    with Session() as session:
        query = select(models.User).where(
            models.User.bot_token == bot_token, models.User.username == username
        )
        user = session.scalars(query).first()
        session.delete(user)
        session.commit()


def get_active_signatures(user_id):
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


def get_active_account_signatures(account_id):
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.account_id == account_id,
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


def get_account_signatures(account_id):
    with Session() as session:
        query = select(models.Signature).where(
            models.Signature.account_id == account_id
        )
        return session.scalars(query).all()


def edit_signature_account(signature_id, account_id):
    with Session() as session:
        signature = session.get(models.Signature, signature_id)
        signature.account_id = account_id
        session.commit()


def create_signature(
    bot_token, user_id, plan_id, due_date, account_id=None, payment_id=None
):
    with Session() as session:
        signature = models.Signature(
            bot_token=bot_token,
            user_id=user_id,
            plan_id=plan_id,
            account_id=account_id,
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


def get_accounts(bot_token):
    with Session() as session:
        query = select(models.Account).where(
            models.Account.bot_token == bot_token
        )
        return session.scalars(query).all()


def get_plan_accounts(plan_id):
    with Session() as session:
        query = select(models.Account).where(models.Account.plan_id == int(plan_id))
        return session.scalars(query).all()


def get_plan_from_account(account_id):
    with Session() as session:
        account = session.get(models.Account, account_id)
        return account.plan


def get_account(account_id):
    with Session() as session:
        return session.get(models.Account, account_id)


def create_account(bot_token, plan_id, message):
    with Session() as session:
        account_model = models.Account(
            bot_token=bot_token,
            plan_id=plan_id,
            message=message,
        )
        session.add(account_model)
        session.commit()


def edit_account_message(account_id, message):
    with Session() as session:
        account = session.get(models.Account, account_id)
        account.message = message
        session.commit()


def delete_account(account_id):
    with Session() as session:
        account = session.get(models.Account, account_id)
        session.delete(account)
        session.commit()


def get_categories(bot_token):
    with Session() as session:
        query = select(models.Category).where(
            models.Category.bot_token == bot_token
        )
        return session.scalars(query).all()


def get_main_categories(bot_token):
    with Session() as session:
        query = select(models.Category).where(
            models.Category.bot_token == bot_token,
            models.Category.parent_category_name == 'Nenhuma',
        )
        return session.scalars(query).all()


def get_category(category_id):
    with Session() as session:
        return session.get(models.Category, category_id)


def create_category(bot_token, parent_category_name, name):
    with Session() as session:
        category_model = models.Category(
            bot_token=bot_token,
            parent_category_name=parent_category_name,
            name=name,
        )
        session.add(category_model)
        session.commit()


def get_subcategories(bot_token, parent_category_id):
    with Session() as session:
        category = session.get(models.Category, parent_category_id)
        query = select(models.Category).where(
            models.Category.bot_token == bot_token,
            models.Category.parent_category_name == category.name,
        )
        return session.scalars(query).all()


def edit_category_name(category_id, name):
    with Session() as session:
        category = session.get(models.Category, category_id)
        category.name = name
        session.commit()


def edit_parent_category(category_id, parent_category_id):
    with Session() as session:
        category = session.get(models.Category, category_id)
        parent_category = session.get(models.Category, parent_category_id)
        if parent_category:
            category.parent_category_name = parent_category.name
        else:
            category.parent_category_name = 'Nenhuma'
        session.commit()


def get_categories_except(bot_token, category_id):
    with Session() as session:
        category = session.get(models.Category, category_id)
        query = select(models.Category).where(
            models.Category.bot_token == bot_token,
            models.Category.name != category.parent_category_name,
            models.Category.name != category.name,
        )
        return session.scalars(query).all()


def delete_category(category_id):
    with Session() as session:
        category = session.get(models.Category, category_id)
        query = select(models.Category).where(
            models.Category.parent_category_name == category.name
        )
        for child_category_model in session.scalars(query).all():
            child_category_model.parent_category_name = 'Nenhuma'
        session.delete(category)
        session.commit()


def get_setting(bot_token, name, default=''):
    with Session() as session:
        query = select(models.Setting).where(
            models.Setting.bot_token == bot_token, models.Setting.name == name
        )
        setting = session.scalars(query).first()
        return default if setting is None else setting.value


def set_setting(bot_token, name, value):
    with Session() as session:
        query = select(models.Setting).where(
            models.Setting.bot_token == bot_token, models.Setting.name == name
        )
        setting = session.scalars(query).first()
        if setting:
            setting.value = value
        else:
            setting = models.Setting(
                bot_token=bot_token,
                name=name,
                value=value,
            )
            session.add(setting)
        session.commit()


def get_plan(plan_id):
    with Session() as session:
        return session.get(models.Plan, plan_id)


def get_plans_with_category(category_id):
    with Session() as session:
        query = select(models.Plan).where(models.Plan.category_id == category_id)
        return session.scalars(query).all()


def create_plan(bot_token, value, name, days, category_id):
    with Session() as session:
        plan = models.Plan(
            bot_token=bot_token,
            value=value,
            name=name,
            days=days,
            category_id=category_id,
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


def get_payment(payment_id, gateway):
    with Session() as session:
        query = select(models.Payment).where(
            models.Payment.payment_id == payment_id,
            models.Payment.gateway == gateway,
        )
        return session.scalars(query).first()


def get_payment_plan(payment_id):
    with Session() as session:
        return session.get(models.Payment, payment_id).plan


def create_payment(bot_token, chat_id, user_id, payment_id, gateway, plan):
    with Session() as session:
        payment = models.Payment(
            bot_token=bot_token,
            chat_id=chat_id,
            user_id=user_id,
            payment_id=payment_id,
            gateway=gateway,
            plan=plan,
        )
        session.add(payment)
        session.commit()


def delete_payment(payment_id):
    with Session() as session:
        payment = session.get(models.Payment, payment_id)
        session.delete(payment)
        session.commit()


def get_subscribers(bot_token):
    with Session() as session:
        query = (
            select(models.User)
            .join(models.Signature)
            .where(
                models.Signature.bot_token == bot_token,
                models.Signature.due_date >= get_today_date(),
            )
        )
        return session.scalars(query).all()


def get_bots():
    with Session() as session:
        query = select(models.Bot).where(models.Bot.token != '')
        return session.scalars(query).all()


def get_bot(bot_id):
    with Session() as session:
        return session.get(models.Bot, bot_id)


def get_bot_by_token(token):
    with Session() as session:
        query = select(models.Bot).where(models.Bot.token == token)
        return session.scalars(query).first()


def get_active_bots(username):
    with Session() as session:
        query = select(models.Bot).where(
            models.Bot.username == username,
            models.Bot.token != ''
        )
        return session.scalars(query).all()


def get_inactive_bots(username):
    with Session() as session:
        query = select(models.Bot).where(
            models.Bot.username == username,
            models.Bot.token == ''
        )
        return session.scalars(query).all()


def create_bot(username, token):
    with Session() as session:
        bot = models.Bot(
            username=username,
            token=token,
        )
        session.add(bot)
        session.commit()


def edit_bot_token(bot_id, token):
    with Session() as session:
        bot = session.get(models.Bot, bot_id)
        bot.token = token
        session.commit()


def is_admin(username):
    with Session() as session:
        query = select(models.Bot).where(models.Bot.username == username)
        return bool(session.scalars(query).all())
