# chatbot-evo

Script em Python para extrair o histórico de mensagens de uma instância do WhatsApp conectada via [Evolution API](https://doc.evolution-api.com/), organizar as conversas por contato e salvar tudo em um arquivo JSON.

## O que ele faz

- Busca as mensagens registradas em uma instância da Evolution API (`/chat/findMessages/{instance}`).
- Filtra apenas mensagens de texto (`conversation`), ignorando outros tipos (imagem, áudio, etc.).
- Agrupa as mensagens por número de contato.
- Salva o resultado em `{instance}_historico_msg.json`.

## Estrutura do projeto

```
chatbot-evo/
├── main.py                # ponto de entrada, orquestra o fluxo
├── config.py               # variáveis de ambiente, headers e sessão HTTP
├── services/
│   └── evolution.py        # chamadas à Evolution API
├── bot/
│   └── messages.py         # processamento e agrupamento das mensagens
├── requirements.txt
├── .env.example
└── .gitignore
```

## Pré-requisitos

- Python 3.10+
- Uma instância ativa na Evolution API, com a `apikey` e a URL base em mãos

## Instalação

```bash
git clone https://github.com/devthayron/chatbot-evo.git
cd chatbot-evo

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Configuração

Copie o `.env.example` para `.env` e preencha com os dados da sua instância:

```bash
cp .env.example .env
```

```env
BASE_URL=http://seu-servidor-evolution:8080
API_KEY_EVO=sua_api_key_aqui
INSTANCE=nome_da_sua_instancia
```

| Variável       | Descrição                                              |
|----------------|----------------------------------------------------------|
| `BASE_URL`     | URL base do seu servidor da Evolution API                |
| `API_KEY_EVO`  | API key de autenticação da instância                      |
| `INSTANCE`     | Nome da instância cujas mensagens serão buscadas           |

## Uso

```bash
python main.py
```

Saída esperada no terminal:

```
Mensagens processadas: 21
Mensagens ignoradas: 1
Contatos encontrados: 2
Histórico salvo em: guara_historico_msg.json
```

O arquivo `{instance}_historico_msg.json` é gerado na raiz do projeto com o seguinte formato:

```json
{
  "5599999999999": {
    "push_name": "João",
    "messages": [
      { "from_me": false, "message": "opa", "message_type": "conversation", "timestamp": 1783083116 },
      { "from_me": true, "message": "Iae", "message_type": "conversation", "timestamp": 1783083075 }
    ]
  }
}
```
 
*`from_me: false` → mensagem enviada pelo contato (João). `from_me: true` → mensagem enviada por você.*
 
> `push_name` sempre reflete o nome do **contato**. Se o contato ainda não te respondeu, o campo fica `null`.

## Roadmap

- [ ] Suporte a outros tipos de mensagem (imagem, áudio, documento)
- [ ] Envio de mensagens automáticas (`URL_SEND_MESSAGES` já está mapeada em `config.py`, mas ainda não é usada)
- [ ] Integração com api da OPENAI
- [ ] Criação do chatbot
- [ ] Testes automatizados


## Autor

- **Thayron Higlânder** – [LinkedIn](https://www.linkedin.com/in/thayron-higlander) 
