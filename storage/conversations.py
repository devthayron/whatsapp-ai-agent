import time
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from storage.database import SessionLocal, Base, engine
from storage.models import Conversation, Message
from services.evolution import evolution_service
from bot.processor import process_message

TIMEZONE = ZoneInfo("America/Sao_Paulo")
MAX_HISTORY = 30

# Cria as tabelas no banco caso ainda não existam (idempotente).
Base.metadata.create_all(bind=engine)

def _add_message(session, conversation, role, content, timestamp):
    """Adiciona uma mensagem à conversa, ignorando se já existir uma idêntica."""
    ja_existe = (
        session.query(Message)
        .filter_by(
            conversation_id=conversation.id,
            role=role,
            content=content,
            timestamp=timestamp,
        )
        .first()
    )
    if ja_existe:
        return

    session.add(Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        timestamp=timestamp,
    ))


def _import_history_from_evolution(session, conversation):
    """
    Busca o histórico antigo direto na Evolution API pra essa conversa
    e salva no banco. Usado só na primeira vez que o número aparece
    (conversa recém-criada, sem mensagens ainda).
    """
    try:
        registros = evolution_service.get_messages_by_number(conversation.number)
    except Exception as e:
        print(f"Falha ao importar histórico da Evolution API pra {conversation.number}: {e}")
        return

    for registro in registros:
        msg = process_message(registro)
        if not msg or not msg["message"]:
            continue

        _add_message(
            session,
            conversation,
            role="assistant" if msg["from_me"] else "user",
            content=msg["message"],
            timestamp=msg["timestamp"],
        )


def _get_or_create_conversation(session, number, push_name):
    conversation = session.query(Conversation).filter_by(number=number).one_or_none()

    if conversation is None:
        conversation = Conversation(number=number, push_name=push_name)
        session.add(conversation)
        session.flush()  # garante que conversation.id já existe antes de importar
        _import_history_from_evolution(session, conversation)
    elif push_name:
        conversation.push_name = push_name

    return conversation


def save_message(number, push_name, from_me, content, timestamp=None):
    """
    Carrega a conversa (criando e importando histórico antigo se for a
    primeira vez), adiciona a mensagem e salva no banco.
    Retorna o objeto Conversation atualizado.
    """
    with SessionLocal() as session:
        if not content:
            conversation = session.query(Conversation).filter_by(number=number).one_or_none()
            if conversation:
                _ = conversation.messages  # força carregar antes de fechar a sessão
            return conversation

        conversation = _get_or_create_conversation(session, number, push_name)

        role = "assistant" if from_me else "user"
        ts = timestamp or int(time.time())

        _add_message(session, conversation, role, content, ts)

        try:
            session.commit()
        except IntegrityError:

            session.rollback()

            conversation = session.query(Conversation).filter_by(number=number).one_or_none()

        if conversation:
            _ = conversation.messages  # força carregar antes de fechar a sessão

        return conversation


def _format_timestamp(ts):
    dt = datetime.fromtimestamp(ts, tz=TIMEZONE)
    return dt.strftime("%d/%m/%Y %H:%M")


def get_openai_history(conversation, limit=MAX_HISTORY):
    if not conversation:
        return []

    mensagens = sorted(conversation.messages, key=lambda m: m.timestamp)[-limit:]

    history = []
    for msg in mensagens:
        time_prefix = f"[{_format_timestamp(msg.timestamp)}] "
        history.append({
            "role": msg.role,
            "content": time_prefix + msg.content,
        })

    return history