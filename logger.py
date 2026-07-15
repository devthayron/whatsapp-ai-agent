import logging
from pathlib import Path

from config import LOG_LEVEL


def setup_logging():
    """
    Configura o logging da aplicação no console e arquivo (logs/app.log).

    Nível controlado via variável de ambiente LOG_LEVEL (default: INFO),
    """
    Path("logs").mkdir(exist_ok=True)

    level = getattr(logging, LOG_LEVEL, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Para não poluir o log da aplicação com detalhes de requests HTTP internas.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)