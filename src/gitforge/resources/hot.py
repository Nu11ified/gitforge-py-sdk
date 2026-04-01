from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from ..http import HttpClient


class HotResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def read_file(
        self,
        repo_id: str,
        path: str,
        ref: str = "main",
        include: Optional[list[str]] = None,
    ) -> dict:
        query: dict[str, str] = {"ref": ref}
        if include:
            query["include"] = ",".join(include)
        encoded_path = "/".join(quote(seg, safe="") for seg in path.split("/"))
        return await self._http.get(f"/repos/{repo_id}/hot/files/{encoded_path}", query)

    async def list_tree(
        self,
        repo_id: str,
        path: str = ".",
        ref: str = "main",
        depth: int = 1,
    ) -> dict:
        query: dict[str, str] = {"ref": ref, "depth": str(depth)}
        # "." means root tree — use "root" to avoid URL normalization stripping the dot
        safe_path = "root" if path in (".", "") else path
        encoded_path = "/".join(quote(seg, safe="") for seg in safe_path.split("/"))
        return await self._http.get(f"/repos/{repo_id}/hot/tree/{encoded_path}", query)

    async def commit(
        self,
        repo_id: str,
        ref: str,
        message: str,
        operations: list[dict[str, Any]],
        author: Optional[dict[str, str]] = None,
        expected_head_sha: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "ref": ref,
            "message": message,
            "operations": operations,
        }
        if author is not None:
            body["author"] = author
        if expected_head_sha is not None:
            body["expectedHeadSha"] = expected_head_sha
        return await self._http.post(f"/repos/{repo_id}/hot/commit", body)

    async def list_refs(
        self,
        repo_id: str,
        pattern: Optional[str] = None,
    ) -> dict:
        query: dict[str, str] = {}
        if pattern:
            query["pattern"] = pattern
        return await self._http.get(f"/repos/{repo_id}/hot/refs", query)

    async def create_ref(
        self,
        repo_id: str,
        name: str,
        sha: str,
        force: bool = False,
    ) -> dict:
        return await self._http.post(f"/repos/{repo_id}/hot/refs", {
            "name": name,
            "sha": sha,
            "force": force,
        })
