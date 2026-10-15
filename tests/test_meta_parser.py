import pytest

from app.schemas.message import MessageReceived
from config import settings
from integrations.meta.parser import extract_messages


def text_message(msg_id="wamid.1", sender="5511999999999", body="Oi, tudo bem?"):
    return {
        "from": sender,
        "id": msg_id,
        "timestamp": "1710000000",
        "type": "text",
        "text": {"body": body},
    }


@pytest.fixture
def make_payload():
    def _make(
        messages=None,
        contacts=None,
        phone_number_id=None,
        field="messages",
        obj="whatsapp_business_account",
        include_messages=True,
    ):
        value = {
            "messaging_product": "whatsapp",
            "metadata": {
                "display_phone_number": "15550000000",
                "phone_number_id": phone_number_id or settings.META_PHONE_NUMBER_ID,
            },
            "contacts": (
                [{"profile": {"name": "Fulano"}, "wa_id": "5511999999999"}]
                if contacts is None
                else contacts
            ),
        }

        if include_messages:
            value["messages"] = [text_message()] if messages is None else messages
        else:
            value["statuses"] = [{"id": "wamid.1", "status": "read"}]

        return {
            "object": obj,
            "entry": [{"id": "WABA", "changes": [{"field": field, "value": value}]}],
        }

    return _make


def test_builds_message_received(make_payload):
    result = extract_messages(make_payload())

    assert result == [
        MessageReceived(
            external_id="meta_wamid.1",
            number="5511999999999",
            name="Fulano",
            content="Oi, tudo bem?",
            content_type="text",
            timestamp=1710000000,
        )
    ]


def test_strips_whitespace(make_payload):
    result = extract_messages(make_payload(messages=[text_message(body="  oi  ")]))
    assert result[0].content == "oi"


def test_name_is_none_without_contacts(make_payload):
    result = extract_messages(make_payload(contacts=[]))
    assert result[0].name is None


def test_extracts_multiple_messages(make_payload):
    messages = [text_message("wamid.1", body="a"), text_message("wamid.2", body="b")]
    result = extract_messages(make_payload(messages=messages))

    assert [m.content for m in result] == ["a", "b"]
    assert [m.external_id for m in result] == ["meta_wamid.1", "meta_wamid.2"]


def test_ignores_status_events(make_payload):
    assert extract_messages(make_payload(include_messages=False)) == []


def test_ignores_wrong_object(make_payload):
    assert extract_messages(make_payload(obj="page")) == []


def test_ignores_other_field(make_payload):
    assert extract_messages(make_payload(field="account_update")) == []


def test_ignores_other_phone_number_id(make_payload):
    assert extract_messages(make_payload(phone_number_id="999")) == []


@pytest.mark.parametrize("message_type", ["image", "audio", "sticker", "reaction"])
def test_ignores_non_text(make_payload, message_type):
    message = {"from": "5511999999999", "id": "wamid.1", "type": message_type}
    assert extract_messages(make_payload(messages=[message])) == []


@pytest.mark.parametrize("body", [None, "", "   "])
def test_ignores_empty_text(make_payload, body):
    assert extract_messages(make_payload(messages=[text_message(body=body)])) == []


def test_empty_payload_returns_empty_list():
    assert extract_messages({}) == []
