import pytest

from bot.message_processor import (
    extract_webhook_message,
    handle_audio,
    handle_image,
    handle_message_type,
    handle_text,
    normalize_message,
    normalize_phone,
)


@pytest.fixture
def make_raw_message():
    """
    Cria um raw_message no formato da Evolution API com valores padrão de uma mensagem de texto válida.

    Uso:
        raw_message = make_raw_message()
        raw_message = make_raw_message(remote_jid_alt="123456789@s.whatsapp.net")
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
        message_body = (
            {"conversation": content} if message_type == "conversation" else {}
        )

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


# handle_text / handle_image / handle_audio / handle_message_type
#
# handle_message_type olha o campo "messageType" e chama o handler correspondente no dicionário MESSAGE_TYPE_HANDLERS.
# Cada handler individual sabe extrair (ou simular) o conteúdo daquele tipo específico.


def test_handle_text_extracts_conversation_field():
    """
    Mensagens de texto armazenam seu conteúdo em 'message.conversation'.
    """
    raw_message = {"message": {"conversation": "olá, tudo bem?"}}
    assert handle_text(raw_message) == "olá, tudo bem?"


def test_handle_text_missing_message_returns_none():
    """
    Se o payload não possuir o campo 'message', não há conteúdo para extrair e a função deve retornar None.
    """
    assert handle_text({}) is None


def test_handle_image_returns_placeholder():
    """
    Mensagens de imagem retornam um placeholder enquanto não há processamento.
    """
    assert handle_image({}) == "[Imagem enviada pelo usuário]"


def test_handle_audio_returns_placeholder():
    """
    Mensagens de áudio retornam um placeholder enquanto não há transcrição.
    """
    assert handle_audio({}) == "[Áudio enviado pelo usuário]"


@pytest.mark.parametrize(
    "message_type, expected_content",
    [
        ("conversation", "teste"),
        ("imageMessage", "[Imagem enviada pelo usuário]"),
        ("audioMessage", "[Áudio enviado pelo usuário]"),
    ],
)
def test_handle_message_type_known_types(
    make_raw_message, message_type, expected_content
):
    """
    Cada tipo de mensagem conhecido deve ser encaminhado ao handler correspondente.
    """
    raw_message = make_raw_message(message_type=message_type, content="teste")
    result_type, content = handle_message_type(raw_message)
    assert result_type == message_type
    assert content == expected_content


def test_handle_message_type_unknown_type_uses_fallback(make_raw_message):
    """
    Tipos desconhecidos devem utilizar o fallback sem interromper o processamento.
    """
    raw_message = make_raw_message(message_type="stickerMessage")
    result_type, content = handle_message_type(raw_message)
    assert result_type == "stickerMessage"
    assert content == "[Mensagem do tipo: stickerMessage]"


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
# Converte um raw_message da Evolution API para o formato
# padronizado utilizado pelo restante da aplicação.


def test_normalize_message_prefers_remote_jid_alt(make_raw_message):
    """
    Prioriza remoteJidAlt quando ambos os identificadores estão presentes.
    """
    raw_message = make_raw_message(
        remote_jid="111@s.whatsapp.net",
        remote_jid_alt="222@s.whatsapp.net",
    )

    result = normalize_message(raw_message)
    assert result["number"] == "222"


def test_normalize_message_without_number_returns_none(make_raw_message):
    """
    Retorna None quando não é possível identificar o número do contato.
    """
    raw_message = make_raw_message(remote_jid=None, remote_jid_alt=None)
    assert normalize_message(raw_message) is None


def test_normalize_message_builds_expected_dict(make_raw_message):
    """
    Monta o dicionário padronizado com todos os campos esperados.
    """
    raw_message = make_raw_message()

    result = normalize_message(raw_message)

    assert result == {
        "message_id": "MSG1",
        "from_me": False,
        "number": "5511999999999",
        "push_name": "Fulano",
        "content": "Oi, tudo bem?",
        "message_type": "conversation",
        "timestamp": 1710000000,
    }
