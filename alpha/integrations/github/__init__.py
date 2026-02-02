"""
Alpha GitHub Integration

Comprehensive GitHub API integration for repository, issue, and pull request management.

Features:
- Repository operations (list, info, content)
- Issue management (list, view, create, update, comment)
- Pull request management (list, view, status)
- Commit and branch information
- Proactive GitHub intelligence
- Secure token-based authentication

Usage:
    from alpha.integrations.github import GitHubClient

    client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    repos = await client.list_repositories()
    issues = await client.list_issues("owner/repo")
"""

from alpha.integrations.github.client import GitHubClient
from alpha.integrations.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubPermissionError,
)

__version__ = "1.0.0"

__all__ = [
    "GitHubClient",
    "GitHubError",
    "GitHubAuthenticationError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
    "GitHubPermissionError",
]
