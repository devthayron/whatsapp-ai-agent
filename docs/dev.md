# Ambiente de desenvolvimento

A aplicação FastAPI é executada localmente e o webhook é exposto à internet utilizando o ngrok, permitindo que a Evolution API envie eventos para a aplicação.

A Evolution API pode ser executada em diferentes ambientes:

- **VPS:** mais próximo de um ambiente de produção.
- **Máquina local:** ideal para testes.
- **Outros serviços de hospedagem:** conforme a necessidade do projeto.

Neste projeto, a Evolution API está hospedada em uma **VPS**, enquanto a aplicação FastAPI é executada localmente.

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

A documentação interativa da API estará disponível em:

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

---

# Ambiente de produção

Em produção, a aplicação pode ser executada em uma VPS ou outro serviço de hospedagem, eliminando a necessidade do ngrok.

Fluxo:

```text
WhatsApp
    │
    ▼
Evolution API (VPS)
    │
    ▼
FastAPI (VPS)
    │
    ▼
PostgreSQL
```

O PostgreSQL é recomendado para produção por oferecer:

- Melhor desempenho com grandes volumes de dados.
- Maior escalabilidade.
- Recursos avançados de segurança.
- Facilidade para backups e manutenção.

---

# Observação

O ngrok é utilizado apenas para expor temporariamente uma aplicação executada localmente. Em produção, o recomendado é utilizar um domínio próprio com HTTPS e hospedar todos os serviços em uma infraestrutura dedicada.

---

# Comparação dos ambientes

## Desenvolvimento

```text
Evolution API (VPS ou local)
        │
        ▼
      ngrok
        │
        ▼
 FastAPI (local)
        │
        ▼
      SQLite
```

## Produção

```text
Evolution API
        │
        ▼
     FastAPI
        │
        ▼
   PostgreSQL
```