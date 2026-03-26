from __future__ import annotations

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.search import SearchResource
from gitforge.types import (
    Comparison,
    DiffEntry,
    SearchCodeResult,
    SearchMatch,
    SearchResult,
)


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
SEARCH_CODE_URL = f"{BASE_URL}/repos/{REPO_ID}/search/code"


def _search_match(**overrides: object) -> dict:
    d: dict = {"line": 10, "content": 'console.log("hello")', "highlight": "hello"}
    d.update(overrides)
    return d


def _search_result(**overrides: object) -> dict:
    d: dict = {
        "repoId": REPO_ID,
        "repoName": "my-repo",
        "filePath": "src/index.ts",
        "branch": "main",
        "language": "typescript",
        "matches": [_search_match()],
    }
    d.update(overrides)
    return d


def _search_code_result(**overrides: object) -> dict:
    d: dict = {
        "results": [_search_result()],
        "total": 1,
        "page": 1,
        "perPage": 20,
    }
    d.update(overrides)
    return d


def _comparison(**overrides: object) -> dict:
    d: dict = {
        "ahead": 3,
        "behind": 1,
        "commits": [
            {"sha": "abc123", "message": "feat: add feature", "author": "dev", "date": "2026-03-25T00:00:00Z"},
        ],
        "files": [{"path": "src/index.ts", "status": "modified"}],
    }
    d.update(overrides)
    return d


