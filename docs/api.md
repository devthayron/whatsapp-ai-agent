# API

Guia para quem consome a API (front-end, integrações e ferramentas de IA). A documentação interativa é gerada pela FastAPI.

| Recurso      | URL                                  |
| ------------ | ------------------------------------ |
| Swagger UI   | `{BASE_URL}/docs`                    |
| ReDoc        | `{BASE_URL}/redoc`                   |
| OpenAPI JSON | `{BASE_URL}/openapi.json`            |

`{BASE_URL}` é o endereço da API: `http://localhost:8000` em desenvolvimento ou o domínio informado pela equipe em produção.

> O `openapi.json` descreve o corpo de cada requisição, o formato das respostas e os erros possíveis de cada rota. Ele pode ser importado no Postman ou Insomnia, ou usado para gerar tipos e clientes automaticamente (ex.: `openapi-typescript`). Este guia complementa com o fluxo de autenticação e as regras de uso.

---

# Resumo para o front

1. A API aceita chamadas do navegador **somente** das origens liberadas em `CORS_ORIGINS`. Peça a liberação do seu endereço.
2. Em `login`, `refresh` e `logout`, envie **credenciais** (`credentials: "include"` no fetch, `withCredentials: true` no axios). Sem isso o navegador ignora o cookie.
3. O **access token** vem no corpo do login. Guarde **só em memória** e envie em `Authorization: Bearer <token>`.
4. O **refresh token** vem em um cookie `HttpOnly`. Você não o lê nem o guarda: o navegador cuida dele.
5. Ao abrir a página, chame `POST /auth/refresh`. Se der certo, a sessão foi restaurada; se der `401`, mostre o login.
6. Quando uma chamada retornar `401 Token expirado`, chame `/auth/refresh` **uma vez** e repita a chamada original **uma vez**.
7. O `/chat/` espera a IA responder e pode levar vários segundos: use indicador de carregamento e um timeout generoso (ex.: 60 s).
8. Não existe rota para listar o histórico. O front só envia uma mensagem e recebe a resposta dela.
9. Front e API devem estar no **mesmo site** (ex.: `app.exemplo.com` e `api.exemplo.com`, ou `localhost` com portas diferentes). Em domínios totalmente diferentes o navegador pode não enviar o cookie.

---

# Rotas

## Para o front

| Método | Rota                 | Autenticação       | Uso                                              |
| ------ | -------------------- | ------------------ | ------------------------------------------------ |
| POST   | `/auth/register`     | —                  | Cria uma conta                                   |
| POST   | `/auth/login`        | —                  | Login. Access token no corpo, refresh no cookie  |
| POST   | `/auth/refresh`      | Cookie do refresh  | Gera um novo access token                        |
| POST   | `/auth/logout`       | —                  | Apaga o cookie do refresh token                  |
| GET    | `/auth/me`           | Access token       | Dados da conta autenticada                       |
| POST   | `/chat/`             | Access token       | Conversa com o agente, sem WhatsApp              |

## Auxiliares e internas

| Método | Rota                 | Autenticação       | Uso                                              |
| ------ | -------------------- | ------------------ | ------------------------------------------------ |
| GET    | `/`                  | —                  | Verifica se a API está no ar                     |
| POST   | `/auth/login-oauth2` | —                  | Login do botão Authorize do Swagger (sem cookie) |
| POST   | `/webhook/`          | `X-Webhook-Secret` | **Uso interno** (Evolution API). Não use no front|

---

# Tipos (TypeScript)

Referência rápida dos formatos de requisição e resposta. Equivalem aos schemas do `openapi.json`, que é a fonte oficial: se houver divergência, vale o `openapi.json`.

```ts
// Requisições
interface RegisterRequest { name?: string | null; email: string; password: string }
interface LoginRequest { email: string; password: string }
interface ChatRequest {
  number: string;                    // só dígitos, com DDI, sem "+" (ex.: "5511999999999")
  content: string;
  name?: string | null;
  external_id?: string | null;       // evita duplicidade
  content_type?: string;             // padrão "text"
  timestamp?: number | string | null; // epoch ou data ISO 8601
}

// Respostas
interface MessageResponse { message: string }
interface TokenResponse { access_token: string; token_type: "bearer" }
interface MeResponse { id: number; name: string | null; email: string; is_active: boolean }

type ChatResponse =
  | { status: "processed"; response: string }
  | { status: "duplicate"; response: null }
  | { status: "failed"; response: string; retry: boolean };

// Erros
interface ApiError { detail: string }
interface ValidationError {
  detail: { type: string; loc: (string | number)[]; msg: string; input?: unknown }[];
}
```

---

# Autenticação

## Os dois tokens

| Token         | Validade   | Onde fica                          | Uso                                         |
| ------------- | ---------- | ---------------------------------- | ------------------------------------------- |
| Access token  | 30 minutos | Corpo da resposta do login → memória do front | Enviado em toda chamada protegida |
| Refresh token | 7 dias     | Cookie `HttpOnly` (gerenciado pelo navegador) | Usado só em `/auth/refresh`         |

Detalhes do cookie:

