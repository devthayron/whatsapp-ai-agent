import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY_EVO = os.getenv("API_KEY_EVO")
BASE_URL = os.getenv("BASE_URL")

INSTANCE = "guara"

URL_GET_MESSAGES = f"{BASE_URL}/chat/findMessages/{INSTANCE}"
URL_SEND_MESSAGES = f"{BASE_URL}/message/sendText/{INSTANCE}"

HEADERS = {
    "apikey": API_KEY_EVO,
    "Content-Type": "application/json",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)