# gitforge

Python SDK for [GitForge](https://git-forge.dev) — Git infrastructure for developers who build on Git.

## Install

```bash
pip install gitforge
```

Requires Python 3.10+.

## Quick Start

```python
from gitforge import GitForge

client = GitForge(
    base_url="https://api.git-forge.dev",
    token="gf_your_token_here",
)

# Create a repo
repo = await client.repos.create(
    name="my-repo",
    visibility="private",
)

# Commit files without a git client
await client.repo(repo.id).commits \
    .create(
        branch="main",
        message="initial commit",
        author_name="Your Name",
        author_email="you@example.com",
    ) \
    .add_file("README.md", "# My Project") \
    .add_file("src/main.py", "print('hello')") \
    .send()

# List repos
repos = await client.repos.list(limit=10)

# Search code
results = await client.search.code("def handle_push")
```

## Resources

| Resource | Methods |
|----------|---------|
| `repos` | `create`, `list`, `get`, `update`, `delete` |
| `branches` | `list`, `create`, `delete`, `promote` |
| `tags` | `list`, `create`, `delete` |
| `commits` | `create` (builder), `list`, `get` |
| `files` | `get_blob`, `get_tree` |
| `search` | `code` |
| `tokens` | `create`, `list`, `revoke` |
| `mirrors` | `list`, `create`, `sync`, `delete` |
| `webhooks` | `create`, `list`, `update`, `delete`, `test` |

## Webhook Validation

```python
from gitforge.webhooks import validate_webhook

is_valid = validate_webhook(
    payload=raw_body,
    signature=request.headers["x-gitforge-signature"],
    secret="your_webhook_secret",
    timestamp=request.headers.get("x-gitforge-timestamp"),
    tolerance=300,
)
```

## Error Handling

```python
from gitforge import GitForgeError

try:
    await client.repos.get("nonexistent")
except GitForgeError as e:
    print(e.status)   # 404
    print(e.code)     # "NOT_FOUND"
    print(e.message)
```

## Contributing

This SDK is developed inside the [GitForge monorepo](https://github.com/Nu11ified/GitForge) at `sdks/python/` and published to this repo via git subtree.

To contribute:

1. Clone the monorepo: `git clone https://github.com/Nu11ified/GitForge.git`
2. Install dependencies: `pip install -e sdks/python[dev]`
3. Make changes in `sdks/python/`
4. Run tests: `pytest sdks/python/`
5. Submit a PR to the monorepo

## License

MIT