* Nome: `refresh_token`
* `HttpOnly`: o JavaScript não consegue lê-lo
* `Path=/auth`: só é enviado para rotas `/auth/*`, nunca para `/chat/`
* `Secure`: ativo em produção (HTTPS)
* `SameSite`: `lax` por padrão

## Fluxo

```text
Login ─► access token (corpo) + refresh token (cookie)
   │
   ▼
Chamadas com Authorization: Bearer <access token>
   │
   │ 401 "Token expirado"
   ▼
POST /auth/refresh (cookie enviado automaticamente) ─► novo access token
   │
   ▼
Repete a chamada original (uma vez)
   │
   │ /auth/refresh retornou 401
   ▼
Sessão encerrada ─► tela de login
```

## Uso recomendado

* **Ao abrir a página:** chame `/auth/refresh`. O access token vive só em memória e some ao recarregar; o cookie permanece. Se o refresh der certo, a pessoa continua logada.
* **Renove sob demanda:** só quando o access token vencer (ou pouco antes, se o front ler o horário de expiração do token). Não renove a cada requisição.
* **Uma renovação por vez:** se várias requisições falharem juntas, faça apenas uma chamada a `/auth/refresh` e reaproveite o resultado.
* **Sem loop:** após renovar, repita a chamada original uma vez. Se falhar de novo, trate como erro.
* **Diferencie os `401`:** `Token expirado` pede renovação. `Token inválido`, `Tipo de token inválido` e `Conta inválida` são problemas reais: renovar não resolve.
* **Armazenamento:** o access token fica só em memória (não use `localStorage`). O refresh token nem passa pelo seu código.
* **Nunca** coloque tokens em URLs, logs ou repositórios.
* **Logout:** chame `/auth/logout` e descarte o access token da memória.
* **Integrações servidor a servidor** (sem navegador): crie uma conta dedicada por integração. O cookie é enviado como qualquer header `Cookie`, e a conta pode ser desativada sem afetar as demais.

## O que a API não faz

* **O refresh não renova o refresh token.** Ele vale 7 dias a partir do login; depois, é preciso novo login.
* **Não há revogação.** O logout só apaga o cookie do navegador; o token continua válido até vencer. Para bloquear um acesso, desative a conta (`is_active=false`): a API confere isso a cada requisição.
* **Trocar o `SECRET_KEY` invalida todos os tokens.**

---

# Detalhe das rotas

## POST `/auth/register`

Corpo: `RegisterRequest`. Não retorna token: depois do cadastro, faça login.

**200:** `{ "message": "Conta criada com sucesso" }`

**Erros:** `400` email já cadastrado · `422` corpo inválido

```bash
curl -X POST {BASE_URL}/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria","email":"maria@exemplo.com","password":"senha-forte-123"}'
```

---

## POST `/auth/login`

Corpo: `LoginRequest`. Deve ser chamado com credenciais habilitadas.

**200:** `TokenResponse` no corpo + cabeçalho `Set-Cookie: refresh_token=...; HttpOnly; Path=/auth`

