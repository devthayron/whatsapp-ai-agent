from config import settings
from integrations.evolution.client import evolution_service

# from integrations.meta.client import meta_service


def get_messaging_service():
    if settings.MESSAGING_PROVIDER == "evolution":
        return evolution_service

    # if settings.MESSAGING_PROVIDER == "meta":
    #     return meta_service

    raise ValueError(f"Messaging provider não suportado: {settings.MESSAGING_PROVIDER}")


messaging_service = get_messaging_service()
