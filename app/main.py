from fastapi import FastAPI

from logger import setup_logging
setup_logging()

from app.routes.chat import router as chat_router
from app.routes.webhook import router as webhook_router
from database.connection import Base, engine
from database import models

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(chat_router)
app.include_router(webhook_router)

@app.get("/")
def home():
    return {
        "status": "online"
    }