from config import settings


def get_messaging_service():
    # Import tardio: só instancia o cliente do provedor escolhido.
    if settings.MESSAGING_PROVIDER == "evolution":
        from integrations.evolution.client import evolution_service

        return evolution_service

    if settings.MESSAGING_PROVIDER == "meta":
        from integrations.meta.client import meta_service

        return meta_service

    raise ValueError(f"Messaging provider não suportado: {settings.MESSAGING_PROVIDER}")


messaging_service = get_messaging_service()
