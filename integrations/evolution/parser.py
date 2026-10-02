import logging

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
            "Mensagem ignorada (enviada pelo próprio bot) | remote_jid=%s", remote_jid
        )
        return None

    # Responde apenas mensagens no contato privado
    if not remote_jid.endswith("@s.whatsapp.net"):
        logger.debug(
            "Mensagem ignorada | motivo=chat não individual | remote_jid=%s", remote_jid
        )
        return None

    return raw_message


def handle_text(raw_message):
    """Texto simples."""
    return raw_message.get("message", {}).get("conversation")


def handle_extended_text(raw_message):
    """Texto com link, resposta (reply) ou preview."""
    return raw_message.get("message", {}).get("extendedTextMessage", {}).get("text")


# Apenas tipos de texto são suportados. Qualquer outro tipo é ignorado.
MESSAGE_TYPE_HANDLERS = {
    "conversation": handle_text,
    "extendedTextMessage": handle_extended_text,
}


def handle_message_type(raw_message):
    """
    Retorna (message_type, content).

    content é None quando o tipo não é suportado ou não há texto.
    """
    message_type = raw_message.get("messageType")

    handler = MESSAGE_TYPE_HANDLERS.get(message_type)

    if handler is None:
        logger.debug("Tipo de mensagem ignorado | message_type=%s", message_type)
        return message_type, None

    content = handler(raw_message)

    if not isinstance(content, str) or not content.strip():
        return message_type, None

    return message_type, content.strip()


def normalize_phone(number: str | None) -> str | None:

    if number is None:
        return None

    return number.split("@")[0]


def normalize_message(raw_message):

    key = raw_message.get("key", {})
    message_id = key.get("id")
    from_me = key.get("fromMe")
    remote_jid = key.get("remoteJid")
    remote_jid_alt = key.get("remoteJidAlt")
    timestamp = raw_message.get("messageTimestamp")
    push_name = raw_message.get("pushName")

    # Extrai o conteúdo; só mensagens de texto passam.
    message_type, content = handle_message_type(raw_message)

    if content is None:
        logger.debug(
            "Mensagem ignorada | motivo=não é texto | message_type=%s | message_id=%s",
            message_type,
            message_id,
        )
        return None

    # Número do contato da conversa
    number = normalize_phone(remote_jid_alt or remote_jid)

    if not number:
        logger.warning(
            "Mensagem sem número identificável, ignorada | message_id=%s", message_id
        )
        return None

    return {
        "message_id": message_id,
        "from_me": from_me,
        "number": number,
        "push_name": push_name,
        "content": content,
        "message_type": message_type,
        "timestamp": timestamp,
    }
