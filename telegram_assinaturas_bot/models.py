from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from telegram_assinaturas_bot.database import db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    signatures: Mapped[List['Signature']] = relationship(
        back_populates='user', cascade='all,delete-orphan'
    )
    payments: Mapped[List['Payment']] = relationship(
        back_populates='user', cascade='all,delete-orphan'
    )
    account: Mapped[Optional['Account']] = relationship(back_populates='users')
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('accounts.id')
    )


class Signature(Base):
    __tablename__ = 'signatures'
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped['User'] = relationship(back_populates='signatures')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    plan: Mapped['Plan'] = relationship(back_populates='signatures')
    plan_id: Mapped[int] = mapped_column(ForeignKey('plans.id'))
    payment_id: Mapped[Optional[str]]
    create_date: Mapped[Optional[date]] = mapped_column(
        default=(datetime.now() - timedelta(hours=3)).date()
    )
    due_date: Mapped[date]


class Account(Base):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped['Category'] = relationship(back_populates='accounts')
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    login: Mapped[str]
    password: Mapped[str]
    users_number: Mapped[int]
    users: Mapped[List['User']] = relationship(
        back_populates='account', cascade='all,set null'
    )


class Plan(Base):
    __tablename__ = 'plans'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[float]
    days: Mapped[int]
    message: Mapped[str]
    signatures: Mapped[List['Signature']] = relationship(
        back_populates='plan', cascade='all,delete-orphan'
    )
    category: Mapped['Category'] = relationship(back_populates='plans')
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))


class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    parent_category_name: Mapped[Optional[str]] = mapped_column(
        default='Nenhuma'
    )
    plans: Mapped[List['Plan']] = relationship(
        back_populates='category', cascade='all,delete-orphan'
    )
    accounts: Mapped[List['Account']] = relationship(
        back_populates='category', cascade='all,delete-orphan'
    )


class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[str]
    user: Mapped['User'] = relationship(back_populates='payments')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    chat_id: Mapped[str]


Base.metadata.create_all(db)
