from __future__ import annotations

from typing import Any

from ..http import HttpClient


class StateResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def current(
        self,
        items: list[dict[str, Any]],
    ) -> dict:
        return await self._http.post("/state/current", {"items": items})
