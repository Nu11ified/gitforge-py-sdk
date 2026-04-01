from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Optional

import httpx

from .errors import GitForgeError, RefUpdateError


class HttpClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = client or httpx.AsyncClient()

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if extra:
            headers.update(extra)
        return headers

    async def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code == 204:
            return None

        try:
            body = response.json()
        except Exception:
            body = None

        if not response.is_success:
            code = (body or {}).get("code") or (body or {}).get("error") or "unknown"
            message = (body or {}).get("message") or f"HTTP {response.status_code}"

            if response.status_code == 409 and code == "branch_moved" and body and body.get("currentSha"):
                raise RefUpdateError(message, body["currentSha"])

            raise GitForgeError(response.status_code, code, message)

        return body

    async def get(self, path: str, query: Optional[dict[str, str]] = None) -> Any:
        url = f"{self.base_url}{path}"
        response = await self.client.get(url, headers=self._headers(), params=query or {})
        return await self._handle_response(response)

    async def post(self, path: str, body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        kwargs: dict[str, Any] = {"headers": self._headers({"Content-Type": "application/json"})}
        if body is not None:
            kwargs["json"] = body
        response = await self.client.post(url, **kwargs)
        return await self._handle_response(response)

    async def patch(self, path: str, body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        kwargs: dict[str, Any] = {"headers": self._headers({"Content-Type": "application/json"})}
        if body is not None:
            kwargs["json"] = body
        response = await self.client.patch(url, **kwargs)
        return await self._handle_response(response)

    async def delete(self, path: str, query: Optional[dict[str, str]] = None) -> None:
        url = f"{self.base_url}{path}"
        response = await self.client.delete(url, headers=self._headers(), params=query or {})
        return await self._handle_response(response)

    async def get_raw(self, path: str, query: Optional[dict[str, str]] = None) -> bytes:
        url = f"{self.base_url}{path}"
        response = await self.client.get(url, headers=self._headers(), params=query or {})
        if not response.is_success:
            try:
                body = response.json()
            except Exception:
                body = None
            code = (body or {}).get("code") or (body or {}).get("error") or "unknown"
            message = (body or {}).get("message") or f"HTTP {response.status_code}"
            raise GitForgeError(response.status_code, code, message)
        return response.content

    async def delete_with_body(self, path: str, body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        kwargs: dict[str, Any] = {"headers": self._headers({"Content-Type": "application/json"})}
        if body is not None:
            kwargs["json"] = body
        response = await self.client.request("DELETE", url, **kwargs)
        return await self._handle_response(response)

    async def sse(
        self,
        path: str,
        query: Optional[dict[str, str]] = None,
    ) -> AsyncIterator[dict[str, str]]:
        """Consume an SSE endpoint, yielding {event, data} dicts."""
        url = f"{self.base_url}{path}"
        headers = self._headers({"Accept": "text/event-stream"})

        async with self.client.stream(
            "GET", url, headers=headers, params=query or {}
        ) as response:
            if not response.is_success:
                body = None
                try:
                    await response.aread()
                    body = response.json()
                except Exception:
                    pass
                code = (body or {}).get("code") or "unknown"
                message = (body or {}).get("message") or f"HTTP {response.status_code}"
                raise GitForgeError(response.status_code, code, message)

            current_event = "message"
            current_data = ""

            async for line in response.aiter_lines():
                if line == "":
                    if current_data:
                        yield {"event": current_event, "data": current_data}
                    current_event = "message"
                    current_data = ""
                elif line.startswith(":"):
                    continue
                elif line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:"):
                    value = line[5:].strip()
                    current_data = value if current_data == "" else current_data + "\n" + value

            if current_data:
                yield {"event": current_event, "data": current_data}
