from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from ..http import HttpClient
from ..types import Tag, PaginatedResponse
from .._util import _from_dict


class TagsResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[Tag]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get(f"/repos/{self._repo_id}/tags", query)
        return PaginatedResponse(
            data=[_from_dict(Tag, t) for t in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def create(self, name: str, sha: str) -> Tag:
        data = await self._http.post(
            f"/repos/{self._repo_id}/tags", {"name": name, "sha": sha}
        )
        return _from_dict(Tag, data)

    async def delete(self, name: str) -> None:
        await self._http.delete(
            f"/repos/{self._repo_id}/tags/{quote(name, safe='')}"
        )
