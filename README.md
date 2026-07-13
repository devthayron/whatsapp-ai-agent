# Agente de IA para WhatsApp

Sistema de agente de IA integrado ao WhatsApp por meio da Evolution API, capaz de identificar usuários, armazenar o histórico das conversas, recuperar o contexto automaticamente e gerar respostas utilizando modelos da OpenAI.

---

# Funcionalidades

* Integração entre WhatsApp, Evolution API, OpenAI e banco de dados
* Recebimento e processamento de mensagens via webhook
* Identificação automática de usuários
* Armazenamento persistente do histórico de conversas
* Importação automática do histórico existente no primeiro contato
* Recuperação de contexto para respostas mais precisas
* Geração de respostas contextualizadas utilizando modelos da OpenAI
* Controle de mensagens duplicadas
* Envio automático das respostas pelo WhatsApp

---

# Memória das conversas

Quando um usuário envia uma mensagem:

1. A mensagem chega pelo WhatsApp através da Evolution API.
2. O sistema identifica o usuário pelo número do telefone.
3. É verificado se já existe histórico desse usuário armazenado no banco de dados.
4. Caso exista, o histórico salvo é utilizado como contexto da conversa.
5. Caso seja o primeiro contato, o sistema importa automaticamente o histórico existente na Evolution API.
6. As mensagens encontradas são organizadas por data e armazenadas no banco.
7. Após a primeira importação, o histórico salvo passa a ser reutilizado nas próximas interações.

> A sincronização do histórico acontece apenas no primeiro contato de cada usuário, reduzindo consultas desnecessárias à Evolution API.

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
Identificar usuário
    │
    ▼
Verificar histórico
    │
    ├───────────────┐
    │               │
    ▼               ▼
Existe histórico  Primeiro contato
    │               │
    ▼               ▼
Usar histórico   Importar histórico
do banco         da Evolution API
    │               │
    └───────┬───────┘
            │
            ▼
 Recuperar contexto
            │
            ▼
     Agente de IA
            │
            ▼
     Modelo OpenAI
            │
            ▼
     Gerar resposta
            │
            ▼
 Salvar no banco de dados
            │
            ▼
Enviar resposta no WhatsApp
```

---

# Estrutura do projeto

```text
whatsapp-ai-agent/
├── app/
│   ├── main.py
│   └── routes/
│       ├── webhook.py
│       └── chat.py
│
├── bot/                                # aplicação e rotas da API
│   └── message_processor.py
│
├── services/                           # integrações e regras do sistema
│   ├── agent.py
│   ├── evolution.py
│   └── openai.py
│
├── database/                           # modelos e operações do banco de dados
│   ├── connection.py
│   ├── models.py
│   ├── users.py
│   └── conversations.py
│
├── data/                               # arquivos de dados da aplicação
│   └── conversations.db
│
├── config.py
├── requirements.txt
└── README.md
```

---

# Tecnologias

* Python 3.12
* FastAPI
* OpenAI API
* Evolution API
* SQLAlchemy
* SQLite

---

# Banco de dados

SQLite é utilizado inicialmente para armazenar usuários e histórico das conversas.

```text
data/
└── conversations.db
```

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

| Campo        | Descrição                                           |
| ------------ | ----------------------------------------------------- |
| id           | Identificador interno                                 |
| message_id   | Identificador único da mensagem                      |
| user_id      | Usuário relacionado                                  |
| role         | Origem da mensagem (`user` ou `assistant`)        |
| content      | Conteúdo da mensagem                                 |
| message_type | Origem da mensagem (Webhook, Evolution API ou OpenAI) |
| sent_at      | Data e hora da mensagem                               |

---

# Instalação

```bash
git clone https://github.com/devthayron/whatsapp-ai-agent.git

cd whatsapp-ai-agent

python -m venv venv

source venv/bin/activate            # linux/mac

# venv/scripts/activate             # Windows

pip install -r requirements.txt
```

---

# Configuração

Renomeie o `env.example` para `.env` e preencha:

```env
OPENAI_API_KEY=sua_chave
BASE_URL=http://seu-servidor-evolution:8080
INSTANCE=nome_da_instancia
API_KEY_EVO=sua_api_key
```

## Variáveis de ambiente

| Variável      | Descrição                              |
| -------------- | ---------------------------------------- |
| OPENAI_API_KEY | Chave da OpenAI                          |
| BASE_URL       | Endereço da Evolution API               |
| INSTANCE       | Nome da instância do WhatsApp           |
| API_KEY_EVO    | Chave de autenticação da Evolution API |

---

# Executando

As instruções para executar a aplicação e a configuração do ambiente de desenvolvimento estão disponíveis na:

[Documentação de desenvolvimento](docs/dev.md)


---

# Próximos passos

* Testes automatizados
* Sistema de logs
* Dockerização da aplicação
* Migração para PostgreSQL
* Dashboard administrativo
* RAG com documentos
* Suporte a múltiplos modelos de IA
* Memória de longo prazo

---

# Autor

- **Thayron Higlânder** – [LinkedIn](https://www.linkedin.com/in/thayron-higlander) 
