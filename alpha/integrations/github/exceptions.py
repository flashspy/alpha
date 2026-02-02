"""
GitHub Integration Exception Classes

Custom exception hierarchy for GitHub API errors.
"""


class GitHubError(Exception):
    """Base exception for all GitHub integration errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class GitHubAuthenticationError(GitHubError):
    """Raised when authentication fails (invalid token, expired, insufficient permissions)."""

    def __init__(self, message: str = "GitHub authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class GitHubRateLimitError(GitHubError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        reset_time: int = None,
        **kwargs,
    ):
        self.reset_time = reset_time
        super().__init__(message, **kwargs)


class GitHubNotFoundError(GitHubError):
    """Raised when requested resource is not found (404)."""

    def __init__(
        self, message: str = "GitHub resource not found", **kwargs
    ):
        super().__init__(message, **kwargs)
        self.status_code = 404


class GitHubPermissionError(GitHubError):
    """Raised when user lacks permission for requested operation (403)."""

    def __init__(
        self,
        message: str = "Insufficient permissions for GitHub operation",
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.status_code = 403


class GitHubValidationError(GitHubError):
    """Raised when request validation fails (422)."""

    def __init__(
        self, message: str = "GitHub request validation failed", **kwargs
    ):
        super().__init__(message, **kwargs)
        self.status_code = 422


class GitHubNetworkError(GitHubError):
    """Raised when network request fails (timeout, connection error)."""

    def __init__(
        self, message: str = "GitHub network request failed", **kwargs
    ):
        super().__init__(message, **kwargs)
