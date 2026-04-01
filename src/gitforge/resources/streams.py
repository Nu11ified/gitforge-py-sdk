from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

from ..http import HttpClient


class StreamsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def repo(
        self,
        repo_id: str,
        types: Optional[list[str]] = None,
        paths: Optional[list[str]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        query: dict[str, str] = {}
        if types:
            query["types"] = ",".join(types)
        if paths:
            query["paths"] = ",".join(paths)

        async for raw in self._http.sse(f"/repos/{repo_id}/stream", query):
            if raw["event"] == "connected":
                continue
            try:
                yield {"event": raw["event"], "data": json.loads(raw["data"])}
            except (json.JSONDecodeError, KeyError):
                yield {"event": raw["event"], "data": {"raw": raw.get("data", "")}}

    async def changes(
        self,
        repos: Optional[list[str]] = None,
        event_types: Optional[list[str]] = None,
        paths: Optional[list[str]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        query: dict[str, str] = {}
        if repos:
            query["repos"] = ",".join(repos)
        if event_types:
            query["eventTypes"] = ",".join(event_types)
        if paths:
            query["paths"] = ",".join(paths)

        async for raw in self._http.sse("/stream/changes", query):
            if raw["event"] == "connected":
                continue
            try:
                yield {"event": raw["event"], "data": json.loads(raw["data"])}
            except (json.JSONDecodeError, KeyError):
                yield {"event": raw["event"], "data": {"raw": raw.get("data", "")}}
