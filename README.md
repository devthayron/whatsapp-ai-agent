# Agente de IA para WhatsApp

Agente de IA integrado ao WhatsApp pela API oficial da Meta (WhatsApp Cloud API). Recebe mensagens por webhook, agrupa mensagens enviadas em sequência (debounce), usa o histórico salvo no banco como contexto e responde com modelos da OpenAI (LangChain).

---

# Funcionalidades

* Webhook da Meta com validação de assinatura (`X-Hub-Signature-256`) e handshake de verificação
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
WhatsApp → Meta (Cloud API) → Webhook → Parser
    → Identificar/criar usuário → Salvar mensagem (PostgreSQL)
    → Janela de debounce (Redis) → Worker
    → Histórico → IA (OpenAI) → Enviar pela Cloud API → Salvar resposta
```

Só são processadas mensagens de **texto**. Áudios, imagens, figurinhas, reações e eventos de status (entregue, lida) são ignorados.

---

# Estrutura

```text
whatsapp-ai-agent/
├── app/
│   ├── main.py                  # app, CORS, rotas e worker
│   ├── worker.py                # worker de debounce
│   ├── routes/                  # auth, chat, webhook_meta
│   └── schemas/                 # message, user, responses
├── agent/                       # model, processor, prompt
├── cache/                       # client (Redis), debounce
├── core/security.py             # criação de tokens JWT
├── integrations/
│   └── meta/                    # client, parser
├── database/                    # base, connection, models, users, conversations
├── migrations/                  # Alembic
├── tests/                       # agent, auth, conversations, meta (client, parser, webhook), routes, users, worker
├── docs/                        # dev, database, api
├── config.py
├── dependencies.py              # sessão e autenticação
├── logger.py
└── requirements.txt
```

---

# Tecnologias

Python 3.12 · FastAPI · LangChain · OpenAI · WhatsApp Cloud API (Meta) · SQLAlchemy · PostgreSQL · Redis · Alembic · PyJWT · Pytest

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

# Configurando a Meta

1. Em [developers.facebook.com](https://developers.facebook.com), crie um app do tipo **Business** e adicione o produto **WhatsApp**.
2. Em **WhatsApp → API Setup**, copie o **Phone number ID** (`META_PHONE_NUMBER_ID`).
3. Em **App settings → Basic**, copie o **App Secret** (`META_APP_SECRET`).
4. Escolha um texto qualquer como `META_VERIFY_TOKEN` (precisa ser o mesmo no `.env` e no painel).
5. Em **WhatsApp → Configuration → Webhook**, informe:
   * **Callback URL:** `https://seu-dominio/webhook/meta`
   * **Verify token:** o valor de `META_VERIFY_TOKEN`
   * Depois de verificar, assine o campo **`messages`**.
6. Token de acesso:
   * O token do painel **expira em 24 horas**: serve só para o primeiro teste.
   * Para produção, crie um **System User** em Business Settings, atribua o app e o número de WhatsApp com a permissão `whatsapp_business_messaging`, gere um token **sem expiração** e use em `META_ACCESS_TOKEN`.
7. Enquanto o número for o de teste da Meta, só é possível conversar com os números cadastrados como destinatários no painel.

Limitação da Cloud API: texto livre só pode ser enviado **dentro de 24 horas** após a última mensagem do usuário.

---

# Variáveis de ambiente

## Obrigatórias

| Variável             | Descrição                                                          |
| --------------------- | -------------------------------------------------------------------- |
| SECRET_KEY            | Chave de assinatura dos tokens JWT (mínimo 32 caracteres)           |
| OPENAI_API_KEY        | Chave da OpenAI                                                      |
| DATABASE_URL          | URL do PostgreSQL (`postgresql+psycopg://user:senha@host:5432/db`) |
| META_ACCESS_TOKEN     | Token de acesso da Cloud API (use o permanente em produção)         |
| META_PHONE_NUMBER_ID  | ID do número de WhatsApp no painel da Meta                           |
| META_APP_SECRET       | App Secret, usado para validar a assinatura do webhook               |
| META_VERIFY_TOKEN     | Token do handshake de cadastro do webhook                            |

## Opcionais

| Variável                   | Padrão                      | Descrição                                                             |
| --------------------------- | ---------------------------- | ----------------------------------------------------------------------- |
| META_API_VERSION            | `v23.0`                    | Versão da Graph API                                                     |
| AI_PROVIDER                 | `openai`                   | Provedor do modelo                                                      |
| AI_MODEL                    | `gpt-5.4-nano`             | Modelo                                                                  |
| LOG_LEVEL                   | `DEBUG`                    | Nível de log                                                           |
| ALGORITHM                   | `HS256`                    | Algoritmo do JWT                                                        |
| ACCESS_TOKEN_EXPIRE_MINUTES | `30`                       | Validade do access token                                                |
| REFRESH_TOKEN_EXPIRE_DAYS   | `7`                        | Validade do refresh token e do cookie                                   |
| COOKIE_SECURE               | `false`                    | `true` em produção (cookie só por HTTPS)                           |
| COOKIE_SAMESITE             | `lax`                      | `lax`, `strict` ou `none` (`none` exige `COOKIE_SECURE=true`) |
| COOKIE_DOMAIN               | vazio                        | Domínio do cookie (ex.:`.exemplo.com`)                               |
| CORS_ORIGINS                | `http://localhost:3000`    | Origens do front liberadas, separadas por vírgula                      |
| REDIS_URL                   | `redis://localhost:6379/0` | Endereço do Redis                                                      |
| DEBOUNCE_SECONDS            | `7`                        | Janela para agrupar mensagens                                           |
| DEBOUNCE_LEASE_SECONDS      | `120`                      | Tempo máximo de retenção do usuário pelo worker                     |
| DEBOUNCE_RETRY_SECONDS      | `15`                       | Intervalo entre tentativas                                              |
| DEBOUNCE_MAX_ATTEMPTS       | `3`                        | Máximo de tentativas por ciclo                                         |
| WORKER_IN_API               | `true`                     | Executa o worker dentro da API                                          |
| WORKER_CONCURRENCY          | `10`                       | Usuários processados em paralelo                                       |

Gerar uma `SECRET_KEY` segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

# Documentação

| Documento                           | Conteúdo                                           |
| ----------------------------------- | --------------------------------------------------- |
| [docs/dev.md](docs/dev.md)           | Ambiente local, execução, webhook, worker e front |
| [docs/database.md](docs/database.md) | Tabelas, campos, índices e migrações             |
| [docs/api.md](docs/api.md)           | Rotas, Swagger, tipos e uso dos tokens              |

Swagger: `http://localhost:8000/docs`

---

# Testes

```bash
python -m pytest -v
```

Usam SQLite em memória e mocks para IA, Redis e Meta. Não precisam de serviços externos.

---

# Próximos passos

* Rota para consultar o histórico de conversas
* RAG com documentos
* Docker
* Dashboard administrativo
* Múltiplos modelos de IA
* Áudio e imagem
* Memória de longo prazo

---

# Autor

**Thayron Higlânder** – [LinkedIn](https://www.linkedin.com/in/thayron-higlander)
