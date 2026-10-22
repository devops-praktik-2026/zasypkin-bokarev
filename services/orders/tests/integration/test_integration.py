"""Тесты связки двух сервисов.

Отличаются от обычных тестов: им нужны настоящие сервисы,
поднятые docker compose (make up). Поэтому они помечены маркерами
и не запускаются в обычной проверке «Тесты»:
- integration — оба сервиса подняты;
- accounts_down — сервис клиентов погашен (docker compose stop accounts).
"""

import os
import time

import httpx
import pytest

ACCOUNTS_BASE = os.environ.get("ACCOUNTS_BASE", "http://localhost:8001")
ORDERS_BASE = os.environ.get("ORDERS_BASE", "http://localhost:8002")


@pytest.fixture()
def account() -> dict:
    response = httpx.post(
        f"{ACCOUNTS_BASE}/accounts",
        json={"name": "Интеграция", "email": f"int-{time.time_ns()}@example.com"},
        timeout=5,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.integration
def test_create_order_for_real_account_returns_201(account: dict) -> None:
    """Связка насквозь: клиент создан в сервисе клиентов, заказ — в заказах."""

    response = httpx.post(
        f"{ORDERS_BASE}/orders",
        json={"account_id": account["id"], "item": "Кофемолка", "quantity": 1},
        timeout=5,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["account_id"] == account["id"]


@pytest.mark.accounts_down
def test_order_returns_503_fast_when_accounts_silent() -> None:
    """Сосед погашен: 503 («я жив, не отвечает он») не дольше трёх секунд."""

    started = time.monotonic()
    response = httpx.post(
        f"{ORDERS_BASE}/orders",
        json={"account_id": 1, "item": "Что-нибудь", "quantity": 1},
        timeout=10,
    )
    elapsed = time.monotonic() - started

    assert response.status_code == 503, response.text
    assert elapsed < 3, f"ожидали не дольше 3 секунд, получили {elapsed:.1f}"
