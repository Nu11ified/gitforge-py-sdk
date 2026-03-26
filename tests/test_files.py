from __future__ import annotations

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.files import FilesResource
from gitforge.types import TreeEntry, BlobContent


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
TREE_URL = f"{BASE_URL}/repos/{REPO_ID}/tree"
BLOB_URL = f"{BASE_URL}/repos/{REPO_ID}/blob"

TREE_ENTRY_JSON = {
    "name": "README.md",
    "type": "blob",
    "mode": "100644",
    "sha": "abc123def456789",
}

BLOB_JSON = {
    "content": "# Hello World\n",
    "size": 15,
}


def _tree_entry(**overrides: object) -> dict:
    d = dict(TREE_ENTRY_JSON)
    d.update(overrides)
    return d


def _blob(**overrides: object) -> dict:
    d = dict(BLOB_JSON)
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def files(http_client: HttpClient) -> FilesResource:
    return FilesResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------


class TestListFiles:
    async def test_lists_files_at_root_with_default_ref(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        entries = [TREE_ENTRY_JSON]
        route = mock_router.get(f"{TREE_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=entries)
        )
        result = await files.list_files()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        url_str = str(request.url)
        assert f"/repos/{REPO_ID}/tree/HEAD" in url_str
        assert "path=" not in url_str
        assert "ephemeral=" not in url_str

    async def test_lists_files_at_specific_path(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        entries = [_tree_entry(name="index.ts")]
        route = mock_router.get(f"{TREE_URL}/main").mock(
            return_value=httpx.Response(200, json=entries)
        )
        result = await files.list_files(ref="main", path="src")
        url_str = str(route.calls[0].request.url)
        assert "path=src" in url_str
        assert len(result) == 1
        assert result[0].name == "index.ts"

    async def test_lists_files_with_ephemeral_flag(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        entries = [TREE_ENTRY_JSON]
        route = mock_router.get(f"{TREE_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=entries)
        )
        result = await files.list_files(ephemeral=True)
        url_str = str(route.calls[0].request.url)
        assert "ephemeral=true" in url_str

    async def test_returns_list_of_tree_entry_dataclasses(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        entries = [
            _tree_entry(name="file.txt", type="blob", mode="100644", sha="aaa111"),
            _tree_entry(name="lib", type="tree", mode="040000", sha="bbb222"),
            _tree_entry(name="run.sh", type="blob", mode="100755", sha="ccc333"),
        ]
        mock_router.get(f"{TREE_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=entries)
        )
        result = await files.list_files()
        assert len(result) == 3
        assert all(isinstance(e, TreeEntry) for e in result)
        assert result[0].name == "file.txt"
        assert result[0].type == "blob"
        assert result[0].mode == "100644"
        assert result[0].sha == "aaa111"
        assert result[1].name == "lib"
        assert result[1].type == "tree"
        assert result[2].name == "run.sh"
        assert result[2].mode == "100755"


# ---------------------------------------------------------------------------
# get_file
# ---------------------------------------------------------------------------


class TestGetFile:
    async def test_gets_file_content_by_path(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(f"{BLOB_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=BLOB_JSON)
        )
        result = await files.get_file("README.md")
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        url_str = str(request.url)
        assert "path=README.md" in url_str
        assert result.content == "# Hello World\n"
        assert result.size == 15

    async def test_gets_file_at_specific_ref(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        blob = _blob(content="v2 content", size=10)
        route = mock_router.get(f"{BLOB_URL}/abc123").mock(
            return_value=httpx.Response(200, json=blob)
        )
        result = await files.get_file("src/main.py", ref="abc123")
        url_str = str(route.calls[0].request.url)
        assert f"/blob/abc123" in url_str
        assert "path=src%2Fmain.py" in url_str or "path=src/main.py" in url_str
        assert result.content == "v2 content"

    async def test_gets_file_with_ephemeral_flag(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(f"{BLOB_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=BLOB_JSON)
        )
        result = await files.get_file("README.md", ephemeral=True)
        url_str = str(route.calls[0].request.url)
        assert "ephemeral=true" in url_str
        assert "path=README.md" in url_str

    async def test_returns_blob_content_with_content_and_size(
        self, files: FilesResource, mock_router: respx.MockRouter
    ) -> None:
        blob = _blob(content="const x = 42;", size=13)
        mock_router.get(f"{BLOB_URL}/HEAD").mock(
            return_value=httpx.Response(200, json=blob)
        )
        result = await files.get_file("test.js")
        assert isinstance(result, BlobContent)
        assert result.content == "const x = 42;"
        assert result.size == 13
