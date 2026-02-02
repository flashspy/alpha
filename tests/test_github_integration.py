"""
Tests for GitHub Integration

Comprehensive test suite covering:
- Exception classes
- Data models
- GitHubClient (with mocked API)
- GitHubTool integration
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

from alpha.integrations.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubPermissionError,
)
from alpha.integrations.github.models import (
    GitHubUser,
    Repository,
    Label,
    Issue,
    PullRequest,
    Comment,
    Commit,
)
from alpha.integrations.github import GitHubClient
from alpha.tools.github_tool import GitHubTool


# ===== Exception Tests =====


def test_github_error_basic():
    """Test GitHubError exception."""
    error = GitHubError("Test error")
    assert str(error) == "Test error"
    assert error.status_code is None


def test_github_error_with_status():
    """Test GitHubError with status code."""
    error = GitHubError("Test error", status_code=500)
    assert "[500]" in str(error)
    assert error.status_code == 500


def test_github_authentication_error():
    """Test GitHubAuthenticationError."""
    error = GitHubAuthenticationError()
    assert "authentication failed" in str(error).lower()


def test_github_rate_limit_error():
    """Test GitHubRateLimitError."""
    error = GitHubRateLimitError(reset_time=1234567890)
    assert error.reset_time == 1234567890


def test_github_not_found_error():
    """Test GitHubNotFoundError."""
    error = GitHubNotFoundError()
    assert error.status_code == 404


# ===== Data Model Tests =====


def test_github_user_from_dict():
    """Test GitHubUser.from_dict()."""
    data = {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
        "type": "User",
        "name": "The Octocat",
    }
    user = GitHubUser.from_dict(data)
    assert user.login == "octocat"
    assert user.id == 1
    assert user.name == "The Octocat"


def test_repository_from_dict():
    """Test Repository.from_dict()."""
    data = {
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "html_url": "https://github.com/octocat",
        },
        "html_url": "https://github.com/octocat/Hello-World",
        "description": "My first repository",
        "private": False,
        "fork": False,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:14:43Z",
        "pushed_at": "2011-01-26T19:06:43Z",
        "size": 180,
        "stargazers_count": 80,
        "watchers_count": 80,
        "forks_count": 9,
        "open_issues_count": 0,
        "default_branch": "main",
        "language": "Python",
    }
    repo = Repository.from_dict(data)
    assert repo.name == "Hello-World"
    assert repo.full_name == "octocat/Hello-World"
    assert repo.owner.login == "octocat"
    assert repo.stargazers_count == 80
    assert repo.language == "Python"


def test_issue_from_dict():
    """Test Issue.from_dict()."""
    data = {
        "id": 1,
        "number": 1347,
        "title": "Found a bug",
        "body": "I'm having a problem with this.",
        "state": "open",
        "user": {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "html_url": "https://github.com/octocat",
        },
        "labels": [{"id": 1, "name": "bug", "color": "f29513"}],
        "assignees": [],
        "milestone": None,
        "comments": 0,
        "created_at": "2011-04-22T13:33:48Z",
        "updated_at": "2011-04-22T13:33:48Z",
        "closed_at": None,
        "html_url": "https://github.com/octocat/Hello-World/issues/1347",
        "repository_url": "https://api.github.com/repos/octocat/Hello-World",
    }
    issue = Issue.from_dict(data)
    assert issue.number == 1347
    assert issue.title == "Found a bug"
    assert issue.state == "open"
    assert issue.user.login == "octocat"
    assert len(issue.labels) == 1
    assert issue.labels[0].name == "bug"


def test_pull_request_from_dict():
    """Test PullRequest.from_dict()."""
    data = {
        "id": 1,
        "number": 1,
        "title": "Amazing new feature",
        "body": "Please pull this in!",
        "state": "open",
        "user": {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "html_url": "https://github.com/octocat",
        },
        "head": {"ref": "new-feature"},
        "base": {"ref": "main"},
        "draft": False,
        "merged": False,
        "mergeable": True,
        "mergeable_state": "clean",
        "labels": [],
        "assignees": [],
        "milestone": None,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "merged_at": None,
        "closed_at": None,
        "html_url": "https://github.com/octocat/Hello-World/pull/1",
        "commits": 3,
        "additions": 100,
        "deletions": 3,
        "changed_files": 5,
    }
    pr = PullRequest.from_dict(data)
    assert pr.number == 1
    assert pr.title == "Amazing new feature"
    assert pr.head_ref == "new-feature"
    assert pr.base_ref == "main"
    assert pr.mergeable is True
    assert pr.commits == 3


# ===== GitHubClient Tests (Mocked) =====


@pytest.fixture
def mock_session():
    """Create a mock requests.Session."""
    session = MagicMock()
    session.headers = {}
    return session


@pytest.fixture
def github_client(monkeypatch):
    """Create GitHubClient with mocked session."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-12345")

    with patch("alpha.integrations.github.client.requests.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        client = GitHubClient(token="test-token-12345")
        client.session = mock_session

        yield client


def test_client_initialization():
    """Test GitHubClient initialization."""
    with patch("alpha.integrations.github.client.requests.Session"):
        client = GitHubClient(token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://api.github.com"


def test_client_requires_token():
    """Test that GitHubClient requires a token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(GitHubAuthenticationError):
            GitHubClient()


def test_client_make_request_success(github_client):
    """Test successful API request."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    result = github_client._make_request("GET", "test")
    assert result == {"key": "value"}


def test_client_make_request_404(github_client):
    """Test API request with 404 error."""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Not Found"}
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    with pytest.raises(GitHubNotFoundError):
        github_client._make_request("GET", "test")


def test_client_make_request_401(github_client):
    """Test API request with 401 authentication error."""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.json.return_value = {"message": "Bad credentials"}
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    with pytest.raises(GitHubAuthenticationError):
        github_client._make_request("GET", "test")


def test_client_make_request_rate_limit(github_client):
    """Test API request with rate limit error."""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 403
    mock_response.json.return_value = {"message": "API rate limit exceeded"}
    mock_response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1234567890",
    }

    github_client.session.request.return_value = mock_response

    with pytest.raises(GitHubRateLimitError):
        github_client._make_request("GET", "test")


def test_client_list_repositories(github_client):
    """Test list_repositories method."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "name": "repo1",
            "full_name": "user/repo1",
            "owner": {
                "login": "user",
                "id": 1,
                "avatar_url": "url",
                "html_url": "url",
            },
            "html_url": "https://github.com/user/repo1",
            "description": "Test repo",
            "private": False,
            "fork": False,
            "created_at": "2011-01-26T19:01:12Z",
            "updated_at": "2011-01-26T19:01:12Z",
            "pushed_at": "2011-01-26T19:01:12Z",
            "size": 100,
            "stargazers_count": 10,
            "watchers_count": 10,
            "forks_count": 2,
            "open_issues_count": 1,
            "default_branch": "main",
        }
    ]
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    repos = github_client.list_repositories()
    assert len(repos) == 1
    assert repos[0].name == "repo1"


def test_client_get_repository(github_client):
    """Test get_repository method."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {
            "login": "octocat",
            "id": 1,
            "avatar_url": "url",
            "html_url": "url",
        },
        "html_url": "https://github.com/octocat/Hello-World",
        "description": "My first repository",
        "private": False,
        "fork": False,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "pushed_at": "2011-01-26T19:01:12Z",
        "size": 180,
        "stargazers_count": 80,
        "watchers_count": 80,
        "forks_count": 9,
        "open_issues_count": 0,
        "default_branch": "main",
    }
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    repo = github_client.get_repository("octocat", "Hello-World")
    assert repo.name == "Hello-World"
    assert repo.stargazers_count == 80


