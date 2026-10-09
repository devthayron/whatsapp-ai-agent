import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

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


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(webhook_router)


@app.get("/")
def home():
    return {"status": "online"}
