# Ambiente de desenvolvimento

A aplicação FastAPI é executada localmente e utiliza o `ngrok` para expor o webhook à internet, permitindo que a `Evolution API` envie eventos para a aplicação.

A Evolution API pode ser executada em diferentes ambientes:

* **VPS:** mais próxima de um ambiente de produção.
* **Máquina local:** ideal para testes.
* **Outros serviços de hospedagem:** conforme a necessidade do projeto.

Neste projeto, a `Evolution API` está hospedada em uma **VPS**, enquanto a aplicação FastAPI é executada localmente.

A `Evolution API` é usada apenas para **receber** mensagens (webhook) e **enviar** respostas.

O `ngrok` é utilizado apenas para expor temporariamente uma aplicação local. Em produção, recomenda-se utilizar um domínio próprio com HTTPS e uma infraestrutura dedicada.

---

# Fluxo de desenvolvimento

```text
WhatsApp
    │
    ▼
Evolution API (VPS)
    │
    ▼
ngrok (URL pública)
    │
    ▼
FastAPI (computador local)
    │
    ▼
SQLite
```

---

# Executando a aplicação

## Terminal 1 — iniciar o FastAPI

```bash
uvicorn app.main:app --reload
```

A documentação da API estará disponível em:

```text
http://localhost:8000/docs
```

## Terminal 2 — criar um túnel público com o ngrok

```bash
ngrok http 8000
```

O ngrok irá gerar uma URL pública semelhante a:

```text
https://xxxx.ngrok-free.app
```

Configure essa URL como webhook na Evolution API:

```text
https://xxxx.ngrok-free.app/webhook/
```

> Dependendo da configuração utilizada, o ngrok pode gerar uma nova URL a cada execução.

---

# Banco de dados

O projeto utiliza SQLite durante o desenvolvimento por ser simples de configurar e não exigir um servidor dedicado.

O banco é armazenado localmente em:

```text
data/
└── conversations.db
```

As tabelas são criadas automaticamente ao iniciar a aplicação. O processo apenas cria tabelas que não existem e **nunca altera** tabelas existentes.

Ao alterar o schema em `database/models.py`, recrie o banco:

```bash
rm data/conversations.db
```

---

# Contexto das conversas

Atualemente o contexto enviado à IA vem exclusivamente do banco de dados: cada mensagem recebida e cada resposta enviada são salvas, e as últimas **30 mensagens da conversa, somando mensagens do usuário e da IA**, são recuperadas a cada nova interação.

Consequências:

* Um usuário novo começa com contexto vazio, mesmo que já tenha conversado com o número antes.
* Mensagens enviadas manualmente pelo celular da conta não são salvas (`fromMe` é ignorado).
* Para testar o contexto, envie mensagens em sequência, como: `"meu nome é João"` e depois `"qual é meu nome?"`.
* Para recomeçar do zero, apague o banco.

---

# Ambiente de produção

Em produção, a aplicação pode ser executada em uma VPS ou outro serviço de hospedagem, eliminando a necessidade do ngrok.

Também deve ser **avaliado o uso da API oficial do WhatsApp (Meta)**, conforme as necessidades do projeto.

Fluxo:

```text
WhatsApp
    │
    ▼
API oficial do WhatsApp (Meta)
    │
    ▼
FastAPI (VPS)
    │
    ▼
PostgreSQL
```

O PostgreSQL é uma opção adequada para produção por oferecer recursos de escalabilidade, segurança, backups e manutenção mais robustos que o SQLite em cenários maiores.

---