def _diff_entry(**overrides: object) -> dict:
    d: dict = {
        "path": "src/index.ts",
        "status": "modified",
        "additions": 5,
        "deletions": 2,
        "patch": "@@ -1,3 +1,6 @@\n+new line",
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def search(http_client: HttpClient) -> SearchResource:
    return SearchResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# search_code
# ---------------------------------------------------------------------------


class TestSearchCode:
    async def test_sends_query_as_q_param(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result())
        )
        await search.search_code("hello")
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        url_str = str(request.url)
        assert "q=hello" in url_str

    async def test_sends_language_as_lang_param(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result())
        )
        await search.search_code("hello", language="typescript")
        url_str = str(route.calls[0].request.url)
        assert "lang=typescript" in url_str
        assert "q=hello" in url_str

    async def test_omits_lang_param_when_language_not_provided(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result())
        )
        await search.search_code("test")
        url_str = str(route.calls[0].request.url)
        assert "lang=" not in url_str

    async def test_returns_search_code_result_shape(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result(total=42, page=2, perPage=10))
        )
        result = await search.search_code("hello")
        assert isinstance(result, SearchCodeResult)
        assert result.total == 42
        assert result.page == 2
        assert result.per_page == 10

    async def test_result_contains_search_result_objects(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result())
        )
        result = await search.search_code("hello")
        assert len(result.results) == 1
        r = result.results[0]
        assert isinstance(r, SearchResult)
        assert r.repo_id == REPO_ID
        assert r.repo_name == "my-repo"
        assert r.file_path == "src/index.ts"
        assert r.branch == "main"
        assert r.language == "typescript"

    async def test_result_matches_are_parsed(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        sr = _search_result(
            filePath="lib/utils.ts",
            matches=[
                {"line": 5, "content": "function hello() {}", "highlight": "hello"},
                {"line": 12, "content": 'return "hello world"', "highlight": "hello"},
            ],
        )
        mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result(results=[sr]))
        )
        result = await search.search_code("hello")
        matches = result.results[0].matches
        assert len(matches) == 2
        assert all(isinstance(m, SearchMatch) for m in matches)
        assert matches[0].line == 5
        assert matches[0].content == "function hello() {}"
        assert matches[0].highlight == "hello"
        assert matches[1].line == 12
        assert matches[1].content == 'return "hello world"'

    async def test_handles_empty_results(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result(results=[], total=0))
        )
        result = await search.search_code("nonexistent")
        assert result.results == []
        assert result.total == 0

    async def test_handles_result_without_language(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        sr = _search_result()
        del sr["language"]
        mock_router.get(SEARCH_CODE_URL).mock(
            return_value=httpx.Response(200, json=_search_code_result(results=[sr]))
        )
        result = await search.search_code("hello")
        assert result.results[0].language is None


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


class TestCompare:
    async def test_sends_get_to_compare_url(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        compare_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...feature"
        route = mock_router.get(compare_url).mock(
            return_value=httpx.Response(200, json=_comparison())
        )
        result = await search.compare("main", "feature")
        assert route.called
        assert route.calls[0].request.method == "GET"

    async def test_returns_comparison_dataclass(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        compare_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...feature"
        mock_router.get(compare_url).mock(
            return_value=httpx.Response(200, json=_comparison())
        )
        result = await search.compare("main", "feature")
        assert isinstance(result, Comparison)
        assert result.ahead == 3
        assert result.behind == 1
        assert len(result.commits) == 1
        assert len(result.files) == 1

    async def test_returns_correct_comparison_shape(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        compare_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...develop"
        data = _comparison(
            ahead=5,
            behind=0,
            commits=[
                {"sha": "aaa", "message": "first", "author": "dev1", "date": "2026-03-20T00:00:00Z"},
                {"sha": "bbb", "message": "second", "author": "dev2", "date": "2026-03-21T00:00:00Z"},
            ],
            files=[
                {"path": "a.ts", "status": "added"},
                {"path": "b.ts", "status": "deleted"},
            ],
        )
        mock_router.get(compare_url).mock(
            return_value=httpx.Response(200, json=data)
        )
        result = await search.compare("main", "develop")
        assert result.ahead == 5
        assert result.behind == 0
        assert len(result.commits) == 2
        assert result.commits[0]["sha"] == "aaa"
        assert result.commits[1]["message"] == "second"
        assert len(result.files) == 2
        assert result.files[0]["status"] == "added"
        assert result.files[1]["path"] == "b.ts"


# ---------------------------------------------------------------------------
# compare_diff
# ---------------------------------------------------------------------------


class TestCompareDiff:
    async def test_sends_get_to_compare_diff_url(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        diff_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...feature/diff"
        route = mock_router.get(diff_url).mock(
            return_value=httpx.Response(200, json=[_diff_entry()])
        )
        result = await search.compare_diff("main", "feature")
        assert route.called
        assert route.calls[0].request.method == "GET"

    async def test_returns_list_of_diff_entries(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        diff_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...feature/diff"
        mock_router.get(diff_url).mock(
            return_value=httpx.Response(200, json=[_diff_entry()])
        )
        result = await search.compare_diff("main", "feature")
        assert len(result) == 1
        assert isinstance(result[0], DiffEntry)
        assert result[0].path == "src/index.ts"
        assert result[0].status == "modified"
        assert result[0].additions == 5
        assert result[0].deletions == 2
        assert "+new line" in result[0].patch

    async def test_returns_multiple_diff_entries(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        diff_url = f"{BASE_URL}/repos/{REPO_ID}/compare/v1.0...v2.0/diff"
        diffs = [
            _diff_entry(path="a.ts", status="added", additions=10, deletions=0),
            _diff_entry(path="b.ts", status="deleted", additions=0, deletions=15),
        ]
        mock_router.get(diff_url).mock(
            return_value=httpx.Response(200, json=diffs)
        )
        result = await search.compare_diff("v1.0", "v2.0")
        assert len(result) == 2
        assert result[0].path == "a.ts"
        assert result[0].additions == 10
        assert result[1].path == "b.ts"
        assert result[1].deletions == 15

    async def test_returns_empty_list_for_no_diff(
        self, search: SearchResource, mock_router: respx.MockRouter
    ) -> None:
        diff_url = f"{BASE_URL}/repos/{REPO_ID}/compare/main...main/diff"
        mock_router.get(diff_url).mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await search.compare_diff("main", "main")
        assert result == []
