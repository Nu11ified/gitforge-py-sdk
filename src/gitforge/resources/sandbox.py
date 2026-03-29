from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import SandboxUrl
from .._util import _from_dict


class SandboxResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def create_sandbox_url(
        self,
        ttl_seconds: int,
        scopes: Optional[list[str]] = None,
        branch: Optional[str] = None,
        ephemeral: Optional[bool] = None,
    ) -> SandboxUrl:
        body: dict[str, Any] = {"ttlSeconds": ttl_seconds}
        if scopes is not None:
            body["scopes"] = scopes
        if branch is not None:
            body["branch"] = branch
        if ephemeral is not None:
            body["ephemeral"] = ephemeral
        data = await self._http.post(
            f"/repos/{self._repo_id}/sandbox-url", body
        )
        return _from_dict(SandboxUrl, data)
