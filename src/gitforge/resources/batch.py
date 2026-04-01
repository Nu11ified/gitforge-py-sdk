from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class BatchResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create_branches(
        self,
        items: list[dict[str, Any]],
        atomic: bool = False,
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/branches", {
            "action": "create",
            "items": items,
            "atomic": atomic,
            "onError": on_error,
        })

    async def delete_branches(
        self,
        items: list[dict[str, Any]],
        atomic: bool = False,
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/branches", {
            "action": "delete",
            "items": items,
            "atomic": atomic,
            "onError": on_error,
        })

    async def create_commits(
        self,
        items: list[dict[str, Any]],
        atomic: bool = False,
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/commits", {
            "items": items,
            "atomic": atomic,
            "onError": on_error,
        })

    async def read_files(
        self,
        items: list[dict[str, Any]],
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/files/read", {
            "items": items,
            "onError": on_error,
        })

    async def write_files(
        self,
        items: list[dict[str, Any]],
        atomic: bool = False,
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/files/write", {
            "items": items,
            "atomic": atomic,
            "onError": on_error,
        })

    async def read_refs(
        self,
        items: list[dict[str, Any]],
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/refs", {
            "action": "read",
            "items": items,
            "onError": on_error,
        })

    async def create_prs(
        self,
        items: list[dict[str, Any]],
        atomic: bool = False,
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/prs", {
            "items": items,
            "atomic": atomic,
            "onError": on_error,
        })

    async def diff(
        self,
        items: list[dict[str, Any]],
        on_error: str = "continue",
    ) -> dict:
        return await self._http.post("/batch/diff", {
            "items": items,
            "onError": on_error,
        })
