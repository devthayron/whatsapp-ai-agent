# Chatbot WhatsApp com IA

Chatbot para WhatsApp desenvolvido em Python utilizando FastAPI, Evolution API e OpenAI.

O projeto recebe mensagens através de um webhook da Evolution API, mantém o histórico de cada conversa, envia o contexto para a OpenAI e responde automaticamente ao usuário pelo WhatsApp.

---

## Funcionalidades

- Integração com Evolution API
- Webhook para recebimento de mensagens
- Integração com OpenAI
- Memória de conversa por contato
- Histórico no formato compatível com a OpenAI
- Respostas automáticas pelo WhatsApp
- Estrutura modular para facilitar manutenção e escalabilidade

---

## Arquitetura

```text
WhatsApp
    │
    ▼
Evolution API
    │
    ▼
Webhook (FastAPI)
    │
    ▼
Processamento da mensagem
    │
    ▼
Persistência da conversa (JSON)
    │
    ▼
Histórico da conversa
    │
    ▼
OpenAI API
    │
    ▼
Resposta da IA
    │
    ▼
Evolution API
    │
    ▼
WhatsApp
```

---

## Estrutura do projeto

```text
chatbot/
├── app/
│   ├── main.py                # Inicialização da API
│   ├── routes/
│   │   ├── webhook.py         # Recebe mensagens
│   │   └── chat.py
│   └── schemas/
│
├── bot/
│   └── processor.py           # Processamento das mensagens
│
├── services/
│   ├── evolution.py           # Evolution API
│   └── openai.py              # OpenAI API
│
├── storage/
│   └── conversations.py       # Memória das conversas
│
├── data/
│   └── conversations/         # Histórico em JSON
│
├── config.py
├── requirements.txt
└── README.md
```

---

## Tecnologias

- Python 3.12
- FastAPI
- OpenAI API
- Evolution API
- Uvicorn
- python-dotenv

---

## Como funciona

Quando uma nova mensagem chega:

1. O webhook recebe a mensagem enviada pela Evolution API.
2. A mensagem é processada.
3. O histórico da conversa é atualizado.
4. O histórico é convertido para o formato esperado pela OpenAI.
5. A IA gera uma resposta utilizando o contexto da conversa.
6. A resposta é salva.
7. A resposta é enviada ao usuário pelo WhatsApp.

---

## Instalação

Clone o projeto

```bash
git clone https://github.com/devthayron/chatbot.git

cd chatbot
```

Crie o ambiente virtual

```bash
python -m venv venv
```

Linux

```bash
source venv/bin/activate
```

Windows

```powershell
venv\Scripts\activate
```

Instale as dependências

```bash
pip install -r requirements.txt
```

---

## Configuração

Crie um arquivo `.env`

```env
OPENAI_API_KEY=

BASE_URL=
INSTANCE=
API_KEY_EVO=
```

---

## Executando

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

```
http://localhost:8000
```

---

## Exemplo de conversa armazenada

```json
{
  "number": "5599999999999",
  "push_name": "João",
  "messages": [
    {
      "from_me": false,
      "message": "Olá",
      "message_type": "conversation",
      "timestamp": 1783083116
    },
    {
      "from_me": true,
      "message": "Olá! Como posso ajudar você?",
      "message_type": "conversation",
      "timestamp": 1783083150
    }
  ]
}
```

---

## Próximos passos

- Banco de dados (PostgreSQL)
- Memória de longo prazo
- Suporte a múltiplas instâncias
- Painel administrativo
- Testes automatizados

---

## Autor

**Thayron Higlânder Santos**

- LinkedIn: https://www.linkedin.com/in/thayron-higlander