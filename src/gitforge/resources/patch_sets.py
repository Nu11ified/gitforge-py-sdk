from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import PatchSet, PatchSetWithPatches, PatchSetPatch
from .._util import _from_dict


class PatchSetsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create(
        self,
        repo_id: str,
        name: str,
        base_ref: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"repoId": repo_id, "name": name}
        if base_ref is not None:
            body["baseRef"] = base_ref
        if description is not None:
            body["description"] = description
        return await self._http.post("/patch-sets", body)

    async def list(
        self,
        repo_id: Optional[str] = None,
    ) -> list[PatchSet]:
        query: dict[str, str] = {}
        if repo_id is not None:
            query["repoId"] = repo_id
        data = await self._http.get("/patch-sets", query)
        if isinstance(data, list):
            return [_from_dict(PatchSet, item) for item in data]
        if isinstance(data, dict) and "data" in data:
            return [_from_dict(PatchSet, item) for item in data["data"]]
        return []

    async def get(self, set_id: str) -> PatchSetWithPatches:
        data = await self._http.get(f"/patch-sets/{set_id}")
        return _from_dict(PatchSetWithPatches, data)

    async def update(
        self,
        set_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        auto_rebase: Optional[bool] = None,
        visibility: Optional[str] = None,
    ) -> PatchSet:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if auto_rebase is not None:
            body["autoRebase"] = auto_rebase
        if visibility is not None:
            body["visibility"] = visibility
        data = await self._http.patch(f"/patch-sets/{set_id}", body)
        return _from_dict(PatchSet, data)

    async def delete(self, set_id: str) -> None:
        await self._http.delete(f"/patch-sets/{set_id}")

    async def add_patch(
        self,
        set_id: str,
        name: str,
        diff: str,
        description: Optional[str] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name, "diff": diff}
        if description is not None:
            body["description"] = description
        if author_name is not None:
            body["authorName"] = author_name
        if author_email is not None:
            body["authorEmail"] = author_email
        return await self._http.post(f"/patch-sets/{set_id}/patches", body)

    async def update_patch(
        self,
        set_id: str,
        patch_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        order: Optional[int] = None,
    ) -> dict:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if status is not None:
            body["status"] = status
        if order is not None:
            body["order"] = order
        return await self._http.patch(f"/patch-sets/{set_id}/patches/{patch_id}", body)

    async def remove_patch(self, set_id: str, patch_id: str) -> None:
        await self._http.delete(f"/patch-sets/{set_id}/patches/{patch_id}")

    async def rebase(self, set_id: str) -> dict:
        return await self._http.post(f"/patch-sets/{set_id}/rebase")

    async def materialize(self, set_id: str) -> dict:
        return await self._http.post(f"/patch-sets/{set_id}/materialize")
