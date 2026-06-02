from fastapi import FastAPI

from app import models
from app.database import Base, engine

app = FastAPI(title="Lvtantan API")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
