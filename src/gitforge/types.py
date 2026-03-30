from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


@dataclass
class Repo:
    id: str
    name: str
    visibility: str = "private"
    default_branch: str = "main"
    lfs_enabled: bool = False
    is_archived: bool = False
    slug: Optional[str] = None
    owner_slug: Optional[str] = None
    description: Optional[str] = None
    forked_from: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    star_count: Optional[int] = None
    open_pr_count: Optional[int] = None
    open_issue_count: Optional[int] = None
    topics: Optional[list[str]] = None
    merge_commit_template: Optional[str] = None


@dataclass
class Branch:
    name: str
    sha: str
    expires_at: Optional[str] = None


@dataclass
class Tag:
    name: str
    sha: str


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    author_email: str
    date: str
    parent_shas: list[str] = field(default_factory=list)


@dataclass
class CommitDetail(Commit):
    tree: str = ""
    files: list[dict[str, str]] = field(default_factory=list)


@dataclass
class DiffEntry:
    path: str
    status: str
    additions: int = 0
    deletions: int = 0
    patch: str = ""


@dataclass
class TreeEntry:
    name: str
    type: str
    mode: str
    sha: str


@dataclass
class BlobContent:
    content: str
    size: int = 0


@dataclass
class SearchMatch:
    line: int
    content: str
    highlight: str = ""


@dataclass
class SearchResult:
    repo_id: str
    repo_name: str
    file_path: str
    branch: str
    matches: list[SearchMatch] = field(default_factory=list)
    language: Optional[str] = None


@dataclass
class SearchCodeResult:
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 20


@dataclass
class Comparison:
    ahead: int = 0
    behind: int = 0
    commits: list[dict[str, str]] = field(default_factory=list)
    files: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CommitResult:
    commit_sha: str
    tree_sha: str
    branch: str
    ref: str
    parent_shas: list[str] = field(default_factory=list)
    old_sha: str = ""
    new_sha: str = ""


@dataclass
class RepoToken:
    token: str
    pat_id: str
    expires_at: str
    remote_url: str


@dataclass
class SandboxUrl:
    remote_url: str
    token: str
    expires_at: str
    branch: str
    ephemeral_branch: Optional[str] = None


@dataclass
class GitCredential:
    id: str
    provider: str
    created_at: str
    username: Optional[str] = None
    label: Optional[str] = None


@dataclass
class MirrorConfig:
    id: str
    source_url: str
    created_at: str
    interval: int = 0
    enabled: bool = True
    direction: str = "pull"
    provider: str = ""
    last_sync_at: Optional[str] = None
    last_error: Optional[str] = None
    credential_id: Optional[str] = None


@dataclass
class Webhook:
    id: str
    url: str
    active: bool = True
    events: Optional[list[str]] = None


@dataclass
class WebhookDelivery:
    id: str
    event_type: str
    created_at: str
    payload: str = ""
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[str] = None


@dataclass
class WebhookTestResult:
    success: bool
    status: Optional[int] = None
    response_body: Optional[str] = None
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class PaginatedResponse(Generic[T]):
    data: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class CommitFileEntry:
    path: str
    content: str
    encoding: str = "utf8"
    mode: str = "100644"


@dataclass
class PromoteResult:
    target_branch: str
    commit_sha: str


@dataclass
class PatchSet:
    id: str
    repo_id: str
    name: str
    base_ref: str = "main"
    base_sha: str = ""
    status: str = "clean"
    auto_rebase: bool = False
    visibility: str = "private"
    description: Optional[str] = None
    materialized_branch: Optional[str] = None
    materialized_sha: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class PatchSetPatch:
    id: str
    name: str
    order: int = 0
    diff: str = ""
    status: str = "enabled"
    description: Optional[str] = None
    conflict_details: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class PatchSetWithPatches(PatchSet):
    patches: list[PatchSetPatch] = field(default_factory=list)
