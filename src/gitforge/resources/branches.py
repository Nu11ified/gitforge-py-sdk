from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from ..http import HttpClient
from ..types import Branch, PaginatedResponse, PromoteResult
from .._util import _from_dict


class BranchesResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> PaginatedResponse[Branch]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        if namespace is not None:
            query["namespace"] = namespace
        data = await self._http.get(f"/repos/{self._repo_id}/branches", query)
        return PaginatedResponse(
            data=[_from_dict(Branch, b) for b in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def create(
        self,
        name: str,
        sha: str,
        ephemeral: bool = False,
        ttl_hours: Optional[int] = None,
    ) -> Branch:
        body: dict[str, Any] = {"name": name, "sha": sha}
        if ephemeral:
            body["ephemeral"] = True
        if ttl_hours is not None:
            body["ttlHours"] = ttl_hours
        data = await self._http.post(f"/repos/{self._repo_id}/branches", body)
        return _from_dict(Branch, data)

    async def delete(self, name: str, namespace: Optional[str] = None) -> None:
        query: dict[str, str] = {}
        if namespace is not None:
            query["namespace"] = namespace
        await self._http.delete(
            f"/repos/{self._repo_id}/branches/{quote(name, safe='')}",
            query,
        )

    async def promote(
        self,
        base_branch: str,
        target_branch: Optional[str] = None,
    ) -> PromoteResult:
        body: dict[str, Any] = {"baseBranch": base_branch}
        if target_branch is not None:
            body["targetBranch"] = target_branch
        data = await self._http.post(f"/repos/{self._repo_id}/branches/promote", body)
        return _from_dict(PromoteResult, data)