def test_client_create_issue(github_client):
    """Test create_issue method."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 1,
        "number": 1,
        "title": "Test Issue",
        "body": "Test body",
        "state": "open",
        "user": {
            "login": "user",
            "id": 1,
            "avatar_url": "url",
            "html_url": "url",
        },
        "labels": [],
        "assignees": [],
        "milestone": None,
        "comments": 0,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": None,
        "html_url": "https://github.com/user/repo/issues/1",
        "repository_url": "url",
    }
    mock_response.headers = {"X-RateLimit-Remaining": "5000"}

    github_client.session.request.return_value = mock_response

    issue = github_client.create_issue("user", "repo", "Test Issue", "Test body")
    assert issue.title == "Test Issue"
    assert issue.number == 1


# ===== GitHubTool Tests =====


@pytest.fixture
def github_tool(monkeypatch):
    """Create GitHubTool with mocked client."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-12345")
    tool = GitHubTool()
    return tool


@pytest.mark.asyncio
async def test_github_tool_initialization(monkeypatch):
    """Test GitHubTool initialization."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    tool = GitHubTool()
    assert tool.name == "github"
    assert tool.token == "test-token"


@pytest.mark.asyncio
async def test_github_tool_no_token():
    """Test GitHubTool without token."""
    with patch.dict(os.environ, {}, clear=True):
        tool = GitHubTool()
        result = await tool.execute(operation="list_repos")
        assert result.success is False
        assert "token" in result.error.lower()


@pytest.mark.asyncio
async def test_github_tool_list_repos(github_tool):
    """Test GitHubTool list_repos operation."""
    with patch.object(GitHubClient, "list_repositories") as mock_list:
        mock_repo = Mock()
        mock_repo.full_name = "user/repo"
        mock_repo.description = "Test repo"
        mock_repo.stargazers_count = 10
        mock_repo.forks_count = 2
        mock_repo.language = "Python"
        mock_repo.html_url = "https://github.com/user/repo"
        mock_repo.private = False
        mock_repo.updated_at = datetime(2024, 1, 1)

        mock_list.return_value = [mock_repo]

        result = await github_tool.execute(operation="list_repos")

        assert result.success is True
        assert result.output["count"] == 1
        assert result.output["repositories"][0]["name"] == "user/repo"


@pytest.mark.asyncio
async def test_github_tool_get_repo(github_tool):
    """Test GitHubTool get_repo operation."""
    with patch.object(GitHubClient, "get_repository") as mock_get:
        mock_repo = Mock()
        mock_repo.full_name = "octocat/Hello-World"
        mock_repo.description = "My first repository"
        mock_repo.stargazers_count = 80
        mock_repo.forks_count = 9
        mock_repo.watchers_count = 80
        mock_repo.open_issues_count = 0
        mock_repo.language = "Python"
        mock_repo.default_branch = "main"
        mock_repo.topics = ["python", "testing"]
        mock_repo.clone_url = "https://github.com/octocat/Hello-World.git"
        mock_repo.ssh_url = "git@github.com:octocat/Hello-World.git"
        mock_repo.created_at = datetime(2011, 1, 26)
        mock_repo.updated_at = datetime(2011, 1, 26)
        mock_repo.pushed_at = datetime(2011, 1, 26)
        mock_repo.html_url = "https://github.com/octocat/Hello-World"
        mock_repo.private = False
        mock_repo.archived = False

        mock_get.return_value = mock_repo

        result = await github_tool.execute(
            operation="get_repo", owner="octocat", repo="Hello-World"
        )

        assert result.success is True
        assert result.output["name"] == "octocat/Hello-World"
        assert result.output["stars"] == 80


@pytest.mark.asyncio
async def test_github_tool_create_issue(github_tool):
    """Test GitHubTool create_issue operation."""
    with patch.object(GitHubClient, "create_issue") as mock_create:
        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/user/repo/issues/1"
        mock_issue.state = "open"

        mock_create.return_value = mock_issue

        result = await github_tool.execute(
            operation="create_issue",
            owner="user",
            repo="repo",
            title="Test Issue",
            body="Test body",
        )

        assert result.success is True
        assert result.output["number"] == 1
        assert result.output["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_github_tool_unknown_operation(github_tool):
    """Test GitHubTool with unknown operation."""
    result = await github_tool.execute(operation="unknown_op")
    assert result.success is False
    assert "unknown operation" in result.error.lower()


@pytest.mark.asyncio
async def test_github_tool_missing_params(github_tool):
    """Test GitHubTool with missing required parameters."""
    result = await github_tool.execute(operation="get_repo")
    assert result.success is False
    assert "owner and repo" in result.error.lower()


# ===== Pull Request Creation Tests =====


@pytest.mark.asyncio
async def test_client_create_pull_request():
    """Test GitHubClient.create_pull_request()."""
    with patch("requests.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "number": 1347,
            "title": "Amazing new feature",
            "body": "Please merge this",
            "state": "open",
            "user": {
                "login": "octocat",
                "id": 1,
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "html_url": "https://github.com/octocat",
            },
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "draft": False,
            "merged": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "labels": [],
            "assignees": [],
            "milestone": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "merged_at": None,
            "closed_at": None,
            "html_url": "https://github.com/octocat/Hello-World/pull/1347",
            "commits": 1,
            "additions": 100,
            "deletions": 3,
            "changed_files": 5,
        }
        mock_response.headers = {
            "X-RateLimit-Remaining": "5000",
            "X-RateLimit-Reset": "1234567890",
        }

        mock_session.request.return_value = mock_response

        client = GitHubClient(token="fake_token")
        pr = client.create_pull_request(
            owner="octocat",
            repo="Hello-World",
            title="Amazing new feature",
            head="feature-branch",
            base="main",
            body="Please merge this",
        )

        assert pr.number == 1347
        assert pr.title == "Amazing new feature"
        assert pr.head_ref == "feature-branch"
        assert pr.base_ref == "main"
        assert pr.draft is False
        assert pr.state == "open"


@pytest.mark.asyncio
async def test_client_create_draft_pull_request():
    """Test GitHubClient.create_pull_request() with draft=True."""
    with patch("requests.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 2,
            "number": 1348,
            "title": "Work in progress",
            "body": "Not ready yet",
            "state": "open",
            "user": {
                "login": "octocat",
                "id": 1,
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "html_url": "https://github.com/octocat",
            },
            "head": {"ref": "wip-feature"},
            "base": {"ref": "main"},
            "draft": True,
            "merged": False,
            "mergeable": None,
            "mergeable_state": "unknown",
            "labels": [],
            "assignees": [],
            "milestone": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "merged_at": None,
            "closed_at": None,
            "html_url": "https://github.com/octocat/Hello-World/pull/1348",
            "commits": 2,
            "additions": 50,
            "deletions": 10,
            "changed_files": 3,
        }
        mock_response.headers = {
            "X-RateLimit-Remaining": "5000",
            "X-RateLimit-Reset": "1234567890",
        }

        mock_session.request.return_value = mock_response

        client = GitHubClient(token="fake_token")
        pr = client.create_pull_request(
            owner="octocat",
            repo="Hello-World",
            title="Work in progress",
            head="wip-feature",
            base="main",
            body="Not ready yet",
            draft=True,
        )

        assert pr.number == 1348
        assert pr.draft is True
        assert pr.title == "Work in progress"


@pytest.mark.asyncio
async def test_github_tool_create_pr_success(github_tool):
    """Test GitHubTool create_pr operation - success case."""
    with patch.object(GitHubClient, "create_pull_request") as mock_create:
        mock_pr = Mock()
        mock_pr.number = 42
        mock_pr.title = "Add new feature"
        mock_pr.html_url = "https://github.com/user/repo/pull/42"
        mock_pr.state = "open"
        mock_pr.head_ref = "feature"
        mock_pr.base_ref = "main"
        mock_pr.draft = False

        mock_create.return_value = mock_pr

        result = await github_tool.execute(
            operation="create_pr",
            owner="user",
            repo="repo",
            title="Add new feature",
            head="feature",
            base="main",
            body="This adds a cool feature",
        )

        assert result.success is True
        assert result.output["number"] == 42
        assert result.output["title"] == "Add new feature"
        assert result.output["head_ref"] == "feature"
        assert result.output["base_ref"] == "main"
        assert result.output["draft"] is False
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_github_tool_create_pr_missing_title(github_tool):
    """Test GitHubTool create_pr operation - missing title."""
    result = await github_tool.execute(
        operation="create_pr",
        owner="user",
        repo="repo",
        head="feature",
        base="main",
    )

    assert result.success is False
    assert "title parameter required" in result.error.lower()


@pytest.mark.asyncio
async def test_github_tool_create_pr_missing_head(github_tool):
    """Test GitHubTool create_pr operation - missing head branch."""
    result = await github_tool.execute(
        operation="create_pr",
        owner="user",
        repo="repo",
        title="Test PR",
        base="main",
    )

    assert result.success is False
    assert "head parameter required" in result.error.lower()


@pytest.mark.asyncio
async def test_github_tool_create_pr_missing_base(github_tool):
    """Test GitHubTool create_pr operation - missing base branch."""
    result = await github_tool.execute(
        operation="create_pr",
        owner="user",
        repo="repo",
        title="Test PR",
        head="feature",
    )

    assert result.success is False
    assert "base parameter required" in result.error.lower()


@pytest.mark.asyncio
async def test_github_tool_create_pr_draft(github_tool):
    """Test GitHubTool create_pr operation - draft PR."""
    with patch.object(GitHubClient, "create_pull_request") as mock_create:
        mock_pr = Mock()
        mock_pr.number = 99
        mock_pr.title = "WIP: Draft feature"
        mock_pr.html_url = "https://github.com/user/repo/pull/99"
        mock_pr.state = "open"
        mock_pr.head_ref = "draft-feature"
        mock_pr.base_ref = "develop"
        mock_pr.draft = True

        mock_create.return_value = mock_pr

        result = await github_tool.execute(
            operation="create_pr",
            owner="user",
            repo="repo",
            title="WIP: Draft feature",
            head="draft-feature",
            base="develop",
            draft=True,
        )

        assert result.success is True
        assert result.output["draft"] is True
        assert result.output["number"] == 99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
