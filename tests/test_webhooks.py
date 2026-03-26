from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.webhooks import WebhooksResource
from gitforge.types import (
    PaginatedResponse,
    Webhook,
    WebhookDelivery,
    WebhookTestResult,
)


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://api.gitforge.dev"
REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
WEBHOOK_ID = "wh-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
WEBHOOKS_URL = f"{BASE_URL}/repos/{REPO_ID}/webhooks"

WEBHOOK_JSON = {
    "id": WEBHOOK_ID,
    "url": "https://example.com/webhook",
    "events": ["push", "pull_request"],
    "active": True,
}

DELIVERY_JSON = {
    "id": "del-001",
    "eventType": "push",
    "payload": '{"ref":"refs/heads/main"}',
    "responseStatus": 200,
    "responseBody": "OK",
    "deliveredAt": "2026-03-25T12:00:00.000Z",
    "createdAt": "2026-03-25T11:59:59.000Z",
}

TEST_RESULT_JSON = {
    "success": True,
    "status": 200,
    "responseBody": "OK",
    "durationMs": 142,
    "error": None,
}


def _webhook_json(**overrides: object) -> dict:
    d = dict(WEBHOOK_JSON)
    d.update(overrides)
    return d


def _delivery_json(**overrides: object) -> dict:
    d = dict(DELIVERY_JSON)
    d.update(overrides)
    return d


