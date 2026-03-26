from __future__ import annotations

from typing import Optional

import httpx

from .http import HttpClient
from .resources.repos import ReposResource
from .resources.branches import BranchesResource
from .resources.tags import TagsResource
from .resources.commits import CommitsResource
from .resources.files import FilesResource
from .resources.search import SearchResource
from .resources.tokens import TokensResource
from .resources.credentials import CredentialsResource
from .resources.mirrors import MirrorsResource
from .resources.webhooks import WebhooksResource


class RepoScope:
    """Scoped access to repo-level resources."""

    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self.branches = BranchesResource(http, repo_id)
        self.tags = TagsResource(http, repo_id)
        self.commits = CommitsResource(http, repo_id)
        self.files = FilesResource(http, repo_id)
        self.search = SearchResource(http, repo_id)
        self.tokens = TokensResource(http, repo_id)
        self.mirrors = MirrorsResource(http, repo_id)
        self.webhooks = WebhooksResource(http, repo_id)


class GitForge:
    def __init__(
        self,
        base_url: str,
        token: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._http = HttpClient(base_url=base_url, token=token, client=client)
        self.repos = ReposResource(self._http)
        self.credentials = CredentialsResource(self._http)

    def repo(self, repo_id: str) -> RepoScope:
        return RepoScope(self._http, repo_id)
