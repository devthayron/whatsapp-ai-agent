def extract_webhook_message(payload):

    event = payload.get("event")
    # Processa apenas novas mensagens recebidas
    if event != "messages.upsert":
        return None

    raw_message = payload.get("data")

    if not raw_message:
        return None
    
    key = raw_message.get("key", {})
    remote_jid = key.get("remoteJid", "")

    # Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe"):
        return None
    
    # Responde apenas mensagens no contato privado
    if not remote_jid.endswith("@s.whatsapp.net"):
        return None

    return raw_message


def handle_text(raw_message):
    return raw_message.get("message", {}).get("conversation")

def handle_image(raw_message):
    return "[Imagem enviada pelo usuário]"

def handle_audio(raw_message):
    return "[Áudio enviado pelo usuário]"

MESSAGE_TYPE_HANDLERS = {
        "conversation": handle_text,
        "imageMessage": handle_image,
        "audioMessage": handle_audio,
    }

def handle_message_type(raw_message):
    message_type = raw_message.get("messageType")

    handle = MESSAGE_TYPE_HANDLERS.get(message_type)

    if handle:
        return message_type, handle(raw_message)

    return message_type, f"[Mensagem do tipo: {message_type}]"

def normalize_phone(number: str | None) -> str | None:

    if number is None:
        return None

    return number.split("@")[0]

def normalize_message(raw_message):
    
    key = raw_message.get("key", {})
    message_id = key.get('id')
    from_me = key.get("fromMe")
    remote_jid = key.get("remoteJid")
    remote_jid_alt = key.get("remoteJidAlt")
    timestamp = raw_message.get("messageTimestamp")
    push_name = raw_message.get("pushName")

    # Apenas mensagens de texto por enquanto
    message_type, content = handle_message_type(raw_message)
    
    # Número do contato da conversa
    number = normalize_phone(remote_jid_alt or remote_jid)

    if not number:
        return None

    return {
        'message_id': message_id,
        "from_me": from_me,
        "number": number,
        "push_name": push_name,
        "content": content,
        "message_type": message_type,
        "timestamp": timestamp,
    }

