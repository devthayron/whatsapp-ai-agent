# Ambiente de desenvolvimento

A API FastAPI, o PostgreSQL e o Redis rodam localmente. O `ngrok` expõe o webhook para a Meta, que só **recebe** e **envia** mensagens pela Cloud API.

```text
WhatsApp → Meta (Cloud API) → ngrok → FastAPI (local)
                                         ├─ Redis (debounce)
                                         ├─ PostgreSQL (histórico)
                                         └─ OpenAI (respostas)

Front-end (navegador) → FastAPI (CORS + cookie do refresh token)
```

---

# Pré-requisitos

* Python 3.12
* PostgreSQL e Redis
* ngrok
* App na Meta com o produto WhatsApp (veja [Configurando a Meta](../README.md#configurando-a-meta))
* Chave da OpenAI

PostgreSQL e Redis via Docker:

```bash
docker run -d --name chatbot-postgres \
  -e POSTGRES_USER=chatbot -e POSTGRES_PASSWORD=SUA_SENHA -e POSTGRES_DB=chatbot \
  -p 5432:5432 postgres:16

docker run -d --name chatbot-redis -p 6379:6379 redis:7
```

---

# Configuração

Copie `.env.example` para `.env`. A lista completa de variáveis está no [README](../README.md#variáveis-de-ambiente). As principais:

```env
DATABASE_URL=postgresql+psycopg://chatbot:SUA_SENHA@localhost:5432/chatbot
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=uma-chave-com-pelo-menos-32-caracteres

META_ACCESS_TOKEN=...
META_PHONE_NUMBER_ID=...
META_APP_SECRET=...
META_VERIFY_TOKEN=...

# Front-end e cookie do refresh token
CORS_ORIGINS=http://localhost:3000
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

---

# Banco de dados

```bash
alembic upgrade head
```

Ao alterar os modelos:

```bash
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

Revise a migração gerada antes de aplicar. Detalhes em [database.md](database.md).

---

# Executando

**Terminal 1: API**

```bash
uvicorn app.main:app --reload
```

Swagger em `http://localhost:8000/docs`.

**Terminal 2: ngrok**

```bash
ngrok http 8000
```

**Cadastro do webhook na Meta**

No painel do app (WhatsApp → Configuration → Webhook), informe:

* Callback URL: `https://xxxx.ngrok-free.app/webhook/meta`
* Verify token: o valor de `META_VERIFY_TOKEN`
* Assine o campo `messages`

A Meta chama `GET /webhook/meta` para verificar. A API precisa estar no ar **antes** de clicar em "Verify and save".

A URL do ngrok muda a cada execução (conforme o plano). Quando mudar, atualize a Callback URL no painel. Não há script de cadastro: na Meta, isso é feito só pelo painel.

---

# Worker de debounce

A cada mensagem, a janela do usuário é renovada no Redis. Quando vence (`DEBOUNCE_SECONDS`, padrão 7s), o worker busca o histórico, chama a IA e envia **uma** resposta.

| Modo                    | Configuração          | Comando                           |
| ----------------------- | ----------------------- | --------------------------------- |
| Dentro da API (padrão) | `WORKER_IN_API=true`  | `uvicorn app.main:app --reload` |
| Processo separado       | `WORKER_IN_API=false` | `python -m app.worker`          |

O processo separado usa sinais Unix: funciona em Linux/macOS. No Windows, use o modo dentro da API.

Comportamento:

* **Lease:** o worker reserva o usuário por `DEBOUNCE_LEASE_SECONDS`. Se cair, outro ciclo assume.
* **Ack:** o usuário só sai da fila se nenhuma mensagem nova chegou durante o processamento.
* **Retry:** só ocorre quando o usuário não recebeu nada (falha no envio, ou falha da IA e do fallback). Até `DEBOUNCE_MAX_ATTEMPTS`, a cada `DEBOUNCE_RETRY_SECONDS`.
* **Sem retry:** se algo já foi entregue (resposta ou mensagem de erro), para não duplicar.
* **Redis fora do ar:** o webhook responde direto, sem debounce.

---

# Contexto das conversas

A IA recebe as últimas **30 mensagens** (usuário + IA) do banco.

* Usuário novo começa sem contexto.
* A mensagem de erro padrão enviada quando a IA falha não entra no histórico.
* Para testar: envie `"meu nome é João"` e depois `"qual é meu nome?"`.
* Para recomeçar, apague as mensagens do usuário (ou o banco).

---

# Front-end: CORS e cookie

O refresh token é gravado em um cookie `HttpOnly` e o navegador só aceita chamadas de outro endereço se a API liberar a origem.

* **`CORS_ORIGINS`:** liste as origens exatas do front, separadas por vírgula. Com cookies não vale `*`.
* **Mesmo site:** front e API devem estar no mesmo site (`localhost:3000` e `localhost:8000` contam como o mesmo site; em produção, `app.exemplo.com` e `api.exemplo.com`). Com `SameSite=lax`, domínios totalmente diferentes não recebem o cookie.
* **Desenvolvimento:** `COOKIE_SECURE=false`, pois o cookie `Secure` só trafega por HTTPS.
* **Produção:** `COOKIE_SECURE=true` e `CORS_ORIGINS` com o endereço real do front.
* **Prefixo de URL:** o cookie usa `path=/auth`. Se a API ficar atrás de um prefixo (ex.: `/api`), ajuste `REFRESH_COOKIE_PATH` em `app/routes/auth.py`.
* O front precisa enviar credenciais em `login`, `refresh` e `logout` (`credentials: "include"`).

Fluxo completo e tipos das respostas em [api.md](api.md).

---

# Testar sem WhatsApp

Use `POST /chat/` com um access token, direto no Swagger ou por curl. Passo a passo e uso dos tokens em [api.md](api.md).

Erros comuns ao enviar o JSON pelo Swagger:

| Erro                                              | Causa                                                              |
| ------------------------------------------------- | ------------------------------------------------------------------ |
| `json_invalid` / `Expecting property name...` | Vírgula sobrando depois do último campo, ou aspas curvas/simples |
| `422` em `number`                             | `number` enviado sem aspas (precisa ser texto)                   |
| `401 Token expirado`                            | O access token dura 30 min: clique em **Authorize** de novo  |
| Mensagem salva com data de 1970                   | `timestamp: 0` (valor de exemplo do Swagger): remova o campo     |

---

# Problemas comuns com a Meta

| Sintoma                                        | Causa provável                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------------------ |
| "Verify and save" falha                        | API fora do ar, URL errada (falta `/webhook/meta`) ou `META_VERIFY_TOKEN` diferente |
| Mensagens não chegam                           | Campo `messages` não assinado, ou ngrok com URL antiga                         |
| `401` no webhook                               | `META_APP_SECRET` errado (a assinatura não confere)                            |
| Para de responder depois de ~24h               | Token temporário do painel expirou: use o token do System User                 |
| Erro ao enviar para um número                  | Número de teste: o destinatário precisa estar cadastrado no painel             |
| Erro ao enviar depois de um tempo sem conversa | Janela de 24h expirada (texto livre só vale dentro dela)                       |

---

# Testes

```bash
python -m pytest -v
```

SQLite em memória e mocks de IA, Redis e Meta. Cobrem parser, usuários, conversas, agente, autenticação (login, refresh por cookie, logout), rotas, webhook da Meta e worker.

O `conftest.py` força `DATABASE_URL=sqlite://` e usa o banco de teste também em `dependencies.SessionLocal`, então os testes nunca tocam o PostgreSQL real.

Aviso `InsecureKeyLengthWarning` nos testes: o `SECRET_KEY` de teste tem menos de 32 bytes. É inofensivo, e some usando uma chave de teste mais longa no `conftest.py`.

---

# Logs

Console e `logs/app.log`. Controlados por `LOG_LEVEL` (padrão `DEBUG`; use `INFO` para reduzir). O conteúdo das mensagens nunca é registrado.

---

# Produção

* Domínio próprio com HTTPS (sem ngrok) e Callback URL atualizada no painel da Meta
* Token permanente de System User em `META_ACCESS_TOKEN`
* `COOKIE_SECURE=true`, `CORS_ORIGINS` com o endereço real do front e front e API no mesmo site
* `WORKER_IN_API=false`, com o worker em processo separado
* `SECRET_KEY` (32+ caracteres) longa e aleatória
* `LOG_LEVEL=INFO`
* PostgreSQL com backup; Redis e banco com acesso restrito
