import logging

from app.schemas.message import MessageReceived

logger = logging.getLogger(__name__)


def extract_webhook_message(payload):
    event = payload.get("event")

    # Processa apenas novas mensagens recebidas
    if event != "messages.upsert":
        logger.debug("Evento de webhook ignorado | event=%s", event)
        return None

    raw_message = payload.get("data")

    if not raw_message:
        logger.debug("Payload sem campo 'data', ignorado")
        return None

    key = raw_message.get("key", {})
    remote_jid = key.get("remoteJid", "")

    # Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe"):
        logger.debug(
            "Mensagem ignorada (enviada pelo próprio bot) | remote_jid=%s",
            remote_jid,
        )
        return None

    # Responde apenas mensagens no contato privado
    if not remote_jid.endswith("@s.whatsapp.net"):
        logger.debug(
            "Mensagem ignorada | motivo=chat não individual | remote_jid=%s",
            remote_jid,
        )
        return None

    return raw_message


def handle_text(raw_message):
    """Texto simples."""
    content = raw_message.get("message", {}).get("conversation")

    return "text", content


def handle_extended_text(raw_message):
    """Texto com link, resposta (reply) ou preview."""
    content = raw_message.get("message", {}).get("extendedTextMessage", {}).get("text")

    return "text", content


# Tipos de mensagem da Evolution → handlers da aplicação
MESSAGE_TYPE_HANDLERS = {
    "conversation": handle_text,
    "extendedTextMessage": handle_extended_text,
}


def handle_message_type(raw_message):
    """
    Retorna (content_type, content).

    content_type é o tipo definido pela aplicação.
    content é None quando o tipo não é suportado ou não há texto.
    """
    message_type = raw_message.get("messageType")

    handler = MESSAGE_TYPE_HANDLERS.get(message_type)

    if handler is None:
        logger.debug(
            "Tipo de mensagem ignorado | message_type=%s",
            message_type,
        )
        return None, None

    content_type, content = handler(raw_message)

    if not isinstance(content, str) or not content.strip():
        return content_type, None

    return content_type, content.strip()


def normalize_phone(number: str | None) -> str | None:
    if number is None:
        return None

    return number.split("@")[0]


def normalize_message(raw_message: dict) -> MessageReceived | None:
    key = raw_message.get("key", {})

    message_id = key.get("id")
    remote_jid = key.get("remoteJid")
    remote_jid_alt = key.get("remoteJidAlt")

    content_type, content = handle_message_type(raw_message)

    if content is None:
        logger.debug(
            "Mensagem ignorada | motivo=não é texto | content_type=%s | message_id=%s",
            content_type,
            message_id,
        )
        return None

    number = normalize_phone(remote_jid_alt or remote_jid)

    if not number:
        logger.warning(
            "Mensagem sem número identificável, ignorada | message_id=%s",
            message_id,
        )
        return None

    return MessageReceived(
        external_id=f"evolution_{message_id}" if message_id else None,
        number=number,
        name=raw_message.get("pushName"),
        content=content,
        content_type=content_type,
        timestamp=raw_message.get("messageTimestamp"),
    )
