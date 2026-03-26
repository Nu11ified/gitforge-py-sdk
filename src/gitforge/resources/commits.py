from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import Commit, CommitDetail, CommitResult, DiffEntry, PaginatedResponse
from .._util import _from_dict


class CommitBuilder:
    def __init__(
        self,
        http: HttpClient,
        repo_id: str,
        branch: str,
        message: str,
        author_name: str,
        author_email: str,
        base_branch: Optional[str] = None,
    ) -> None:
        self._http = http
        self._repo_id = repo_id
        self._branch = branch
        self._message = message
        self._author_name = author_name
        self._author_email = author_email
        self._base_branch = base_branch
        self._files: list[dict[str, Any]] = []
        self._deletes: list[str] = []
        self._is_ephemeral = False
        self._cas_head_sha: Optional[str] = None

    def add_file(self, path: str, content: str, encoding: str = "utf8", mode: str = "100644") -> CommitBuilder:
        self._files.append({"path": path, "content": content, "encoding": encoding, "mode": mode})
        return self

    def delete_file(self, path: str) -> CommitBuilder:
        self._deletes.append(path)
        return self

    def ephemeral(self, value: bool = True) -> CommitBuilder:
        self._is_ephemeral = value
        return self

    def expected_head_sha(self, sha: str) -> CommitBuilder:
        self._cas_head_sha = sha
        return self

    async def send(self) -> CommitResult:
        body: dict[str, Any] = {
            "branch": self._branch,
            "message": self._message,
            "author": {"name": self._author_name, "email": self._author_email},
            "files": self._files,
            "deletes": self._deletes,
        }
        if self._base_branch:
            body["baseBranch"] = self._base_branch
        if self._is_ephemeral:
            body["ephemeral"] = True
        if self._cas_head_sha:
            body["expectedHeadSha"] = self._cas_head_sha
        data = await self._http.post(f"/repos/{self._repo_id}/commits", body)
        return _from_dict(CommitResult, data)


class CommitsResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def list(
        self,
        ref: str = "HEAD",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[Commit]:
        query: dict[str, str] = {"ref": ref}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get(f"/repos/{self._repo_id}/commits", query)
        return PaginatedResponse(
            data=[_from_dict(Commit, c) for c in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def get(self, sha: str) -> CommitDetail:
        data = await self._http.get(f"/repos/{self._repo_id}/commits/{sha}")
        return _from_dict(CommitDetail, data)

    async def get_diff(self, sha: str) -> list[DiffEntry]:
        data = await self._http.get(f"/repos/{self._repo_id}/commits/{sha}/diff")
        return [_from_dict(DiffEntry, d) for d in data]

    def create(
        self,
        branch: str,
        message: str,
        author_name: str,
        author_email: str,
        base_branch: Optional[str] = None,
    ) -> CommitBuilder:
        return CommitBuilder(
            self._http, self._repo_id, branch, message,
            author_name, author_email, base_branch,
        )
