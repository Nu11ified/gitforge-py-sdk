from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import Repo, PaginatedResponse
from .._util import _from_dict


class ReposResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Repo:
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if visibility is not None:
            body["visibility"] = visibility
        data = await self._http.post("/repos", body)
        return _from_dict(Repo, data)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PaginatedResponse[Repo]:
        query: dict[str, str] = {}
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        data = await self._http.get("/repos", query)
        return PaginatedResponse(
            data=[_from_dict(Repo, r) for r in data["data"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            has_more=data["hasMore"],
        )

    async def get(self, id: str) -> Repo:
        data = await self._http.get(f"/repos/{id}")
        return _from_dict(Repo, data)

    async def update(
        self,
        id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_branch: Optional[str] = None,
        merge_commit_template: Optional[str] = None,
    ) -> Repo:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if default_branch is not None:
            body["defaultBranch"] = default_branch
        if merge_commit_template is not None:
            body["mergeCommitTemplate"] = merge_commit_template
        data = await self._http.patch(f"/repos/{id}", body)
        return _from_dict(Repo, data)

    async def delete(self, id: str) -> None:
        await self._http.delete(f"/repos/{id}")

    # --- Git Notes ---

    async def create_note(
        self,
        repo_id: str,
        sha: str,
        note: str,
        author: dict[str, str],
        expected_ref_sha: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"sha": sha, "action": "add", "note": note, "author": author}
        if expected_ref_sha is not None:
            body["expectedRefSha"] = expected_ref_sha
        return await self._http.post(f"/repos/{repo_id}/notes", body)

    async def append_note(
        self,
        repo_id: str,
        sha: str,
        note: str,
        author: dict[str, str],
    ) -> dict:
        return await self._http.post(f"/repos/{repo_id}/notes", {
            "sha": sha, "action": "append", "note": note, "author": author,
        })

    async def get_note(self, repo_id: str, sha: str) -> dict:
        return await self._http.get(f"/repos/{repo_id}/notes/{sha}")

    async def delete_note(
        self,
        repo_id: str,
        sha: str,
        author: Optional[dict[str, str]] = None,
        expected_ref_sha: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {}
        if author is not None:
            body["author"] = author
        if expected_ref_sha is not None:
            body["expectedRefSha"] = expected_ref_sha
        return await self._http.delete_with_body(f"/repos/{repo_id}/notes/{sha}", body or None)

    # --- Restore Commit ---

    async def restore_commit(
        self,
        repo_id: str,
        target_branch: str,
        target_commit_sha: str,
        author: dict[str, str],
        committer: Optional[dict[str, str]] = None,
        commit_message: Optional[str] = None,
        expected_head_sha: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "targetBranch": target_branch,
            "targetCommitSha": target_commit_sha,
            "author": author,
        }
        if committer is not None:
            body["committer"] = committer
        if commit_message is not None:
            body["commitMessage"] = commit_message
        if expected_head_sha is not None:
            body["expectedHeadSha"] = expected_head_sha
        return await self._http.post(f"/repos/{repo_id}/restore-commit", body)

    # --- Files Metadata ---

    async def list_files_with_metadata(
        self,
        repo_id: str,
        ref: Optional[str] = None,
        ephemeral: Optional[bool] = None,
    ) -> dict:
        query: dict[str, str] = {}
        if ref is not None:
            query["ref"] = ref
        if ephemeral is not None:
            query["ephemeral"] = str(ephemeral).lower()
        return await self._http.get(f"/repos/{repo_id}/files/metadata", query)

    # --- Fork Sync ---

    async def pull_upstream(
        self,
        repo_id: str,
        branch: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {}
        if branch is not None:
            body["branch"] = branch
        return await self._http.post(f"/repos/{repo_id}/pull-upstream", body)

    async def detach_upstream(self, repo_id: str) -> dict:
        return await self._http.delete(f"/repos/{repo_id}/base")

    # --- Raw Blob ---

    async def get_raw_file(
        self,
        repo_id: str,
        ref: str,
        path: str,
        download: bool = False,
    ) -> bytes:
        query: dict[str, str] = {"path": path}
        if download:
            query["download"] = "true"
        return await self._http.get_raw(f"/repos/{repo_id}/raw/{ref}", query)
