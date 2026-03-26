from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import GitCredential, PaginatedResponse
from .._util import _from_dict


class CredentialsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create(
        self,
        provider: str,
        token: str,
        username: Optional[str] = None,
        label: Optional[str] = None,
    ) -> GitCredential:
        body: dict[str, Any] = {"provider": provider, "token": token}
        if username is not None:
            body["username"] = username
        if label is not None:
            body["label"] = label
        data = await self._http.post("/git-credentials", body)
        return _from_dict(GitCredential, data)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[GitCredential]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get("/git-credentials", query)
        return PaginatedResponse(
            data=[_from_dict(GitCredential, c) for c in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def update(
        self,
        id: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        label: Optional[str] = None,
    ) -> GitCredential:
        body: dict[str, Any] = {}
        if token is not None:
            body["token"] = token
        if username is not None:
            body["username"] = username
        if label is not None:
            body["label"] = label
        data = await self._http.patch(f"/git-credentials/{id}", body)
        return _from_dict(GitCredential, data)

    async def delete(self, id: str) -> None:
        await self._http.delete(f"/git-credentials/{id}")
