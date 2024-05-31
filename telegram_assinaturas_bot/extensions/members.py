import re

from sqlalchemy import select
from telebot.util import quick_markup

from telegram_assinaturas_bot.database import Session
from telegram_assinaturas_bot.models import Signature, User, Account
from telegram_assinaturas_bot.utils import get_today_date


current_username = None


def init_bot(bot, start):
    @bot.callback_query_handler(func=lambda c: c.data == 'add_member')
    def add_member(callback_query):
        bot.send_message(
            callback_query.message.chat.id, 'Digite o arroba do membro'
        )
        bot.register_next_step_handler(callback_query.message, on_username)

    def on_username(message):
        with Session() as session:
            user_model = User(username=message.text)
            session.add(user_model)
            session.commit()
        bot.send_message(message.chat.id, 'Membro Adicionado!')
        start(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'show_members')
    def show_members(callback_query):
        bot.send_message(
            callback_query.message.chat.id,
            'Membros',
            reply_markup=quick_markup(
                {
                    'Buscar Membros': {'callback_data': 'search_members'},
                    'Ver Membros': {'callback_data': 'see_members'},
                    'Voltar': {'callback_data': 'return_to_main_menu'},
                },
                row_width=1,
            ),
        )

    @bot.callback_query_handler(func=lambda c: c.data == 'see_members')
    def see_members(callback_query):
        with Session() as session:
            options = {}
            for user_model in session.scalars(select(User)).all():
                options[user_model.username] = {
                    'callback_data': f'show_member:{user_model.username}'
                }
            options['Voltar'] = {'callback_data': 'return_to_main_menu'}
            bot.send_message(
                callback_query.message.chat.id,
                'Membros',
                reply_markup=quick_markup(options, row_width=1),
            )

    @bot.callback_query_handler(func=lambda c: c.data == 'search_members')
    def search_members(callback_query):
        bot.send_message(
            callback_query.message.chat.id, 'Digite o termo para busca'
        )
        bot.register_next_step_handler(callback_query.message, on_search_term)

    def on_search_term(message):
        with Session() as session:
            options = {}
            options['Buscar Membros'] = {'callback_data': 'search_members'}
            for user_model in session.scalars(select(User)).all():
                if message.text in user_model.username:
                    options[user_model.username] = {
                        'callback_data': f'show_member:{user_model.username}'
                    }
            options['Voltar'] = {'callback_data': 'return_to_main_menu'}
            bot.send_message(
                message.chat.id,
                'Membros',
                reply_markup=quick_markup(options, row_width=1),
            )

    @bot.callback_query_handler(func=lambda c: 'show_member:' in c.data)
    def show_members_action(callback_query):
        with Session() as session:
            username = callback_query.data.split(':')[-1]
            query = select(User).where(User.username == username)
            user_model = session.scalars(query).first()
            query = select(Signature).where(Signature.user_id == user_model.id).where(Signature.due_date >= get_today_date())
            signatures = session.scalars(query).all()
            if signatures:
                send_member_menu(callback_query.message, signatures)
            else:
                bot.send_message(
                    callback_query.message.chat.id,
                    'Membro não possui uma assinatura ativa',
                    reply_markup=quick_markup(
                        {
                            'Adicionar Plano': {
                                'callback_data': f'add_member_account:{user_model.username}',
                            },
                            'Enviar Mensagem': {
                                'callback_data': f'send_message:{user_model.username}'
                            },
                            'Remover Membro': {
                                'callback_data': f'remove_member:{user_model.username}'
                            },
                            'Voltar': {'callback_data': 'return_to_main_menu'},
                        },
                        row_width=1,
                    ),
                )

    def send_member_menu(message, signatures_models):
        reply_markup = {}
        for signature_model in signatures_models:
            reply_markup[
                f'{signature_model.plan.name} - {signature_model.plan.days} Dias - R${signature_model.plan.value:.2f}'
            ] = {
                'callback_data': f'show_member_signature:{signature_model.id}'
            }
        reply_markup['Adicionar Plano'] = {
            'callback_data': f'add_member_account:{signatures_models[0].user.username}'
        }
        reply_markup['Enviar Mensagem'] = {
            'callback_data': f'send_message:{signatures_models[0].user.username}'
        }
        reply_markup['Remover Membro'] = {
            'callback_data': f'remove_member:{signatures_models[0].user.username}'
        }
        reply_markup['Voltar'] = {'callback_data': 'return_to_main_menu'}
        bot.send_message(
            message.chat.id,
            'Escolha uma opção',
            reply_markup=quick_markup(reply_markup, row_width=1),
        )

    @bot.callback_query_handler(
        func=lambda c: 'show_member_signature:' in c.data
    )
    def show_member_signature(callback_query):
        global current_username
        signature_id = int(callback_query.data.split(':')[-1])
        with Session() as session:
            signature_model = session.get(Signature, signature_id)
            current_username = signature_model.user.username
            bot.send_message(
                callback_query.message.chat.id,
                f'{signature_model.plan.name} - {signature_model.plan.days} Dias - R${signature_model.plan.value:.2f}\n\nVencimento do plano: {signature_model.due_date:%d/%m/%Y}',
                reply_markup=quick_markup(
                    {
                        'Escolher Conta': {
                            'callback_data': f'show_accounts_of_plan:{signature_model.plan.id}:choose_account:{signature_model.id}'
                        },
                        'Cancelar Assinatura': {
                            'callback_data': f'cancel_signature:{signature_id}'
                        },
                        'Voltar': {'callback_data': 'return_to_main_menu'},
                    },
                    row_width=1,
                ),
            )

    @bot.callback_query_handler(func=lambda c: bool(re.findall('^choose_account:', c.data)))
    def choose_account(callback_query):
        signature_id, account_id = callback_query.data.split(':')[1:]
        bot.send_message(callback_query.message.chat.id, 'Escolha uma opção', reply_markup=quick_markup({
            'Adicionar Conta ao Plano': {'callback_data': f'add_account_in_plan:{signature_id}:{account_id}'},
            'Voltar': {'callback_data': 'return_to_main_menu'},
        }, row_width=1))

    @bot.callback_query_handler(func=lambda c: 'add_account_in_plan:' in c.data)
    def add_account_in_plan(callback_query):
        signature_id, account_id = callback_query.data.split(':')[1:]
        with Session() as session:
            account_model = session.get(Account, int(account_id))
            signature_model = session.get(Signature, int(signature_id))
            signature_model.account_id = account_model.id
            session.commit()
        bot.send_message(callback_query.message.chat.id, 'Conta Adicionada!')
        start(callback_query.message)

    @bot.callback_query_handler(func=lambda c: 'add_member_account:' in c.data)
    def add_member_account(callback_query):
        global current_username
        current_username = callback_query.data.split(':')[-1]
        bot.send_message(
            callback_query.message.chat.id,
            'Escolha a conta',
            reply_markup=quick_markup(
                get_categories_reply_markup(
                    'show_accounts_of_plan', 'attach_account'
                ),
                row_width=1,
            ),
        )

    @bot.callback_query_handler(
        func=lambda c: 'attach_account:' in c.data
    )
    def add_member_account_action(callback_query):
        account_id = callback_query.data.split(':')[1:]
        bot.send_message(
            callback_query.message.chat.id,
            'Digite a quantidade de dias de acesso',
        )
        bot.register_next_step_handler(
            callback_query.message,
            lambda m: on_signatures_days(m, account_id),
        )

    def on_signatures_days(message, account_id):
        try:
            with Session() as session:
                query = select(User).where(User.username == current_username)
                user_model = session.scalars(query).first()
                account_model = session.get(Account, account_id)
                signature_model = Signature(
                    user=user_model,
                    plan_id=account_model.plan_id,
                    due_date=get_today_date()
                    + timedelta(days=int(message.text)),
                    account=account_model,
                )
                session.add(signature_model)
                session.commit()
            bot.send_message(message.chat.id, 'Membro Adicionado a Conta!')
        except ValueError:
            bot.send_message(
                message.chat.id,
                'Valor inválido, digite como no exemplo: 10 ou 15',
            )
        start(message)

    @bot.callback_query_handler(func=lambda c: 'send_message:' in c.data)
    def send_member_message(callback_query):
        username = callback_query.data.split(':')[-1]
        bot.send_message(callback_query.message.chat.id, 'Envie as mensagens que deseja enviar para o membro, utilize as tags: {nome}, digite /stop para parar')
        bot.register_next_step_handler(callback_query.message, lambda m: on_member_message(m, username))


    def on_member_message(message, username, for_send_messages=[]):
        if message.text == '/stop':
            sending_message = bot.send_message(message.chat.id, 'Enviando Mensagens...')
            with Session() as session:
                query = select(User).where(User.username == username)
                member = session.scalars(query).first()
                for for_send_message in for_send_messages:
                    try:
                        bot.send_message(str(member.chat_id), for_send_message.text.format(nome=username))
                    except ApiTelegramException:
                        continue
            bot.delete_message(message.chat.id, sending_message.id)
            bot.send_message(message.chat.id, 'Mensagens Enviadas!')
            start(message)
        else:
            for_send_messages.append(message)
            bot.register_next_step_handler(message, lambda m: on_member_message(m, username, for_send_messages))


    @bot.callback_query_handler(func=lambda c: 'remove_member:' in c.data)
    def remove_member_action(callback_query):
        with Session() as session:
            username = callback_query.data.split(':')[-1]
            query = select(User).where(User.username == username)
            user_model = session.scalars(query).first()
            session.delete(user_model)
            session.commit()
            bot.send_message(
                callback_query.message.chat.id, 'Membro Removido!'
            )
            start(callback_query.message)
