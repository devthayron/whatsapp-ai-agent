import pytest

from app.schemas.message import MessageReceived
from integrations.evolution.parser import (
    extract_webhook_message,
    handle_extended_text,
    handle_message_type,
    handle_text,
    normalize_message,
    normalize_phone,
)

UNSUPPORTED_TYPES = [
    "imageMessage",
    "audioMessage",
    "stickerMessage",
    "reactionMessage",
    "protocolMessage",
]


@pytest.fixture
def make_raw_message():
    """
    Cria um raw_message no formato da Evolution API com valores padrão de uma mensagem de texto válida.

    Uso:
        raw_message = make_raw_message()
        raw_message = make_raw_message(remote_jid_alt="123456789@s.whatsapp.net")
        raw_message = make_raw_message(message_type="extendedTextMessage")
    """

    def _make(
        message_id="MSG1",
        from_me=False,
        remote_jid="5511999999999@s.whatsapp.net",
        remote_jid_alt=None,
        timestamp=1710000000,
        push_name="Fulano",
        message_type="conversation",
        content="Oi, tudo bem?",
    ):
        if message_type == "conversation":
            message_body = {"conversation": content}
        elif message_type == "extendedTextMessage":
            message_body = {"extendedTextMessage": {"text": content}}
        else:
            message_body = {}

        return {
            "key": {
                "id": message_id,
                "fromMe": from_me,
                "remoteJid": remote_jid,
                "remoteJidAlt": remote_jid_alt,
            },
            "messageTimestamp": timestamp,
            "pushName": push_name,
            "messageType": message_type,
            "message": message_body,
        }

    return _make


# extract_webhook_message
#   1. evento tem que ser "messages.upsert" (nova mensagem)
#   2. tem que existir o campo "data" com conteúdo
#   3. a mensagem não pode ter sido enviada pelo próprio bot (fromMe=True)
#   4. o chat tem que ser privado (remoteJid termina em "@s.whatsapp.net")


def test_extract_ignores_wrong_event():
    """
    Eventos diferentes de 'messages.upsert' não representam novas mensagens e devem ser ignorados.
    """
    payload = {"event": "connection.update", "data": {"key": {}}}
    assert extract_webhook_message(payload) is None


def test_extract_ignores_missing_data():
    """
    Payloads sem o campo 'data' não possuem mensagem para processar.
    """
    payload = {"event": "messages.upsert"}
    assert extract_webhook_message(payload) is None


def test_extract_ignores_empty_data():
    """
    Um campo 'data' vazio ({}) é tratado como ausência de mensagem.
    """
    payload = {"event": "messages.upsert", "data": {}}
    assert extract_webhook_message(payload) is None


def test_extract_ignores_message_from_bot(make_raw_message):
    """
    Mensagens enviadas pelo próprio bot devem ser ignoradas para evitar que ele responda a si mesmo.
    """
    raw_message = make_raw_message(from_me=True)
    payload = {"event": "messages.upsert", "data": raw_message}
    assert extract_webhook_message(payload) is None


def test_extract_ignores_group_chat(make_raw_message):
    """
    Mensagens enviadas em grupos ('@g.us') são ignoradas, pois o bot atende apenas conversas privadas.
    """
    raw_message = make_raw_message(remote_jid="123456789@g.us")
    payload = {"event": "messages.upsert", "data": raw_message}
    assert extract_webhook_message(payload) is None


def test_extract_accepts_valid_private_message(make_raw_message):
    """
    Quando o payload representa uma mensagem válida de um chat privado, a função deve retornar o raw_message sem alterações.
    """
    raw_message = make_raw_message()
    payload = {"event": "messages.upsert", "data": raw_message}
    assert extract_webhook_message(payload) == raw_message


# handle_text / handle_extended_text / handle_message_type
#
# Retornam (content_type, content). Apenas mensagens de texto são
# suportadas ("conversation" e "extendedTextMessage"), ambas com
# content_type="text". Tipos não suportados retornam (None, None).


def test_handle_text_extracts_conversation_field():
    """
    Mensagens de texto armazenam seu conteúdo em 'message.conversation'.
    """
    raw_message = {"message": {"conversation": "olá, tudo bem?"}}
    assert handle_text(raw_message) == ("text", "olá, tudo bem?")


def test_handle_text_missing_message_returns_none_content():
    """
    Se o payload não possuir o campo 'message', não há conteúdo para extrair.
    """
    assert handle_text({}) == ("text", None)


def test_handle_extended_text_extracts_text():
    """
    Texto com link ou resposta (reply) armazena o conteúdo em 'message.extendedTextMessage.text'.
    """
    raw_message = {"message": {"extendedTextMessage": {"text": "veja https://x.com"}}}
    assert handle_extended_text(raw_message) == ("text", "veja https://x.com")


def test_handle_extended_text_missing_message_returns_none_content():
    """
    Sem o campo 'message' (ou sem 'extendedTextMessage'), o conteúdo é None.
    """
    assert handle_extended_text({}) == ("text", None)
    assert handle_extended_text({"message": {}}) == ("text", None)


