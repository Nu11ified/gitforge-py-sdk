from __future__ import annotations

import httpx
import pytest
import respx
from gitforge.http import HttpClient


@pytest.fixture
def base_url() -> str:
    return "https://api.gitforge.dev"


@pytest.fixture
def token() -> str:
    return "gf_test_token_abc123"


@pytest.fixture
def mock_router() -> respx.MockRouter:
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def http_client(base_url: str, token: str, mock_router: respx.MockRouter) -> HttpClient:
    client = httpx.AsyncClient()
    return HttpClient(base_url=base_url, token=token, client=client)
