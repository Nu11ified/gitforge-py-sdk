from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import MirrorConfig
from .._util import _from_dict


class MirrorsResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def list(self) -> list[MirrorConfig]:
        data = await self._http.get(f"/repos/{self._repo_id}/mirrors")
        return [_from_dict(MirrorConfig, m) for m in data]

    async def create(
        self,
        source_url: str,
        direction: str = "pull",
        interval: Optional[int] = None,
        credential_id: Optional[str] = None,
    ) -> MirrorConfig:
        body: dict[str, Any] = {"sourceUrl": source_url, "direction": direction}
        if interval is not None:
            body["interval"] = interval
        if credential_id is not None:
            body["credentialId"] = credential_id
        data = await self._http.post(f"/repos/{self._repo_id}/mirrors", body)
        return _from_dict(MirrorConfig, data)

    async def update(
        self,
        mirror_id: str,
        interval: Optional[int] = None,
        enabled: Optional[bool] = None,
        credential_id: Optional[str] = None,
    ) -> MirrorConfig:
        body: dict[str, Any] = {}
        if interval is not None:
            body["interval"] = interval
        if enabled is not None:
            body["enabled"] = enabled
        if credential_id is not None:
            body["credentialId"] = credential_id
        data = await self._http.patch(f"/repos/{self._repo_id}/mirrors/{mirror_id}", body)
        return _from_dict(MirrorConfig, data)

    async def delete(self, mirror_id: str) -> None:
        await self._http.delete(f"/repos/{self._repo_id}/mirrors/{mirror_id}")

    async def sync(self, mirror_id: str) -> None:
        await self._http.post(f"/repos/{self._repo_id}/mirrors/{mirror_id}/sync")
