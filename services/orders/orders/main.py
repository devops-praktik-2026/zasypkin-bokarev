"""Точка входа сервиса заказов.

Запуск вручную:
    uvicorn orders.main:app --reload --port 8002
"""

from fastapi import FastAPI
from pydantic import BaseModel

from orders.api import router
from orders.config import settings
from orders.db import Base, engine

app = FastAPI(
    title="Сервис заказов",
    description="Принимает заказы и хранит их историю.",
    version="0.1.0",
)

app.include_router(router)

# Структура базы создаётся при старте. Миграции появятся на этапе 4;
# пока таблица одна, этого достаточно, чтобы сервис работал в compose.

Base.metadata.create_all(bind=engine)


class HealthRead(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthRead, tags=["Служебное"], summary="Жив ли сервис")
def health() -> HealthRead:
    return HealthRead(status="ok", service=settings.service_name)
