from __future__ import annotations

from typing import Optional

from ..http import HttpClient
from ..types import SearchResult, SearchMatch, SearchCodeResult, Comparison, DiffEntry
from .._util import _from_dict


class SearchResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
    ) -> SearchCodeResult:
        # API uses short param names: q for query, lang for language
        params: dict[str, str] = {"q": query}
        if language is not None:
            params["lang"] = language
        data = await self._http.get(f"/repos/{self._repo_id}/search/code", params)
        results = [
            SearchResult(
                repo_id=r.get("repoId", ""),
                repo_name=r.get("repoName", ""),
                file_path=r.get("filePath", ""),
                branch=r.get("branch", ""),
                language=r.get("language"),
                matches=[
                    SearchMatch(line=m["line"], content=m["content"], highlight=m.get("highlight", ""))
                    for m in r.get("matches", [])
                ],
            )
            for r in data.get("results", [])
        ]
        return SearchCodeResult(
            results=results,
            total=data.get("total", 0),
            page=data.get("page", 1),
            per_page=data.get("perPage", 20),
        )

    async def compare(self, base: str, head: str) -> Comparison:
        data = await self._http.get(f"/repos/{self._repo_id}/compare/{base}...{head}")
        return _from_dict(Comparison, data)

    async def compare_diff(self, base: str, head: str) -> list[DiffEntry]:
        data = await self._http.get(f"/repos/{self._repo_id}/compare/{base}...{head}/diff")
        return [_from_dict(DiffEntry, d) for d in data]
