from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import Repo, PaginatedResponse
from .._util import _from_dict


class ReposResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Repo:
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if visibility is not None:
            body["visibility"] = visibility
        data = await self._http.post("/repos", body)
        return _from_dict(Repo, data)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[Repo]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get("/repos", query)
        return PaginatedResponse(
            data=[_from_dict(Repo, r) for r in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def get(self, id: str) -> Repo:
        data = await self._http.get(f"/repos/{id}")
        return _from_dict(Repo, data)

    async def update(
        self,
        id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_branch: Optional[str] = None,
        merge_commit_template: Optional[str] = None,
    ) -> Repo:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if default_branch is not None:
            body["defaultBranch"] = default_branch
        if merge_commit_template is not None:
            body["mergeCommitTemplate"] = merge_commit_template
        data = await self._http.patch(f"/repos/{id}", body)
        return _from_dict(Repo, data)

    async def delete(self, id: str) -> None:
        await self._http.delete(f"/repos/{id}")
