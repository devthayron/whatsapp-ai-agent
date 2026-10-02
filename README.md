# Agente de IA para WhatsApp

Sistema de agente de IA integrado ao WhatsApp por meio da Evolution API, capaz de identificar usuários, armazenar o histórico das conversas, recuperar o contexto automaticamente e gerar respostas utilizando modelos da OpenAI.

---

# Visão geral do projeto

[![Watch a one-minute video tour of whatsapp-ai-agent](https://gitdiagram.com/video-badge.svg)](https://gitdiagram.com/devthayron/whatsapp-ai-agent/video)

---

# Funcionalidades

* Integração entre WhatsApp, Evolution API, OpenAI e banco de dados
* Recebimento e processamento de mensagens via webhook
* Identificação automática de usuários
* Armazenamento persistente das mensagens recebidas e enviadas
* Recuperação de contexto a partir do histórico salvo no banco
* Geração de respostas contextualizadas utilizando modelos da OpenAI (via LangChain)
* Controle de mensagens duplicadas
* Envio automático das respostas pelo WhatsApp
* Sistema de logs estruturado (console e arquivo)
* Testes automatizados com Pytest

---

# Memória das conversas

Quando um usuário envia uma mensagem:

1. A mensagem chega pelo WhatsApp através da Evolution API.
2. O sistema identifica (ou cria) o usuário pelo número do telefone.
3. A mensagem recebida é salva no banco de dados.
4. As últimas mensagens da conversa (limite de 30) são recuperadas do banco, em ordem cronológica.
5. Esse histórico é enviado ao modelo de IA como contexto.
6. A resposta gerada é salva no banco e enviada ao usuário pelo WhatsApp.

> O contexto é construído **exclusivamente** com as mensagens que passaram pela aplicação.

---

# Fluxo da aplicação

```text
WhatsApp
    │
    ▼
Evolution API
    │
    ▼
Webhook
    │
    ▼
Processamento da mensagem
    │
    ▼
Identificar/criar usuário
    │
    ▼
Salvar mensagem recebida
    │
    ▼
Recuperar histórico do banco
    │
    ▼
Agente de IA (LangChain)
    │
    ▼
Modelo OpenAI
    │
    ▼
Gerar resposta
    │
    ▼
Salvar resposta no banco de dados
    │
    ▼
Enviar resposta no WhatsApp
```

---

# Estrutura do projeto

```text
whatsapp-ai-agent/
├── app/                              # aplicação FastAPI
│   ├── main.py
│   ├── routes/
│   │   ├── chat.py
│   │   └── webhook_evolution.py
│   └── schemas/
│       └── chat.py
│
├── agent/                            # agente de IA
│   ├── model.py
│   ├── processor.py
│   └── prompt.py
│
├── integrations/
│   └── evolution/                    # integração com a Evolution API
│       ├── client.py
│       └── parser.py
│
├── database/                         # persistência e modelos
│   ├── connection.py
│   ├── models.py
│   ├── users.py
│   └── conversations.py
│
├── tests/                            # testes automatizados
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_conversations.py
│   ├── test_evolution_parser.py
│   ├── test_routes.py
│   └── test_users.py
│
├── docs/
│   └── dev.md
│
├── data/
│   └── conversations.db
│
├── logs/
│   └── app.log
│
├── config.py
├── logger.py
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Tecnologias

* Python 3.12
* FastAPI
* LangChain
* OpenAI API
* Evolution API
* SQLAlchemy
* SQLite

---

# Aviso

> **Importante:** este projeto utiliza a Evolution API para integração com o WhatsApp. O uso de automações pode violar os Termos de Serviço do WhatsApp e resultar em restrições ou banimento da conta utilizada.

Para ambientes de produção, avalie o uso da API oficial do WhatsApp quando aplicável.

---

# Banco de dados

SQLite é utilizado inicialmente para armazenar usuários e histórico das conversas.

```text
data/
└── conversations.db
```

> As tabelas são criadas automaticamente na inicialização (`create_all`), que **não altera** tabelas já existentes. Ao mudar o schema em `database/models.py`, apague `data/conversations.db` (ou aplique a migração manualmente) em ambiente de desenvolvimento.

---

# Tabelas

## Usuários (`users`)

| Campo  | Descrição               |
| ------ | ------------------------- |
| id     | Identificador do usuário |
| name   | Nome do contato           |
| number | Número do WhatsApp       |

---

## Mensagens (`messages`)

| Campo        | Descrição                                    |
| ------------ | ---------------------------------------------- |
| id           | Identificador interno                          |
| message_id   | Identificador único da mensagem               |
| user_id      | Usuário relacionado                           |
| role         | Origem da mensagem (`user` ou `assistant`) |
| content      | Conteúdo da mensagem                          |
| message_type | Tipo da mensagem                               |
| sent_at      | Data e hora da mensagem                        |

---

# Logging

Logs são registrados no console e em `logs/app.log`, com nível controlado pela variável `LOG_LEVEL` (padrão: `INFO`). Por privacidade, o conteúdo das mensagens nunca é registrado.

---

# Instalação

```bash
git clone https://github.com/devthayron/whatsapp-ai-agent.git

cd whatsapp-ai-agent

python -m venv venv

source venv/bin/activate            # linux/mac

# venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

---

# Configuração

Renomeie o `.env.example` para `.env` e preencha:

```env
OPENAI_API_KEY=sua_chave
BASE_URL=http://seu-servidor-evolution:8080
INSTANCE=nome_da_instancia
API_KEY_EVO=sua_api_key
LOG_LEVEL=INFO
AI_PROVIDER=openai
AI_MODEL=gpt-5.4-nano
```

## Variáveis de ambiente

| Variável      | Descrição                                      |
| -------------- | ------------------------------------------------ |
| OPENAI_API_KEY | Chave da OpenAI                                  |
| BASE_URL       | Endereço da Evolution API                       |
| INSTANCE       | Nome da instância do WhatsApp                   |
| API_KEY_EVO    | Chave de autenticação da Evolution API         |
| LOG_LEVEL      | Nível de log (`INFO`, `DEBUG`...)           |
| AI_PROVIDER    | Provedor do modelo (opcional, padrão`openai`) |
| AI_MODEL       | Modelo utilizado (opcional, padrão`gpt-5.4-nano`)    |

---

# Executando

As instruções para executar a aplicação e a configuração do ambiente de desenvolvimento estão disponíveis na:

[Documentação de desenvolvimento](docs/dev.md)

---

# Testes

O projeto possui testes automatizados utilizando **Pytest**.

Para executar todos os testes:

```bash
python -m pytest -v
```

---

# Próximos passos

* RAG com documentos
* Migração para PostgreSQL
* Dockerização da aplicação
* Dashboard administrativo
* Suporte a múltiplos modelos de IA
* Memória de longo prazo

---

# Autor

- **Thayron Higlânder** – [LinkedIn](https://www.linkedin.com/in/thayron-higlander)
