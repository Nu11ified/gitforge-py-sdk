from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class OperationsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def list(self, repo_id: str, limit: int = 30, offset: int = 0) -> dict:
        return await self._http.get(f"/repos/{repo_id}/operations", {"limit": str(limit), "offset": str(offset)})

    async def undo(self, repo_id: str, operation_id: Optional[str] = None) -> dict:
        body: dict[str, Any] = {}
        if operation_id:
            body["operationId"] = operation_id
        return await self._http.post(f"/repos/{repo_id}/operations/undo", body)

    async def restore(self, repo_id: str, operation_id: str) -> dict:
        return await self._http.post(f"/repos/{repo_id}/operations/{operation_id}/restore")
