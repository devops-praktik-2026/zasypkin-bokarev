"""Общая подготовка для тестов сервиса заказов.

Каждый тест получает свою пустую базу данных в оперативной памяти.
Так тесты не зависят друг от друга и не требуют запущенного PostgreSQL.
"""

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from orders.db import Base, get_session
from orders.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def order_payload() -> dict:
    return {"account_id": 1, "item": "Кофемолка", "quantity": 2}


@pytest.fixture(autouse=True)
def fake_accounts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Подменяем соседа: номер 999 — клиента нет, номер 500 — сервис не отвечает.

    Остальным номерам сервис клиентов отвечает «существует».
    """

    class FakeResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("unexpected", request=None, response=None)

    def fake_get(url: str, timeout: float | None = None) -> FakeResponse:
        if url.endswith("/999"):
            return FakeResponse(404)
        if url.endswith("/500"):
            raise httpx.ConnectError("сервис клиентов не отвечает")
        return FakeResponse(200)

    from orders import accounts_client

    monkeypatch.setattr(accounts_client.httpx, "get", fake_get)
