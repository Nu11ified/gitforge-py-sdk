from __future__ import annotations

import json
from urllib.parse import quote

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.branches import BranchesResource
from gitforge.types import Branch, PaginatedResponse, PromoteResult


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
BRANCHES_URL = f"{BASE_URL}/repos/{REPO_ID}/branches"

BRANCH_JSON = {
    "name": "main",
    "sha": "abc123def456789",
}


def _branch_json(**overrides: object) -> dict:
    d = dict(BRANCH_JSON)
    d.update(overrides)
    return d


def _paginated(branches: list[dict], **overrides: object) -> dict:
    d: dict = {
        "data": branches,
        "total": len(branches),
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
def branches(http_client: HttpClient) -> BranchesResource:
    return BranchesResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_lists_branches_with_default_params(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated([BRANCH_JSON])
        route = mock_router.get(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await branches.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        url_str = str(request.url)
        assert "limit=" not in url_str
        assert "offset=" not in url_str
        assert "namespace=" not in url_str

    async def test_lists_branches_with_namespace_ephemeral(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        ephemeral_branch = _branch_json(
            name="ephemeral/preview-1",
            expiresAt="2026-04-01T00:00:00.000Z",
        )
        paginated = _paginated([ephemeral_branch])
        route = mock_router.get(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await branches.list(namespace="ephemeral")
        url_str = str(route.calls[0].request.url)
        assert "namespace=ephemeral" in url_str
        assert result.data[0].name == "ephemeral/preview-1"
        assert result.data[0].expires_at == "2026-04-01T00:00:00.000Z"

    async def test_returns_paginated_response_with_branch_objects(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        b1 = _branch_json(name="main", sha="aaa111")
        b2 = _branch_json(name="develop", sha="bbb222")
        paginated = _paginated([b1, b2], total=2)
        mock_router.get(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await branches.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(b, Branch) for b in result.data)
        assert result.data[0].name == "main"
        assert result.data[1].name == "develop"
        assert result.total == 2
        assert result.has_more is False

    async def test_passes_limit_and_offset(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated(
            [BRANCH_JSON], total=100, limit=10, offset=20, hasMore=True
        )
        route = mock_router.get(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await branches.list(limit=10, offset=20)
        url_str = str(route.calls[0].request.url)
        assert "limit=10" in url_str
        assert "offset=20" in url_str
        assert result.limit == 10
        assert result.offset == 20
        assert result.has_more is True


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_creates_branch_with_name_and_sha(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        branch_data = _branch_json(name="feature/new", sha="def456abc789")
        route = mock_router.post(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=branch_data)
        )
        result = await branches.create("feature/new", sha="def456abc789")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"name": "feature/new", "sha": "def456abc789"}
        assert isinstance(result, Branch)
        assert result.name == "feature/new"
        assert result.sha == "def456abc789"

    async def test_creates_ephemeral_branch_with_ttl_seconds(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        branch_data = _branch_json(
            name="preview/deploy-42",
            sha="aaa111bbb222",
            expiresAt="2026-03-27T01:00:00.000Z",
        )
        route = mock_router.post(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=branch_data)
        )
        result = await branches.create(
            "preview/deploy-42",
            sha="aaa111bbb222",
            target_is_ephemeral=True,
            ttl_seconds=86400,
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "name": "preview/deploy-42",
            "sha": "aaa111bbb222",
            "targetIsEphemeral": True,
            "ttlSeconds": 86400,
        }
        assert result.expires_at == "2026-03-27T01:00:00.000Z"

    async def test_creates_branch_from_base_branch(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        branch_data = _branch_json(name="feature/new", sha="def456abc789")
        route = mock_router.post(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=branch_data)
        )
        result = await branches.create("feature/new", base_branch="main")
        body = json.loads(route.calls[0].request.content)
        assert body == {"name": "feature/new", "baseBranch": "main"}
        assert isinstance(result, Branch)

    async def test_creates_branch_with_base_is_ephemeral(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        branch_data = _branch_json(name="promoted", sha="abc123")
        route = mock_router.post(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=branch_data)
        )
        result = await branches.create(
            "promoted",
            base_branch="ephemeral/preview-1",
            base_is_ephemeral=True,
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "name": "promoted",
            "baseBranch": "ephemeral/preview-1",
            "baseIsEphemeral": True,
        }

    async def test_returns_branch_dataclass(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(BRANCHES_URL).mock(
            return_value=httpx.Response(200, json=BRANCH_JSON)
        )
        result = await branches.create("main", sha="abc123def456789")
        assert isinstance(result, Branch)
        assert result.name == "main"
        assert result.sha == "abc123def456789"
        assert result.expires_at is None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_deletes_branch_by_name(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(f"{BRANCHES_URL}/main").mock(
            return_value=httpx.Response(204)
        )
        result = await branches.delete("main")
        assert route.called
        assert route.calls[0].request.method == "DELETE"
        assert result is None

    async def test_deletes_with_namespace_query_param(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        encoded = quote("ephemeral/preview-1", safe="")
        route = mock_router.delete(f"{BRANCHES_URL}/{encoded}").mock(
            return_value=httpx.Response(204)
        )
        result = await branches.delete("ephemeral/preview-1", namespace="ephemeral")
        url_str = str(route.calls[0].request.url)
        assert "namespace=ephemeral" in url_str
        assert result is None

    async def test_url_encodes_special_characters_in_branch_name(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        encoded = quote("feature/my-branch", safe="")
        route = mock_router.delete(f"{BRANCHES_URL}/{encoded}").mock(
            return_value=httpx.Response(204)
        )
        await branches.delete("feature/my-branch")
        request_url = str(route.calls[0].request.url)
        # The slash must be encoded as %2F
        assert f"/branches/feature%2Fmy-branch" in request_url

    async def test_url_encodes_multiple_special_chars(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        branch_name = "feat/foo bar+baz"
        encoded = quote(branch_name, safe="")
        route = mock_router.delete(f"{BRANCHES_URL}/{encoded}").mock(
            return_value=httpx.Response(204)
        )
        await branches.delete(branch_name)
        request_url = str(route.calls[0].request.url)
        assert encoded in request_url


# ---------------------------------------------------------------------------
# promote
# ---------------------------------------------------------------------------


class TestPromote:
    async def test_promotes_with_base_branch_only(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        promote_data = {"targetBranch": "main", "commitSha": "abc123"}
        route = mock_router.post(f"{BRANCHES_URL}/promote").mock(
            return_value=httpx.Response(200, json=promote_data)
        )
        result = await branches.promote(base_branch="staging")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"baseBranch": "staging"}
        assert result.target_branch == "main"
        assert result.commit_sha == "abc123"

    async def test_promotes_with_base_and_target_branch(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        promote_data = {"targetBranch": "release/v2", "commitSha": "def456"}
        route = mock_router.post(f"{BRANCHES_URL}/promote").mock(
            return_value=httpx.Response(200, json=promote_data)
        )
        result = await branches.promote(
            base_branch="develop", target_branch="release/v2"
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {"baseBranch": "develop", "targetBranch": "release/v2"}
        assert result.target_branch == "release/v2"
        assert result.commit_sha == "def456"

    async def test_returns_promote_result_dataclass(
        self, branches: BranchesResource, mock_router: respx.MockRouter
    ) -> None:
        promote_data = {"targetBranch": "main", "commitSha": "fff999"}
        mock_router.post(f"{BRANCHES_URL}/promote").mock(
            return_value=httpx.Response(200, json=promote_data)
        )
        result = await branches.promote(base_branch="staging")
        assert isinstance(result, PromoteResult)
        assert result.target_branch == "main"
        assert result.commit_sha == "fff999"
