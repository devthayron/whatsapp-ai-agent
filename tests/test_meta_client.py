from config import settings
from integrations.meta.client import MetaService


class FakeResponse:
    status_code = 200
    text = "{}"

    def raise_for_status(self):
        pass

    def json(self):
        return {"messages": [{"id": "wamid.X"}]}


def test_send_message_builds_cloud_api_payload(monkeypatch):
    service = MetaService()
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(url=url, json=json)
        return FakeResponse()

    monkeypatch.setattr(service.session, "post", fake_post)

    data = service.send_message("5511999999999", "oi")

    assert captured["url"].endswith(f"/{settings.META_PHONE_NUMBER_ID}/messages")
    assert captured["json"]["messaging_product"] == "whatsapp"
    assert captured["json"]["to"] == "5511999999999"
    assert captured["json"]["text"]["body"] == "oi"
    assert data == {"messages": [{"id": "wamid.X"}]}


def test_authorization_header_uses_access_token():
    service = MetaService()

    assert service.session.headers["Authorization"] == (
        f"Bearer {settings.META_ACCESS_TOKEN}"
    )
