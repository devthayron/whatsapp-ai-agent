# integrations/meta/parser.py
from app.schemas.message import MessageReceived
from config import settings


def _normalize_text_message(
    message: dict, contacts: dict[str, str | None]
) -> MessageReceived | None:
    if message.get("type") != "text":
        return None

    number = message.get("from")
    body = (message.get("text") or {}).get("body")
    if not number or not isinstance(body, str) or not body.strip():
        return None

    message_id = message.get("id")
    timestamp = str(message.get("timestamp") or "")

    return MessageReceived(
        external_id=f"meta_{message_id}" if message_id else None,
        number=number,
        name=contacts.get(number),
        content=body.strip(),
        content_type="text",
        timestamp=int(timestamp) if timestamp.isdigit() else None,
    )


def extract_messages(payload: dict) -> list[MessageReceived]:
    """Extrai as mensagens de texto válidas de um webhook da Meta."""
    if payload.get("object") != "whatsapp_business_account":
        return []

    result: list[MessageReceived] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue

            value = change.get("value", {})
            if (
                value.get("metadata", {}).get("phone_number_id")
                != settings.META_PHONE_NUMBER_ID
            ):
                continue

            contacts = {
                c.get("wa_id"): (c.get("profile") or {}).get("name")
                for c in value.get("contacts", [])
            }

            for raw_message in value.get("messages", []):
                message = _normalize_text_message(raw_message, contacts)
                if message:
                    result.append(message)

    return result
