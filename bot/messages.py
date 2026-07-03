def process_message(record):
    key = record.get("key", {})
    remoteJid = key.get("remoteJid")
    from_me = key.get("fromMe")
    message_type = record.get("messageType")
    timestamp = record.get("messageTimestamp")
    push_name = record.get("pushName")

    # Apenas mensagens de texto por enquanto
    if message_type != "conversation":
        return None

    message = record.get("message", {}).get("conversation")

    # Número do contato da conversa
    number = (
        key.get("remoteJidAlt")
        or key.get("remoteJid", "")
    ).split("@")[0]

    return {
        "remoteJid": remoteJid,
        "number": number,
        "push_name": push_name,
        "from_me": from_me,
        "message": message,
        "message_type": message_type,
        "timestamp": timestamp,
    }


def build_history(messages):
    history = {}

    for msg in messages:
        if msg['from_me'] is False:
            number = msg["number"]

        if number not in history:
            history[number] = {
                "push_name": msg["push_name"],
                "messages": [],
            }

        history[number]["messages"].append({
            "from_me": msg["from_me"],
            "message": msg["message"],
            "message_type": msg["message_type"],
            "timestamp": msg["timestamp"],
        })

    return history