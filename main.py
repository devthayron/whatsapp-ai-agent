import json
from services.evolution import get_messages
from bot.messages import process_message, build_history
from config import INSTANCE

def save_messages_to_json(messages, filename=None):
    """
    Salva as mensagens em um arquivo JSON.
    Se nenhum nome de arquivo for fornecido, gera:
    meu_historico_msg.json
    """
    filename = filename or f"{INSTANCE}_historico_msg.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

    return filename


def main():
    registros = get_messages()

    mensagens_processadas = []
    mensagens_ignoradas = 0

    for registro in registros:
        mensagem = process_message(registro)
        if mensagem is None:
            mensagens_ignoradas += 1
            print(
                f"Mensagem ignorada (tipo diferente de texto): "
                f"{registro.get('messageType')}"
            )
            continue

        mensagens_processadas.append(mensagem)

    historico = build_history(mensagens_processadas)

    print(f"Mensagens processadas: {len(mensagens_processadas)}")
    print(f"Mensagens ignoradas: {mensagens_ignoradas}")
    print(f"Contatos encontrados: {len(historico)}")

    arquivo = save_messages_to_json(historico)

    print(f"Histórico salvo em: {arquivo}")


if __name__ == "__main__":
    main()