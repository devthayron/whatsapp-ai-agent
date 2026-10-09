import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import worker
from config import settings
from logger import setup_logging

setup_logging()

from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.webhook_evolution import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = asyncio.Event()

    task = None

    if settings.WORKER_IN_API:
        task = asyncio.create_task(worker.run(stop))

    yield

    stop.set()

    if task:
        await task


app = FastAPI(lifespan=lifespan)

# Necessário para o front no navegador. Com cookies (allow_credentials=True),
# as origens precisam ser explícitas: "*" não funciona.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(webhook_router)


@app.get("/")
def home():
    return {"status": "online"}
