from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.commits import CommitBuilder, CommitsResource
from gitforge.types import Commit, CommitDetail, CommitResult, DiffEntry, PaginatedResponse


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
COMMITS_URL = f"{BASE_URL}/repos/{REPO_ID}/commits"

COMMIT_JSON = {
    "sha": "abc123def456789",
    "message": "feat: add README",
    "author": "Alice",
    "authorEmail": "alice@example.com",
    "date": "2026-03-20T12:00:00Z",
    "parentShas": ["000000parent"],
}

COMMIT_DETAIL_JSON = {
    **COMMIT_JSON,
    "tree": "tree-sha-111",
    "files": [{"path": "README.md", "status": "added"}],
}

DIFF_ENTRY_JSON = {
    "path": "README.md",
    "status": "added",
    "additions": 10,
    "deletions": 0,
    "patch": "@@ -0,0 +1,10 @@\n+# Hello",
}

COMMIT_RESULT_JSON = {
    "commitSha": "new-commit-sha-999",
    "treeSha": "new-tree-sha-888",
    "branch": "main",
    "ref": "refs/heads/main",
    "parentShas": ["abc123def456789"],
    "oldSha": "abc123def456789",
    "newSha": "new-commit-sha-999",
}


def _commit_json(**overrides: object) -> dict:
    d = dict(COMMIT_JSON)
    d.update(overrides)
    return d


def _paginated(commits: list[dict], **overrides: object) -> dict:
    d: dict = {
        "data": commits,
        "total": len(commits),
        "limit": 50,
        "offset": 0,
        "hasMore": False,
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def commits(http_client: HttpClient) -> CommitsResource:
    return CommitsResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# CommitBuilder chaining
# ---------------------------------------------------------------------------


class TestCommitBuilderChaining:
    def test_add_file_returns_self(self, http_client: HttpClient) -> None:
        builder = CommitBuilder(http_client, REPO_ID, "main", "msg", "Alice", "alice@example.com")
        result = builder.add_file("file.txt", "hello")
        assert result is builder

    def test_delete_file_returns_self(self, http_client: HttpClient) -> None:
        builder = CommitBuilder(http_client, REPO_ID, "main", "msg", "Alice", "alice@example.com")
        result = builder.delete_file("old.txt")
        assert result is builder

    def test_ephemeral_returns_self(self, http_client: HttpClient) -> None:
        builder = CommitBuilder(http_client, REPO_ID, "main", "msg", "Alice", "alice@example.com")
        result = builder.ephemeral()
        assert result is builder

    def test_expected_head_sha_returns_self(self, http_client: HttpClient) -> None:
        builder = CommitBuilder(http_client, REPO_ID, "main", "msg", "Alice", "alice@example.com")
        result = builder.expected_head_sha("abc123")
        assert result is builder

    def test_methods_can_be_chained(self, http_client: HttpClient) -> None:
        builder = CommitBuilder(http_client, REPO_ID, "main", "msg", "Alice", "alice@example.com")
        result = (
            builder
            .add_file("a.txt", "aaa")
            .add_file("b.txt", "bbb")
            .delete_file("c.txt")
            .ephemeral()
            .expected_head_sha("sha123")
        )
        assert result is builder


# ---------------------------------------------------------------------------
# CommitBuilder.send
# ---------------------------------------------------------------------------


class TestCommitBuilderSend:
    async def test_posts_to_correct_url_with_body(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=COMMIT_RESULT_JSON)
        )
        builder = CommitBuilder(
            http_client, REPO_ID, "main", "feat: init",
            "Alice", "alice@example.com",
        )
        builder.add_file("README.md", "# Hello", encoding="utf8", mode="100644")
        builder.delete_file("old.txt")
        await builder.send()

        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body["branch"] == "main"
        assert body["message"] == "feat: init"
        assert body["author"] == {"name": "Alice", "email": "alice@example.com"}
        assert body["files"] == [
            {"path": "README.md", "content": "# Hello", "encoding": "utf8", "mode": "100644"},
        ]
        assert body["deletes"] == ["old.txt"]
        assert "baseBranch" not in body
        assert "ephemeral" not in body
        assert "expectedHeadSha" not in body

    async def test_includes_base_branch_when_set(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=COMMIT_RESULT_JSON)
        )
        builder = CommitBuilder(
            http_client, REPO_ID, "feature/x", "msg",
            "Alice", "alice@example.com", base_branch="main",
        )
        builder.add_file("f.txt", "content")
        await builder.send()

        body = json.loads(route.calls[0].request.content)
        assert body["baseBranch"] == "main"

    async def test_includes_ephemeral_when_set(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=COMMIT_RESULT_JSON)
        )
        builder = CommitBuilder(
            http_client, REPO_ID, "preview/1", "msg",
            "Alice", "alice@example.com",
        )
        builder.ephemeral()
        await builder.send()

        body = json.loads(route.calls[0].request.content)
        assert body["ephemeral"] is True

    async def test_includes_expected_head_sha_when_set(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=COMMIT_RESULT_JSON)
        )
        builder = CommitBuilder(
            http_client, REPO_ID, "main", "msg",
            "Alice", "alice@example.com",
        )
        builder.expected_head_sha("expected-sha-abc")
        await builder.send()

        body = json.loads(route.calls[0].request.content)
        assert body["expectedHeadSha"] == "expected-sha-abc"

    async def test_returns_commit_result_with_correct_fields(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=COMMIT_RESULT_JSON)
        )
        builder = CommitBuilder(
            http_client, REPO_ID, "main", "msg",
            "Alice", "alice@example.com",
        )
        builder.add_file("f.txt", "data")
        result = await builder.send()

        assert isinstance(result, CommitResult)
        assert result.commit_sha == "new-commit-sha-999"
        assert result.tree_sha == "new-tree-sha-888"
        assert result.branch == "main"
        assert result.ref == "refs/heads/main"
        assert result.parent_shas == ["abc123def456789"]
        assert result.old_sha == "abc123def456789"
        assert result.new_sha == "new-commit-sha-999"


