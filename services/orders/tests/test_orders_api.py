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


def test_get_order_returns_200_and_card(client, order_payload):
    created = client.post("/orders", json=order_payload).json()

    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["account_id"] == order_payload["account_id"]
    assert body["item"] == order_payload["item"]
    assert body["quantity"] == order_payload["quantity"]
    assert body["created_at"]


def test_get_missing_order_returns_404_with_number(client, order_payload):
    created = client.post("/orders", json=order_payload).json()
    missing_id = created["id"] + 100

    response = client.get(f"/orders/{missing_id}")

    assert response.status_code == 404
    assert str(missing_id) in response.json()["detail"]


def test_list_orders_returns_only_this_account(client, order_payload):
    order_payload |= {"account_id": 7}
    mine = [client.post("/orders", json=order_payload).json()["id"] for _ in range(3)]
    other = order_payload | {"account_id": 8}
    client.post("/orders", json=other)

    response = client.get("/orders", params={"account_id": 7})

    assert response.status_code == 200
    ids = [order["id"] for order in response.json()]
    assert ids == mine


def test_list_orders_empty_account_returns_200_and_empty_list(client):
    response = client.get("/orders", params={"account_id": 99})

    assert response.status_code == 200
    assert response.json() == []


def test_list_orders_limit(client, order_payload):
    order_payload |= {"account_id": 7}
    for _ in range(5):
        client.post("/orders", json=order_payload)

    response = client.get("/orders", params={"account_id": 7, "limit": 2})

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_order_for_missing_account_returns_404(client, order_payload):
    """Клиента с номером 999 нет — заказ в никуда создавать нельзя.

    Ответ сервиса клиентов подменяется: клиент 999 не существует.
    """
    payload = order_payload | {"account_id": 999}

    response = client.post("/orders", json=payload)

    assert response.status_code == 404


def test_create_order_when_accounts_silent_returns_503(client, order_payload):
    """Сервис клиентов не отвечает — заказы отвечают 503, а не виснут."""
    payload = order_payload | {"account_id": 500}

    response = client.post("/orders", json=payload)

    assert response.status_code == 503