```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

**Erros:** `401` email ou senha incorretos · `403` conta desativada · `422` corpo inválido

```bash
curl -i -c cookies.txt -X POST {BASE_URL}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"maria@exemplo.com","password":"senha-forte-123"}'
```

---

## POST `/auth/refresh`

Sem corpo e sem header de autorização: lê o cookie `refresh_token`. Deve ser chamado com credenciais habilitadas.

**200:** `TokenResponse`

**Erros**

| Status | Detalhe                  | Causa                                              |
| ------ | ------------------------ | -------------------------------------------------- |
| 401    | `Refresh token ausente`  | Cookie não enviado, expirado ou apagado            |
| 401    | `Tipo de token inválido` | O cookie não contém um refresh token               |
| 401    | `Token expirado`         | Refresh vencido: faça login de novo                |
| 401    | `Token inválido`         | Token malformado ou assinatura incorreta           |
| 401    | `Conta inválida`         | A conta não existe mais                            |
| 403    | `Conta desativada`       | Conta inativa                                      |

```bash
curl -b cookies.txt -X POST {BASE_URL}/auth/refresh
```

---

## POST `/auth/logout`

Apaga o cookie do refresh token. Não exige autenticação e não revoga o token no servidor.

**200:** `{ "message": "Sessão encerrada" }`

```bash
curl -b cookies.txt -c cookies.txt -X POST {BASE_URL}/auth/logout
```

---

## GET `/auth/me`

Header: `Authorization: Bearer <access token>`

**200:** `MeResponse`

```json
{ "id": 1, "name": "Maria", "email": "maria@exemplo.com", "is_active": true }
```

**Erros:** `401` · `403` conta desativada

---

## POST `/chat/`

Envia uma mensagem ao agente e devolve a resposta na própria requisição.

* É uma rota de **teste e integração**. O fluxo real de produção é o WhatsApp.
* A resposta **não** é enviada pelo WhatsApp.
* **Sem debounce:** cada chamada gera uma resposta.
* O `number` é só um identificador livre da conversa: **não** é vinculado à conta logada. Qualquer conta autenticada pode conversar como qualquer número.
* A conversa é salva e usa as últimas 30 mensagens do `number` como contexto.
* O número deve ter só dígitos, com DDI e sem `+`. A API não valida o formato.

Header: `Authorization: Bearer <access token>` · Corpo: `ChatRequest` · Resposta: `ChatResponse`

O HTTP é `200` mesmo quando o processamento falha. Sempre confira o campo `status`. O campo `retry` só aparece quando `status` é `failed`:

| `status`    | Significado                               | Exemplo                                                                         |
| ----------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| `processed` | Resposta gerada e salva                   | `{"status":"processed","response":"Olá! Tudo bem?"}`                            |
| `duplicate` | `external_id` já foi processado           | `{"status":"duplicate","response":null}`                                        |
| `failed`    | A IA falhou ou a resposta não foi salva   | `{"status":"failed","response":"Desculpe, não consegui...","retry":false}`      |

**Erros:** `401` · `403` · `422` (falta `number` ou `content`)

```bash
curl -X POST {BASE_URL}/chat/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number":"5511999999999","name":"Fulano","content":"Olá!"}'
```

Para testar o contexto, use o mesmo `number`: `"meu nome é João"` e depois `"qual é meu nome?"`.

---

## GET `/`

```json
{ "status": "online" }
```

---

## POST `/auth/login-oauth2`

Mesmo login, em formulário (`application/x-www-form-urlencoded`) com `username` (o email) e `password`. Retorna só `TokenResponse` e **não grava cookie**. Existe para o botão **Authorize** do Swagger; o front não deve usá-la.

---

## POST `/webhook/` (uso interno)

Chamada pela Evolution API, não pelo front. Configurada com `python -m integrations.evolution.setup_webhook`.

Header: `X-Webhook-Secret: <WEBHOOK_SECRET>` · Corpo: evento `messages.upsert`.

| Status | Quando                                                 |
| ------ | ------------------------------------------------------ |
| 200    | Mensagem enfileirada ou evento ignorado (corpo vazio)  |
| 401    | Segredo ausente ou incorreto                           |
| 500    | Erro inesperado ao enfileirar                          |

Ignorados com `200`: outros eventos, `fromMe`, grupos, mensagens que não são texto e duplicadas. A resposta ao usuário não vai no corpo: o worker a envia pela Evolution API quando a janela de debounce vence.

---

# Testar pelo Swagger

1. Abra `{BASE_URL}/docs`.
2. Crie uma conta em **POST /auth/register**.
3. Clique em **Authorize**, informe o **email** em `username` e a senha em `password` (deixe `client_id` e `client_secret` em branco).
4. Teste **POST /chat/** ou **GET /auth/me**.

Observações:

* Cada rota mostra no Swagger o exemplo de resposta e os erros possíveis (400, 401, 403).
* O **Authorize** usa `/auth/login-oauth2`, que não grava cookie. O access token expira em 30 minutos: se aparecer `Token expirado`, autorize de novo.
* Para testar o cookie, execute **POST /auth/login** pelo Swagger: o navegador guarda o cookie e **POST /auth/refresh** passa a funcionar na mesma aba. Isso exige `COOKIE_SECURE=false` em ambiente local sem HTTPS.

---


Exemplo mínimo e válido para `/chat/`:

```json
{
  "number": "559912345678",
  "name": "Thayron",
  "content": "oi, tudo bem?"
}
```

---

# Códigos de erro

| Status | Significado                                                                   |
| ------ | ----------------------------------------------------------------------------- |
| 200    | Sucesso (em `/chat/`, confira também `status`)                                |
| 400    | Requisição inválida (ex.: email já cadastrado)                                |
| 401    | Não autenticado, token inválido/expirado ou credenciais erradas               |
| 403    | Conta desativada                                                              |
| 422    | Corpo inválido (campo ausente ou tipo incorreto)                              |
| 500    | Erro interno inesperado                                                       |

Sem o header `Authorization` em rota protegida, o `401` vem com `{"detail": "Not authenticated"}`.

Erros `422` seguem o padrão da FastAPI:

```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "content"], "msg": "Field required" }
  ]
}
```

---

# Configuração do servidor (referência)

Variáveis que afetam quem consome a API:

| Variável                    | Padrão                  | Efeito                                                          |
| --------------------------- | ----------------------- | --------------------------------------------------------------- |
| CORS_ORIGINS                | `http://localhost:3000` | Origens do front liberadas (separadas por vírgula)              |
| COOKIE_SECURE               | `false`                 | `true` em produção: o cookie só trafega por HTTPS               |
| COOKIE_SAMESITE             | `lax`                   | `lax`, `strict` ou `none` (`none` exige `COOKIE_SECURE=true`)   |
| COOKIE_DOMAIN               | vazio                   | Domínio do cookie (ex.: `.exemplo.com` para compartilhar entre subdomínios) |
| ACCESS_TOKEN_EXPIRE_MINUTES | `30`                    | Validade do access token                                        |
| REFRESH_TOKEN_EXPIRE_DAYS   | `7`                     | Validade do refresh token e do cookie                           |