# ---------------------------------------------------------------------------
# CommitsResource.list
# ---------------------------------------------------------------------------


class TestList:
    async def test_lists_commits_with_default_ref(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated([COMMIT_JSON])
        route = mock_router.get(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await commits.list()
        assert route.called
        url_str = str(route.calls[0].request.url)
        assert "ref=HEAD" in url_str
        assert "limit=" not in url_str
        assert "offset=" not in url_str

    async def test_passes_limit_and_offset(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated(
            [COMMIT_JSON], total=100, limit=10, offset=20, hasMore=True
        )
        route = mock_router.get(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await commits.list(limit=10, offset=20)
        url_str = str(route.calls[0].request.url)
        assert "limit=10" in url_str
        assert "offset=20" in url_str
        assert result.limit == 10
        assert result.offset == 20
        assert result.has_more is True

    async def test_passes_custom_ref(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated([COMMIT_JSON])
        route = mock_router.get(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await commits.list(ref="develop")
        url_str = str(route.calls[0].request.url)
        assert "ref=develop" in url_str

    async def test_returns_paginated_response_with_commit_objects(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        c1 = _commit_json(sha="aaa111", message="first")
        c2 = _commit_json(sha="bbb222", message="second")
        paginated = _paginated([c1, c2], total=2)
        mock_router.get(COMMITS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await commits.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(c, Commit) for c in result.data)
        assert result.data[0].sha == "aaa111"
        assert result.data[0].message == "first"
        assert result.data[1].sha == "bbb222"
        assert result.total == 2
        assert result.has_more is False


# ---------------------------------------------------------------------------
# CommitsResource.get
# ---------------------------------------------------------------------------


class TestGet:
    async def test_gets_commit_by_sha(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(f"{COMMITS_URL}/abc123def456789").mock(
            return_value=httpx.Response(200, json=COMMIT_DETAIL_JSON)
        )
        result = await commits.get("abc123def456789")
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        assert f"/commits/abc123def456789" in str(request.url)

    async def test_returns_commit_detail(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(f"{COMMITS_URL}/abc123def456789").mock(
            return_value=httpx.Response(200, json=COMMIT_DETAIL_JSON)
        )
        result = await commits.get("abc123def456789")
        assert isinstance(result, CommitDetail)
        assert result.sha == "abc123def456789"
        assert result.message == "feat: add README"
        assert result.author == "Alice"
        assert result.author_email == "alice@example.com"
        assert result.date == "2026-03-20T12:00:00Z"
        assert result.tree == "tree-sha-111"
        assert result.parent_shas == ["000000parent"]
        assert result.files == [{"path": "README.md", "status": "added"}]


# ---------------------------------------------------------------------------
# CommitsResource.get_diff
# ---------------------------------------------------------------------------


class TestGetDiff:
    async def test_gets_diff_entries_for_sha(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(f"{COMMITS_URL}/abc123def456789/diff").mock(
            return_value=httpx.Response(200, json=[DIFF_ENTRY_JSON])
        )
        result = await commits.get_diff("abc123def456789")
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        assert f"/commits/abc123def456789/diff" in str(request.url)

    async def test_returns_list_of_diff_entry(
        self, commits: CommitsResource, mock_router: respx.MockRouter
    ) -> None:
        d1 = dict(DIFF_ENTRY_JSON)
        d2 = {
            "path": "src/main.py",
            "status": "modified",
            "additions": 5,
            "deletions": 3,
            "patch": "@@ -1,3 +1,5 @@",
        }
        mock_router.get(f"{COMMITS_URL}/abc123def456789/diff").mock(
            return_value=httpx.Response(200, json=[d1, d2])
        )
        result = await commits.get_diff("abc123def456789")
        assert len(result) == 2
        assert all(isinstance(d, DiffEntry) for d in result)
        assert result[0].path == "README.md"
        assert result[0].status == "added"
        assert result[0].additions == 10
        assert result[0].deletions == 0
        assert result[0].patch == "@@ -0,0 +1,10 @@\n+# Hello"
        assert result[1].path == "src/main.py"
        assert result[1].status == "modified"
        assert result[1].additions == 5
        assert result[1].deletions == 3


# ---------------------------------------------------------------------------
# CommitsResource.create
# ---------------------------------------------------------------------------


class TestCreate:
    def test_returns_commit_builder_instance(
        self, commits: CommitsResource
    ) -> None:
        builder = commits.create(
            branch="main",
            message="feat: init",
            author_name="Alice",
            author_email="alice@example.com",
        )
        assert isinstance(builder, CommitBuilder)

    def test_create_with_base_branch_returns_builder(
        self, commits: CommitsResource
    ) -> None:
        builder = commits.create(
            branch="feature/x",
            message="msg",
            author_name="Alice",
            author_email="alice@example.com",
            base_branch="main",
        )
        assert isinstance(builder, CommitBuilder)
