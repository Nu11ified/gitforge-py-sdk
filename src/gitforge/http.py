from __future__ import annotations

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