@pytest.mark.parametrize("message_type", ["conversation", "extendedTextMessage"])
def test_handle_message_type_text_types(make_raw_message, message_type):
    """
    Os tipos de texto suportados devem ser encaminhados ao handler correspondente.
    """
    raw_message = make_raw_message(message_type=message_type, content="teste")
    assert handle_message_type(raw_message) == ("text", "teste")


def test_handle_message_type_strips_whitespace(make_raw_message):
    """
    Espaços no início e no fim do texto são removidos.
    """
    raw_message = make_raw_message(content="  oi  ")
    assert handle_message_type(raw_message) == ("text", "oi")


@pytest.mark.parametrize("message_type", UNSUPPORTED_TYPES)
def test_handle_message_type_unsupported_returns_none(make_raw_message, message_type):
    """
    Tipos que não são texto retornam (None, None), sem placeholder para o LLM.
    """
    raw_message = make_raw_message(message_type=message_type)
    assert handle_message_type(raw_message) == (None, None)


@pytest.mark.parametrize("content", [None, "", "   "])
def test_handle_message_type_empty_text_returns_none_content(make_raw_message, content):
    """
    Texto ausente, vazio ou só com espaços não tem conteúdo útil.
    """
    raw_message = make_raw_message(content=content)
    assert handle_message_type(raw_message) == ("text", None)


# normalize_phone
#
# Recebe um JID do WhatsApp e retorna apenas o número do contato.


def test_normalize_phone_strips_whatsapp_suffix():
    """
    Caso comum: remove o sufixo '@s.whatsapp.net', sobrando só os dígitos.
    """
    assert normalize_phone("5511999999999@s.whatsapp.net") == "5511999999999"


def test_normalize_phone_none_returns_none():
    """
    Retorna None quando nenhum número é informado.
    """
    assert normalize_phone(None) is None


def test_normalize_phone_no_suffix_returns_same_value():
    """
    Mantém o valor original quando ele já representa apenas o número.
    """
    assert normalize_phone("5511999999999") == "5511999999999"


# normalize_message
#
# Converte um raw_message da Evolution API em MessageReceived,
# o formato padronizado utilizado pelo restante da aplicação.
# Retorna None para mensagens que não são texto.


def test_normalize_message_prefers_remote_jid_alt(make_raw_message):
    """
    Prioriza remoteJidAlt quando ambos os identificadores estão presentes.
    """
    raw_message = make_raw_message(
        remote_jid="111@s.whatsapp.net",
        remote_jid_alt="222@s.whatsapp.net",
    )

    result = normalize_message(raw_message)
    assert result.number == "222"


def test_normalize_message_without_number_returns_none(make_raw_message):
    """
    Retorna None quando não é possível identificar o número do contato.
    """
    raw_message = make_raw_message(remote_jid=None, remote_jid_alt=None)
    assert normalize_message(raw_message) is None


def test_normalize_message_builds_message_received(make_raw_message):
    """
    Monta o MessageReceived com todos os campos esperados.
    """
    result = normalize_message(make_raw_message())

    assert isinstance(result, MessageReceived)
    assert result == MessageReceived(
        external_id="evolution_MSG1",
        number="5511999999999",
        name="Fulano",
        content="Oi, tudo bem?",
        content_type="text",
        timestamp=1710000000,
    )


def test_normalize_message_prefixes_external_id(make_raw_message):
    """
    O external_id recebe o prefixo 'evolution_' para evitar colisão entre provedores.
    """
    result = normalize_message(make_raw_message(message_id="ABC123"))
    assert result.external_id == "evolution_ABC123"


def test_normalize_message_without_message_id_has_no_external_id(make_raw_message):
    """
    Sem id na mensagem, o external_id fica None (e não 'evolution_None').
    """
    result = normalize_message(make_raw_message(message_id=None))
    assert result.external_id is None


def test_normalize_message_extended_text(make_raw_message):
    """
    Texto com link/resposta (extendedTextMessage) é normalizado normalmente.
    """
    raw_message = make_raw_message(
        message_type="extendedTextMessage", content="veja https://x.com"
    )

    result = normalize_message(raw_message)

    assert result.content == "veja https://x.com"
    assert result.content_type == "text"


@pytest.mark.parametrize("message_type", UNSUPPORTED_TYPES)
def test_normalize_message_ignores_non_text(make_raw_message, message_type):
    """
    Mensagens que não são texto são ignoradas e nunca chegam ao LLM.
    """
    raw_message = make_raw_message(message_type=message_type)
    assert normalize_message(raw_message) is None


@pytest.mark.parametrize("content", [None, "", "   "])
def test_normalize_message_ignores_empty_text(make_raw_message, content):
    """
    Texto vazio ou só com espaços é ignorado.
    """
    raw_message = make_raw_message(content=content)
    assert normalize_message(raw_message) is None
