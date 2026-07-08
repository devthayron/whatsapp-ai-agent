def handle_text(raw_message):
    return raw_message.get("message", {}).get("conversation")

def handle_image(raw_message):
    return "(Mensagem do tipo imagem)"

def handle_audio(raw_message):
    return "(Mensagem do tipo áudio)"


def handle_message_type(raw_message):
    message_type = raw_message.get("messageType")

    MESSAGE_TYPE_HANDLERS = {
        "conversation": handle_text,
        "imageMessage": handle_image,
        "audioMessage": handle_audio,
    }

    handle = MESSAGE_TYPE_HANDLERS.get(message_type)

    if handle:
        return message_type, handle(raw_message)

    return message_type, "(Mensagem diferente de texto e imagem e audio)"


def process_message(raw_message):
    key = raw_message.get("key", {})
    remote_jid = key.get("remoteJid")
    remote_Jid_alt = key.get("remoteJidAlt")
    from_me = key.get("fromMe")
    timestamp = raw_message.get("messageTimestamp")
    push_name = raw_message.get("pushName")

    # Apenas mensagens de texto por enquanto
    message_type, message = handle_message_type(raw_message)
    
    # Número do contato da conversa
    number = remote_Jid_alt or remote_jid
    
    if number is None:
        return None

    number = number.split("@")[0]

    return {
        "remoteJid": remote_jid,
        "number": number,
        "push_name": push_name,
        "from_me": from_me,
        "message": message,
        "message_type": message_type,
        "timestamp": timestamp,
    }