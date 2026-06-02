from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routers import users

app = FastAPI(title="Lvtantan API")
app.include_router(users.router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
