# Agente de IA para WhatsApp

Agente de IA integrado ao WhatsApp via Evolution API. Recebe mensagens por webhook, agrupa mensagens enviadas em sequência (debounce), usa o histórico salvo no banco como contexto e responde com modelos da OpenAI (LangChain).

[![Watch a one-minute video tour of whatsapp-ai-agent](https://gitdiagram.com/video-badge.svg)](https://gitdiagram.com/devthayron/whatsapp-ai-agent/video)

---

# Funcionalidades

* Webhook protegido por segredo (`X-Webhook-Secret`)
* Identificação automática de usuários pelo número
* Histórico persistente no PostgreSQL (contexto das últimas 30 mensagens)
* Debounce com Redis: mensagens em sequência geram uma única resposta
* Worker com concorrência, lease e novas tentativas
* Controle de mensagens duplicadas
* Fallback de resposta direta se o Redis estiver fora do ar
* Autenticação JWT: access token no corpo e refresh token em cookie `HttpOnly`
* CORS configurável para o front-end
* API documentada no Swagger, com formato das respostas e dos erros
* Migrações com Alembic
* Logs em console e arquivo (sem conteúdo das mensagens)
* Testes com Pytest

---

# Fluxo

```text
WhatsApp → Evolution API → Webhook → Parser
    → Identificar/criar usuário → Salvar mensagem (PostgreSQL)
    → Janela de debounce (Redis) → Worker
    → Histórico → IA (OpenAI) → Enviar no WhatsApp → Salvar resposta
```

Só são processadas mensagens de **texto** em **conversas individuais**. Grupos, áudios, imagens, figurinhas, reações e mensagens enviadas pela própria conta são ignorados.

---

# Estrutura

```text
whatsapp-ai-agent/
├── app/
│   ├── main.py                  # app, CORS, rotas e worker
│   ├── worker.py                # worker de debounce
│   ├── routes/                  # auth, chat, webhook_evolution
│   └── schemas/                 # message, user, responses
├── agent/                       # model, processor, prompt
├── cache/                       # client (Redis), debounce
├── core/security.py             # criação de tokens JWT
├── integrations/
│   ├── messaging.py             # seleção do provedor
│   └── evolution/               # client, parser, setup_webhook
├── database/                    # base, connection, models, users, conversations
├── migrations/                  # Alembic
├── tests/                       # agent, auth, conversations, parser, routes, users, worker
├── docs/                        # dev, database, api
├── config.py
├── dependencies.py              # sessão e autenticação
├── logger.py
└── requirements.txt
```

---

# Tecnologias

Python 3.12 · FastAPI · LangChain · OpenAI · Evolution API · SQLAlchemy · PostgreSQL · Redis · Alembic · PyJWT · Pytest

---

# Aviso

> A Evolution API não é oficial. O uso de automações pode violar os Termos de Serviço do WhatsApp e resultar em banimento da conta. Em produção, avalie a API oficial (Meta). O provedor é selecionado por `MESSAGING_PROVIDER`, o que facilita a troca.

---

# Instalação

```bash
git clone https://github.com/devthayron/whatsapp-ai-agent.git
cd whatsapp-ai-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

É necessário ter PostgreSQL e Redis disponíveis. Veja [docs/dev.md](docs/dev.md).

---

# Variáveis de ambiente

## Obrigatórias

| Variável       | Descrição                                                    |
| -------------- | ------------------------------------------------------------ |
| BASE_URL       | Endereço da Evolution API                                    |
| INSTANCE       | Nome da instância do WhatsApp                                |
| API_KEY_EVO    | Chave da Evolution API                                       |
| WEBHOOK_URL    | URL pública do webhook (ex.: `https://xxxx.ngrok-free.app/webhook/`) |
| WEBHOOK_SECRET | Segredo enviado no header `X-Webhook-Secret`                 |
| SECRET_KEY     | Chave de assinatura dos tokens JWT (mínimo 32 caracteres)    |
| OPENAI_API_KEY | Chave da OpenAI                                              |
| DATABASE_URL   | URL do PostgreSQL (`postgresql+psycopg://user:senha@host:5432/db`) |

## Opcionais

| Variável                    | Padrão                     | Descrição                                        |
| --------------------------- | -------------------------- | ------------------------------------------------ |
| AI_PROVIDER                 | `openai`                   | Provedor do modelo                               |
| AI_MODEL                    | `gpt-5.4-nano`             | Modelo                                           |
| LOG_LEVEL                   | `DEBUG`                    | Nível de log                                     |
| ALGORITHM                   | `HS256`                    | Algoritmo do JWT                                 |
| ACCESS_TOKEN_EXPIRE_MINUTES | `30`                       | Validade do access token                         |
| REFRESH_TOKEN_EXPIRE_DAYS   | `7`                        | Validade do refresh token e do cookie            |
| COOKIE_SECURE               | `false`                    | `true` em produção (cookie só por HTTPS)         |
| COOKIE_SAMESITE             | `lax`                      | `lax`, `strict` ou `none` (`none` exige `COOKIE_SECURE=true`) |
| COOKIE_DOMAIN               | vazio                      | Domínio do cookie (ex.: `.exemplo.com`)          |
| CORS_ORIGINS                | `http://localhost:3000`    | Origens do front liberadas, separadas por vírgula|
| REDIS_URL                   | `redis://localhost:6379/0` | Endereço do Redis                                |
| DEBOUNCE_SECONDS            | `7`                        | Janela para agrupar mensagens                    |
| DEBOUNCE_LEASE_SECONDS      | `120`                      | Tempo máximo de retenção do usuário pelo worker  |
| DEBOUNCE_RETRY_SECONDS      | `15`                       | Intervalo entre tentativas                       |
| DEBOUNCE_MAX_ATTEMPTS       | `3`                        | Máximo de tentativas por ciclo                   |
| WORKER_IN_API               | `true`                     | Executa o worker dentro da API                   |
| WORKER_CONCURRENCY          | `10`                       | Usuários processados em paralelo                 |
| MESSAGING_PROVIDER          | `evolution`                | Provedor de mensagens                            |

Gerar uma `SECRET_KEY` segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

# Documentação

| Documento                            | Conteúdo                                                  |
| ------------------------------------ | --------------------------------------------------------- |
| [docs/dev.md](docs/dev.md)           | Ambiente local, execução, webhook, worker e front         |
| [docs/database.md](docs/database.md) | Tabelas, campos, índices e migrações                      |
| [docs/api.md](docs/api.md)           | Rotas, Swagger, tipos e uso dos tokens                    |

Swagger: `http://localhost:8000/docs`

---

# Testes

```bash
python -m pytest -v
```

Usam SQLite em memória e mocks para IA, Redis e Evolution API. Não precisam de serviços externos.

---

# Próximos passos

* Rota para consultar o histórico de conversas
* RAG com documentos
* Docker
* Dashboard administrativo
* Múltiplos modelos de IA
* API oficial do WhatsApp (Meta)
* Áudio e imagem
* Memória de longo prazo

---

# Autor

**Thayron Higlânder** – [LinkedIn](https://www.linkedin.com/in/thayron-higlander)