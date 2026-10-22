"""Описание того, что сервис принимает и что отдаёт.

Эти классы — не формальность. Из них FastAPI сам собирает документацию
по адресу /docs и сам проверяет входящие данные.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """Данные для создания заказа."""

    account_id: int = Field(gt=0, examples=[1])
    item: str = Field(min_length=1, max_length=128, examples=["Кофемолка"])
    quantity: int = Field(ge=1, examples=[2])


class OrderRead(BaseModel):
    """То, что сервис отдаёт наружу."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    item: str
    quantity: int
    created_at: datetime
