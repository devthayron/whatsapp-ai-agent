# Banco de dados

* **SGBD:** PostgreSQL (`psycopg`)
* **ORM:** SQLAlchemy 2.x
* **Migrações:** Alembic
* **Conexão:** `DATABASE_URL`

```env
DATABASE_URL=postgresql+psycopg://chatbot:SUA_SENHA@localhost:5432/chatbot
```

Nos testes, o banco é SQLite em memória (forçado no `conftest.py`). O PostgreSQL real nunca é usado.

---

# Diagrama

```mermaid
erDiagram
    USERS ||--o{ MESSAGES : possui

    USERS {
        int id PK
        string name
        string number UK
    }
    MESSAGES {
        int id PK
        string external_id UK
        int user_id FK
        string role
        string content
        string content_type
        datetime sent_at
    }
    ACCOUNTS {
        int id PK
        string name
        string email UK
        string hashed_password
        bool is_active
    }
```

`accounts` não se relaciona com `users`: **contas** acessam a API; **usuários** são os contatos do WhatsApp.

---

# Campos comuns

Todas as tabelas têm:

| Campo      | Tipo          | Descrição                                   |
| ---------- | ------------- | ------------------------------------------- |
| created_at | `TIMESTAMPTZ` | Criação do registro (UTC), automático       |
| updated_at | `TIMESTAMPTZ` | Última alteração (UTC), automático          |

---

# `users`

Contatos do WhatsApp, criados na primeira mensagem de um número.

| Campo  | Tipo          | Nulo | Chave           | Descrição                                   |
| ------ | ------------- | ---- | --------------- | ------------------------------------------- |
| id     | `INTEGER`     | Não  | PK              | Identificador                               |
| name   | `VARCHAR`     | Sim  | —               | Nome do contato (`pushName`)                |
| number | `VARCHAR(20)` | Não  | Único, indexado | Número só com dígitos (`5511999999999`)     |

* O sufixo `@s.whatsapp.net` é removido antes de salvar.
* Se chegar um nome diferente, `name` é atualizado; nome vazio mantém o atual.
* Excluir um usuário exclui suas mensagens (cascade).

---

# `messages`

Histórico: mensagens do usuário e respostas da IA.

| Campo        | Tipo          | Nulo | Chave                      | Descrição                                         |
| ------------ | ------------- | ---- | -------------------------- | ------------------------------------------------- |
| id           | `INTEGER`     | Não  | PK                         | Identificador (define a ordem do histórico)       |
| external_id  | `VARCHAR`     | Sim  | Único, indexado            | Id no provedor, ex.: `evolution_3EB0A1B2C3`       |
| user_id      | `INTEGER`     | Não  | FK → `users.id`, indexado  | Dono da conversa                                  |
| role         | `VARCHAR`     | Não  | —                          | `user` ou `assistant`                             |
| content      | `VARCHAR`     | Não  | —                          | Texto                                             |
| content_type | `VARCHAR`     | Não  | —                          | Atualmente só `text`                              |
| sent_at      | `TIMESTAMPTZ` | Não  | Indexado                   | Data e hora da mensagem                           |

Regras:

* **Duplicidade:** `external_id` único impede gravar a mesma mensagem duas vezes. O prefixo (`evolution_`) evita colisão entre provedores.
* **Sem id do provedor:** `external_id` fica `NULL` e não há deduplicação. Respostas da IA também usam `NULL`.
* **`sent_at`:** usa o timestamp da mensagem, ou o horário atual se não houver. Valores numéricos são convertidos para `America/Sao_Paulo`.
* **Resposta da IA** só é salva depois de enviada.
* A **mensagem de erro padrão** não é salva.

---

# `accounts`

Contas de acesso à API.

| Campo           | Tipo      | Nulo | Chave           | Descrição                                   |
| --------------- | --------- | ---- | --------------- | ------------------------------------------- |
| id              | `INTEGER` | Não  | PK              | Identificador                               |
| name            | `VARCHAR` | Sim  | —               | Nome                                        |
| email           | `VARCHAR` | Não  | Único, indexado | Email de login                              |
| hashed_password | `VARCHAR` | Não  | —               | Hash da senha (a senha nunca é guardada)    |
| is_active       | `BOOLEAN` | Não  | —               | Padrão `true`. Inativa = `403` e bloqueia tokens já emitidos |

Os tokens JWT (access e refresh) **não** são guardados no banco: são validados pela assinatura (`SECRET_KEY`) e, a cada requisição, pela consulta à conta (existe e está ativa). Por isso não há tabela de sessões nem revogação individual de token.

---

# Histórico da conversa

```sql
SELECT * FROM messages
WHERE user_id = :user_id
ORDER BY id DESC
LIMIT 30;
```

O resultado é invertido para ordem cronológica. O limite está em `CONTEXT_MESSAGES_LIMIT` (`database/conversations.py`).

Conversas cujo último registro é do usuário (possivelmente sem resposta):

```sql
SELECT u.number, m.content, m.sent_at
FROM users u
JOIN LATERAL (
    SELECT * FROM messages WHERE user_id = u.id ORDER BY id DESC LIMIT 1
) m ON TRUE
WHERE m.role = 'user';
```

---

# Redis

Não guarda conversas, só coordena o debounce. Se for limpo, nenhuma mensagem se perde.

| Chave               | Tipo | Conteúdo                                                      |
| ------------------- | ---- | ------------------------------------------------------------- |
| `debounce:due`      | ZSET | `user_id` → momento em que a janela (ou o lease) vence        |
| `debounce:attempts` | HASH | `user_id` → tentativas falhas do ciclo atual                  |

---

# Migrações

| Comando                                          | Ação                              |
| ------------------------------------------------ | --------------------------------- |
| `alembic upgrade head`                           | Aplica as migrações pendentes     |
| `alembic revision --autogenerate -m "descrição"` | Gera migração a partir dos modelos|
| `alembic downgrade -1`                           | Reverte a última                  |
| `alembic current`                                | Mostra a versão atual             |

Para alterar o schema: edite `database/models.py` → gere a migração → **revise** → aplique → atualize este documento.


> Essa migração só altera tabelas existentes. Em um banco vazio, é preciso uma migração base que crie as tabelas.

---

# Boas práticas

* Faça backup: o banco é a única fonte do contexto da IA.
* Nunca registre o conteúdo das mensagens em logs.
* Em produção, use um usuário do banco com permissões mínimas.