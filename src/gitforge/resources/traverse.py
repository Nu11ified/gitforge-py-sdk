from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class TraverseResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def repos(
        self,
        q: Optional[str] = None,
        language: Optional[str] = None,
        build_system: Optional[str] = None,
        is_monorepo: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> dict[str, Any]:
        """List repos with index summaries.

        Returns a paginated response with repo summaries including index metadata.
        """
        query: dict[str, str] = {}
        if q is not None:
            query["q"] = q
        if language is not None:
            query["language"] = language
        if build_system is not None:
            query["buildSystem"] = build_system
        if is_monorepo is not None:
            query["isMonorepo"] = str(is_monorepo).lower()
        if sort is not None:
            query["sort"] = sort
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        return await self._http.get("/traverse/repos", query)

    async def repo(
        self,
        repo_id: str,
        ref: Optional[str] = None,
        depth: Optional[str] = None,
        path: Optional[str] = None,
        include: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Get repo traversal data at the specified depth (L1/L2/L3).

        Returns tree structure, symbols, architecture info depending on depth.
        """
        query: dict[str, str] = {}
        if ref is not None:
            query["ref"] = ref
        if depth is not None:
            query["depth"] = depth
        if path is not None:
            query["path"] = path
        if include is not None and len(include) > 0:
            query["include"] = ",".join(include)
        return await self._http.get(f"/traverse/{repo_id}", query)

    async def impact(
        self,
        repo_id: str,
        paths: list[str],
        ref: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run impact analysis for changed paths.

        Returns impacted files, associated test files, and total impact count.
        """
        query: dict[str, str] = {
            "paths": ",".join(paths),
        }
        if ref is not None:
            query["ref"] = ref
        return await self._http.get(f"/traverse/{repo_id}/impact", query)
