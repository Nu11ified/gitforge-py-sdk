from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class ChangesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create(self, repo_id: str, base_ref: str = "main",
                     description: Optional[str] = None,
                     files: Optional[list[dict]] = None) -> dict:
        body: dict[str, Any] = {"baseRef": base_ref}
        if description:
            body["description"] = description
        if files:
            body["files"] = files
        return await self._http.post(f"/repos/{repo_id}/changes", body)

    async def list(self, repo_id: str, status: Optional[str] = None) -> dict:
        query: dict[str, str] = {}
        if status:
            query["status"] = status
        return await self._http.get(f"/repos/{repo_id}/changes", query)

    async def get(self, repo_id: str, change_id: str) -> dict:
        return await self._http.get(f"/repos/{repo_id}/changes/{change_id}")

    async def abandon(self, repo_id: str, change_id: str) -> dict:
        return await self._http.delete(f"/repos/{repo_id}/changes/{change_id}")

    async def amend(self, repo_id: str, change_id: str,
                    files: Optional[list[dict]] = None,
                    deletes: Optional[list[str]] = None) -> dict:
        body: dict[str, Any] = {}
        if files:
            body["files"] = files
        if deletes:
            body["deletes"] = deletes
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/amend", body)

    async def squash(self, repo_id: str, change_id: str,
                     files: Optional[list[str]] = None) -> dict:
        body: dict[str, Any] = {}
        if files:
            body["files"] = files
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/squash", body)

    async def split(self, repo_id: str, change_id: str, files: list[str]) -> dict:
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/split", {"files": files})

    async def describe(self, repo_id: str, change_id: str, description: str) -> dict:
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/describe", {"description": description})

    async def resolve(self, repo_id: str, change_id: str, files: list[dict]) -> dict:
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/resolve", {"files": files})

    async def materialize(self, repo_id: str, change_id: str, branch: str) -> dict:
        return await self._http.post(f"/repos/{repo_id}/changes/{change_id}/materialize", {"branch": branch})

    async def import_from_commits(self, repo_id: str, branch: str, since: Optional[str] = None) -> dict:
        body: dict[str, Any] = {"branch": branch}
        if since:
            body["since"] = since
        return await self._http.post(f"/repos/{repo_id}/changes/from-commits", body)
