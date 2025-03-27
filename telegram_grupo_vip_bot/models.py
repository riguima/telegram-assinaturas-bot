from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from telegram_grupo_vip_bot.database import db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[Optional[str]]
    cpf_cnpj: Mapped[Optional[str]]
    name: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    username: Mapped[str]
    signatures: Mapped[List['Signature']] = relationship(
        back_populates='user', cascade='all,delete-orphan'
    )
    payments: Mapped[List['Payment']] = relationship(
        back_populates='user', cascade='all,delete-orphan'
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


class Plan(Base):
    __tablename__ = 'plans'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[float]
    message: Mapped[str]
    days: Mapped[int]
    signatures: Mapped[List['Signature']] = relationship(
        back_populates='plan', cascade='all,delete-orphan'
    )
    payments: Mapped[List['Payment']] = relationship(
        back_populates='plan', cascade='all,delete-orphan'
    )


class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[str]
    plan: Mapped['Plan'] = relationship(back_populates='payments')
    plan_id: Mapped[int] = mapped_column(ForeignKey('plans.id'))
    user: Mapped['User'] = relationship(back_populates='payments')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    chat_id: Mapped[str]


class Setting(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[str]


Base.metadata.create_all(db)
