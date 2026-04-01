from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class RecipesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def run(
        self,
        name: str,
        repos: Optional[list[str]] = None,
        repo_pattern: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        atomic: bool = False,
        dry_run: bool = False,
    ) -> dict:
        body: dict[str, Any] = {}
        if repos is not None:
            body["repos"] = repos
        if repo_pattern is not None:
            body["repoPattern"] = repo_pattern
        if params:
            body["params"] = params
        if atomic:
            body["atomic"] = True
        if dry_run:
            body["dryRun"] = True
        return await self._http.post(f"/recipes/{name}", body)

    async def patch_fleet(
        self,
        repos: list[str],
        branch_name: str,
        commit_message: str,
        files: list[dict[str, str]],
        create_pr: Optional[dict[str, str]] = None,
    ) -> dict:
        params: dict[str, Any] = {
            "branchName": branch_name,
            "commitMessage": commit_message,
            "files": files,
        }
        if create_pr:
            params["createPr"] = create_pr
        return await self.run("patch-fleet", repos=repos, params=params)

    async def snapshot(
        self,
        repos: list[str],
        paths: Optional[list[str]] = None,
        ref: Optional[str] = None,
    ) -> dict:
        params: dict[str, Any] = {}
        if paths:
            params["paths"] = paths
        if ref:
            params["ref"] = ref
        return await self.run("snapshot", repos=repos, params=params)
