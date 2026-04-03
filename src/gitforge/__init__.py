"""GitForge Python SDK."""

from .client import GitForge, RepoScope
from .errors import GitForgeError, RefUpdateError
from .pagination import paginate
from .types import (
    Repo, Branch, Tag, Commit, CommitDetail, DiffEntry,
    TreeEntry, BlobContent, SearchMatch, SearchResult,
    SearchCodeResult, Comparison, CommitResult, RepoToken,
    SandboxUrl, GitCredential, MirrorConfig, Webhook, WebhookDelivery,
    WebhookTestResult, PaginatedResponse, CommitFileEntry,
    PromoteResult, PatchSet, PatchSetPatch, PatchSetWithPatches,
    HotFile, HotTreeEntry, HotTreeResult, HotCommitResult, HotRefEntry,
    BatchSummary, BatchItem, BatchResponse, Job, StreamEvent,
    ShellExecResult, ShellMount, ShellMultiExecResult, ShellDestroyResult,
)
from .resources.commits import CommitBuilder
from .webhooks.validate import validate_webhook, validate_webhook_signature

__all__ = [
    "GitForge",
    "RepoScope",
    "GitForgeError",
    "RefUpdateError",
    "paginate",
    "CommitBuilder",
    "validate_webhook",
    "validate_webhook_signature",
    # Types
    "Repo", "Branch", "Tag", "Commit", "CommitDetail", "DiffEntry",
    "TreeEntry", "BlobContent", "SearchMatch", "SearchResult",
    "SearchCodeResult", "Comparison", "CommitResult", "RepoToken",
    "SandboxUrl", "GitCredential", "MirrorConfig", "Webhook", "WebhookDelivery",
    "WebhookTestResult", "PaginatedResponse", "CommitFileEntry",
    "PromoteResult", "PatchSet", "PatchSetPatch", "PatchSetWithPatches",
    # Core primitives types
    "HotFile", "HotTreeEntry", "HotTreeResult", "HotCommitResult", "HotRefEntry",
    "BatchSummary", "BatchItem", "BatchResponse", "Job", "StreamEvent",
    # Shell types
    "ShellExecResult", "ShellMount", "ShellMultiExecResult", "ShellDestroyResult",
]
