# Chatbot WhatsApp com IA

Chatbot para WhatsApp desenvolvido em Python utilizando **FastAPI**, **Evolution API**, **OpenAI** e **SQLite**.

O projeto recebe mensagens através de um webhook da Evolution API, armazena o histórico das conversas em banco de dados, utiliza esse contexto para gerar respostas com a OpenAI e envia automaticamente a resposta ao usuário pelo WhatsApp.

---

## Funcionalidades

* Integração com a Evolution API
* Webhook para recebimento de mensagens
* Integração com a OpenAI
* Histórico das conversas em SQLite
* Construção automática do contexto enviado para a OpenAI
* Respostas automáticas pelo WhatsApp
* Estrutura modular para facilitar manutenção e escalabilidade

---

## Fluxo da aplicação

```text
WhatsApp
    |
    ▼
Evolution API
    |
    ▼
Webhook FastAPI
    |
    ▼
Processamento da mensagem
    |
    +------------+
    |            |
    ▼            ▼
SQLite       Contexto
(usuário)       |
                ▼
              OpenAI
                |
                ▼
          Resposta gerada
                |
                ▼
          Evolution API
                |
                ▼
            WhatsApp
```

---

## Estrutura do projeto

```text
chatbot/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── webhook.py
│   │   └── chat.py
│   └── schemas/
│       └── message.py
│
├── bot/
│   └── processor.py
│
├── services/
│   ├── chatbot.py          # fluxo principal do chatbot
│   ├── evolution.py        # integração com Evolution API
│   └── openai.py           # integração com OpenAI
│
├── database/
│   ├── database.py         # conexão com SQLite
│   ├── models.py           # modelos SQLAlchemy
│   └── conversations.py    # operações de persistência
│
├── data/
│   └── conversations.db
│
├── config.py
├── requirements.txt
└── README.md
```

---

## Tecnologias

* Python 3.12
* FastAPI
* OpenAI API
* Evolution API
* SQLAlchemy
* SQLite
* Uvicorn
* python-dotenv

---

## Como funciona

Quando uma nova mensagem chega pelo WhatsApp:

1. A Evolution API envia a mensagem para o webhook da aplicação.
2. O webhook processa a mensagem recebida.
3. A mensagem é salva no banco de dados.
4. O histórico da conversa é recuperado.
5. O histórico é convertido para o formato esperado pela OpenAI.
6. A OpenAI gera uma resposta utilizando o contexto completo da conversa.
7. A resposta é salva no banco.
8. A resposta é enviada ao usuário através da Evolution API.

---

## Instalação

Clone o projeto:

```bash
git clone https://github.com/devthayron/chatbot.git
cd chatbot
```

Crie o ambiente virtual:

```bash
python -m venv venv
```

Linux:

```bash
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=

BASE_URL=
INSTANCE=
API_KEY_EVO=
```

| Variável          | Descrição                    |
| ------------------ | ------------------------------ |
| `OPENAI_API_KEY` | Chave da API da OpenAI         |
| `BASE_URL`       | URL da Evolution API           |
| `INSTANCE`       | Nome da instância do WhatsApp |
| `API_KEY_EVO`    | API Key da Evolution API       |

---

## Executando

Inicie a aplicação:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://localhost:8000
```

A documentação automática pode ser acessada em:

```text
http://localhost:8000/docs
```

---

## Banco de dados

O histórico das conversas é armazenado automaticamente em um banco SQLite localizado em:

```text
data/
└── conversations.db
```
## Modelo de dados

O sistema utiliza **SQLite** para persistência inicial.

### Tabela: `users`

| Campo | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Identificador único do usuário |
| name | TEXT | Nome do usuário |
| number | TEXT | Número do WhatsApp |

### Tabela: `conversation`

| Campo | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Identificador único da conversa |
| user_id | INTEGER | Chave estrangeira para `usuarios.id` |
| role | TEXT | Origem da mensagem (`cliente` ou `bot`) |
| content | TEXT | Conteúdo da mensagem |
| type_message | TEXT | Tipo da mensagem (texto, imagem, áudio, etc.) |
| timestamp | DATETIME | Data e hora da mensagem |

### Relacionamento

| Origem | Destino | Cardinalidade |
|---------|---------|---------------|
| `user.id` | `conversation.user_id` | 1:N (um usuário possui várias conversas) |

Cada conversa é vinculada a um usuário, permitindo recuperar todo o histórico antes da geração de uma nova resposta pela IA.


---

## Próximos passos

* Suporte a múltiplas instâncias do WhatsApp
* Migração para PostgreSQL
* Memória de longo prazo
* Painel administrativo
* Testes automatizados
* logging para auditoria

---

## Autor

**Thayron Higlânder Santos**

* LinkedIn: https://www.linkedin.com/in/thayron-higlander
