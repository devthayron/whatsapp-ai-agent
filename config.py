import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY_EVO = os.getenv("API_KEY_EVO")
BASE_URL = os.getenv("BASE_URL")
INSTANCE = os.getenv("INSTANCE")


if not all([API_KEY_EVO, BASE_URL, INSTANCE]):
    raise RuntimeError("Variáveis de ambiente faltando. Verifique API_KEY_EVO, BASE_URL e INSTANCE no .env")


URL_GET_MESSAGES = f"{BASE_URL}/chat/findMessages/{INSTANCE}"
URL_SEND_MESSAGES = f"{BASE_URL}/message/sendText/{INSTANCE}"


HEADERS = {
    "apikey": API_KEY_EVO,
    "Content-Type": "application/json",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)