def _paginated(items: list[dict], total: int | None = None, **kw: object) -> dict:
    defaults: dict = {
        "data": items,
        "total": total if total is not None else len(items),
        "limit": 25,
        "offset": 0,
        "hasMore": False,
    }
    defaults.update(kw)
    return defaults


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def webhooks(http_client: HttpClient) -> WebhooksResource:
    return WebhooksResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_sends_post_with_url_only(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(WEBHOOKS_URL).mock(
            return_value=httpx.Response(201, json=_webhook_json())
        )
        await webhooks.create(url="https://example.com/webhook")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"url": "https://example.com/webhook"}

    async def test_sends_post_with_secret_and_events(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(WEBHOOKS_URL).mock(
            return_value=httpx.Response(
                201, json=_webhook_json(events=["push"])
            )
        )
        await webhooks.create(
            url="https://example.com/webhook",
            secret="my-webhook-secret",
            events=["push"],
        )
        body = json.loads(route.calls[0].request.content)
        assert body["url"] == "https://example.com/webhook"
        assert body["secret"] == "my-webhook-secret"
        assert body["events"] == ["push"]
        assert "active" not in body

    async def test_returns_webhook(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(WEBHOOKS_URL).mock(
            return_value=httpx.Response(201, json=_webhook_json())
        )
        result = await webhooks.create(url="https://example.com/webhook")
        assert isinstance(result, Webhook)
        assert result.id == WEBHOOK_ID
        assert result.url == "https://example.com/webhook"
        assert result.events == ["push", "pull_request"]
        assert result.active is True

    async def test_sends_post_to_correct_url(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(WEBHOOKS_URL).mock(
            return_value=httpx.Response(201, json=_webhook_json())
        )
        await webhooks.create(url="https://example.com/webhook")
        request = route.calls[0].request
        assert str(request.url) == WEBHOOKS_URL
        assert request.method == "POST"


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_sends_get_default_params(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(WEBHOOKS_URL).mock(
            return_value=httpx.Response(
                200, json=_paginated([_webhook_json()])
            )
        )
        await webhooks.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"

    async def test_sends_get_with_limit_and_offset(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(WEBHOOKS_URL).mock(
            return_value=httpx.Response(
                200,
                json=_paginated(
                    [_webhook_json()],
                    total=50,
                    limit=10,
                    offset=20,
                    hasMore=True,
                ),
            )
        )
        result = await webhooks.list(limit=10, offset=20)
        request = route.calls[0].request
        assert "limit=10" in str(request.url)
        assert "offset=20" in str(request.url)
        assert result.limit == 10
        assert result.offset == 20
        assert result.has_more is True

    async def test_returns_paginated_response_of_webhooks(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        w1 = _webhook_json(id="wh-1")
        w2 = _webhook_json(id="wh-2", active=False)
        mock_router.get(WEBHOOKS_URL).mock(
            return_value=httpx.Response(
                200, json=_paginated([w1, w2], total=2)
            )
        )
        result = await webhooks.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(w, Webhook) for w in result.data)
        assert result.data[0].id == "wh-1"
        assert result.data[1].id == "wh-2"
        assert result.data[1].active is False
        assert result.total == 2

    async def test_returns_empty_list(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(WEBHOOKS_URL).mock(
            return_value=httpx.Response(200, json=_paginated([]))
        )
        result = await webhooks.list()
        assert result.data == []
        assert result.total == 0


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_sends_delete_request(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        result = await webhooks.delete(WEBHOOK_ID)
        assert route.called
        assert result is None

    async def test_sends_delete_to_correct_url(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        other_id = "wh-delete-me"
        url = f"{WEBHOOKS_URL}/{other_id}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        await webhooks.delete(other_id)
        request = route.calls[0].request
        assert str(request.url) == url
        assert request.method == "DELETE"


# ---------------------------------------------------------------------------
# test
# ---------------------------------------------------------------------------


class TestTest:
    async def test_sends_post_to_test_url(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/test"
        route = mock_router.post(url).mock(
            return_value=httpx.Response(200, json=TEST_RESULT_JSON)
        )
        await webhooks.test(WEBHOOK_ID)
        assert route.called
        request = route.calls[0].request
        assert request.method == "POST"
        assert str(request.url) == url

    async def test_returns_webhook_test_result(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/test"
        mock_router.post(url).mock(
            return_value=httpx.Response(200, json=TEST_RESULT_JSON)
        )
        result = await webhooks.test(WEBHOOK_ID)
        assert isinstance(result, WebhookTestResult)
        assert result.success is True
        assert result.status == 200
        assert result.response_body == "OK"
        assert result.duration_ms == 142
        assert result.error is None

    async def test_returns_failed_test_result(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/test"
        mock_router.post(url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": False,
                    "status": None,
                    "responseBody": None,
                    "durationMs": 5012,
                    "error": "Connection refused",
                },
            )
        )
        result = await webhooks.test(WEBHOOK_ID)
        assert result.success is False
        assert result.status is None
        assert result.response_body is None
        assert result.duration_ms == 5012
        assert result.error == "Connection refused"


# ---------------------------------------------------------------------------
# deliveries
# ---------------------------------------------------------------------------


class TestDeliveries:
    async def test_sends_get_to_deliveries_url(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/deliveries"
        route = mock_router.get(url).mock(
            return_value=httpx.Response(
                200, json=_paginated([_delivery_json()])
            )
        )
        await webhooks.deliveries(WEBHOOK_ID)
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"

    async def test_returns_paginated_response_of_deliveries(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/deliveries"
        d1 = _delivery_json(id="del-001")
        d2 = _delivery_json(id="del-002", eventType="pull_request")
        mock_router.get(url).mock(
            return_value=httpx.Response(
                200, json=_paginated([d1, d2], total=2)
            )
        )
        result = await webhooks.deliveries(WEBHOOK_ID)
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(d, WebhookDelivery) for d in result.data)
        assert result.data[0].id == "del-001"
        assert result.data[0].event_type == "push"
        assert result.data[1].id == "del-002"
        assert result.data[1].event_type == "pull_request"
        assert result.total == 2

    async def test_sends_get_with_limit_and_offset(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/deliveries"
        route = mock_router.get(url).mock(
            return_value=httpx.Response(
                200,
                json=_paginated(
                    [_delivery_json()],
                    total=30,
                    limit=5,
                    offset=10,
                    hasMore=True,
                ),
            )
        )
        result = await webhooks.deliveries(WEBHOOK_ID, limit=5, offset=10)
        request = route.calls[0].request
        assert "limit=5" in str(request.url)
        assert "offset=10" in str(request.url)
        assert result.limit == 5
        assert result.offset == 10
        assert result.has_more is True

    async def test_deserialises_all_delivery_fields(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/deliveries"
        mock_router.get(url).mock(
            return_value=httpx.Response(
                200, json=_paginated([_delivery_json()])
            )
        )
        result = await webhooks.deliveries(WEBHOOK_ID)
        d = result.data[0]
        assert d.id == "del-001"
        assert d.event_type == "push"
        assert d.payload == '{"ref":"refs/heads/main"}'
        assert d.response_status == 200
        assert d.response_body == "OK"
        assert d.delivered_at == "2026-03-25T12:00:00.000Z"
        assert d.created_at == "2026-03-25T11:59:59.000Z"

    async def test_delivery_with_null_optional_fields(
        self, webhooks: WebhooksResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{WEBHOOKS_URL}/{WEBHOOK_ID}/deliveries"
        mock_router.get(url).mock(
            return_value=httpx.Response(
                200,
                json=_paginated(
                    [
                        _delivery_json(
                            responseStatus=None,
                            responseBody=None,
                            deliveredAt=None,
                        )
                    ]
                ),
            )
        )
        result = await webhooks.deliveries(WEBHOOK_ID)
        d = result.data[0]
        assert d.response_status is None
        assert d.response_body is None
        assert d.delivered_at is None
        assert d.created_at == "2026-03-25T11:59:59.000Z"
