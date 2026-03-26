from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.tokens import TokensResource
from gitforge.types import RepoToken


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
TOKENS_URL = f"{BASE_URL}/repos/{REPO_ID}/tokens"

TOKEN_JSON = {
    "token": "gf_repo_abc123xyz",
    "patId": "pat-0001-0002-0003",
    "expiresAt": "2026-03-26T01:00:00.000Z",
    "remoteUrl": "https://x:gf_repo_abc123xyz@gitforge.dev/testuser/my-repo.git",
}


def _token_json(**overrides: object) -> dict:
    d = dict(TOKEN_JSON)
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tokens(http_client: HttpClient) -> TokensResource:
    return TokensResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_creates_token_with_ttl_seconds(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        await tokens.create(ttl_seconds=3600)
        body = json.loads(route.calls[0].request.content)
        assert body == {"ttlSeconds": 3600}

    async def test_creates_token_with_scopes(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        await tokens.create(ttl_seconds=3600, scopes=["read", "write"])
        body = json.loads(route.calls[0].request.content)
        assert body == {"ttlSeconds": 3600, "scopes": ["read", "write"]}

    async def test_creates_token_with_type(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        await tokens.create(ttl_seconds=3600, type="ci")
        body = json.loads(route.calls[0].request.content)
        assert body == {"ttlSeconds": 3600, "type": "ci"}

    async def test_creates_token_with_all_options(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        await tokens.create(ttl_seconds=1800, scopes=["read"], type="deploy")
        body = json.loads(route.calls[0].request.content)
        assert body == {"ttlSeconds": 1800, "scopes": ["read"], "type": "deploy"}

    async def test_returns_repo_token_with_correct_fields(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        result = await tokens.create(ttl_seconds=3600)
        assert isinstance(result, RepoToken)
        assert result.token == "gf_repo_abc123xyz"
        assert result.pat_id == "pat-0001-0002-0003"
        assert result.expires_at == "2026-03-26T01:00:00.000Z"
        assert result.remote_url == (
            "https://x:gf_repo_abc123xyz@gitforge.dev/testuser/my-repo.git"
        )

    async def test_sends_post_to_correct_url(
        self, tokens: TokensResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(TOKENS_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_JSON)
        )
        await tokens.create(ttl_seconds=3600)
        request = route.calls[0].request
        assert str(request.url) == TOKENS_URL
        assert request.method == "POST"
