from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import RepoToken
from .._util import _from_dict


class TokensResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def create(
        self,
        ttl_seconds: Optional[int] = None,
        scopes: Optional[list[str]] = None,
    ) -> RepoToken:
        body: dict[str, Any] = {}
        if ttl_seconds is not None:
            body["ttlSeconds"] = ttl_seconds
        if scopes is not None:
            body["scopes"] = scopes
        data = await self._http.post(f"/repos/{self._repo_id}/tokens", body)
        return _from_dict(RepoToken, data)
