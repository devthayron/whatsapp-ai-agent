import logging
from pathlib import Path

from config import settings


def setup_logging():
    """
    Configura o logging da aplicação no console e arquivo (logs/app.log).

    O nível é controlado pela variável de ambiente LOG_LEVEL
    (default: INFO).
    """
    Path("logs").mkdir(exist_ok=True)

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Reduz logs de bibliotecas externas.
    for logger_name in ("httpx", "httpcore", "openai", "urllib3"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
