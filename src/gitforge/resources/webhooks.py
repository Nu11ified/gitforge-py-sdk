from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import Webhook, WebhookDelivery, WebhookTestResult, PaginatedResponse
from .._util import _from_dict


class WebhooksResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def create(
        self,
        url: str,
        events: Optional[list[str]] = None,
        active: bool = True,
    ) -> Webhook:
        body: dict[str, Any] = {"url": url, "active": active}
        if events is not None:
            body["events"] = events
        data = await self._http.post(f"/repos/{self._repo_id}/webhooks", body)
        return _from_dict(Webhook, data)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[Webhook]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get(f"/repos/{self._repo_id}/webhooks", query)
        return PaginatedResponse(
            data=[_from_dict(Webhook, w) for w in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def delete(self, webhook_id: str) -> None:
        await self._http.delete(f"/repos/{self._repo_id}/webhooks/{webhook_id}")

    async def test(self, webhook_id: str) -> WebhookTestResult:
        data = await self._http.post(f"/repos/{self._repo_id}/webhooks/{webhook_id}/test")
        return _from_dict(WebhookTestResult, data)

    async def deliveries(
        self,
        webhook_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[WebhookDelivery]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get(
            f"/repos/{self._repo_id}/webhooks/{webhook_id}/deliveries", query
        )
        return PaginatedResponse(
            data=[_from_dict(WebhookDelivery, d) for d in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )
