from __future__ import annotations

from typing import Optional

from ..http import HttpClient
from ..types import TreeEntry, BlobContent
from .._util import _from_dict


class FilesResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def list_files(
        self,
        ref: str = "HEAD",
        path: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> list[TreeEntry]:
        query: dict[str, str] = {}
        if path is not None:
            query["path"] = path
        if namespace is not None:
            query["namespace"] = namespace
        data = await self._http.get(f"/repos/{self._repo_id}/tree/{ref}", query)
        return [_from_dict(TreeEntry, e) for e in data]

    async def get_file(
        self,
        path: str,
        ref: str = "HEAD",
        namespace: Optional[str] = None,
    ) -> BlobContent:
        query: dict[str, str] = {"path": path}
        if namespace is not None:
            query["namespace"] = namespace
        data = await self._http.get(f"/repos/{self._repo_id}/blob/{ref}", query)
        return _from_dict(BlobContent, data)
