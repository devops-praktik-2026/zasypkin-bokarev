"""Тесты запросов к сервису заказов."""

import pytest


def test_create_order_returns_201_and_card(client, order_payload):
    response = client.post("/orders", json=order_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["account_id"] == order_payload["account_id"]
    assert body["item"] == order_payload["item"]
    assert body["quantity"] == order_payload["quantity"]
    assert body["created_at"]


@pytest.mark.parametrize(
    "broken_field",
    [
        {"quantity": 0},
        {"quantity": -1},
        {"item": ""},
        {"item": "x" * 200},
        {"account_id": 0},
    ],
)
def test_invalid_payload_returns_422(client, order_payload, broken_field):
    payload = order_payload | broken_field

    response = client.post("/orders", json=payload)

    assert response.status_code == 422
