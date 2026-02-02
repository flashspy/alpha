# GitHub Integration User Guide

**Alpha v1.1 - Phase 11.1 Feature**

---

## Overview

The GitHub Integration feature enables Alpha to interact directly with GitHub repositories, issues, pull requests, and commits through natural language commands or explicit tool calls. This integration eliminates context switching and allows you to manage GitHub workflows directly from Alpha's command line.

---

## Features

✅ **Repository Management**
- List your repositories with filters
- Get detailed repository information
- View repository metadata (stars, forks, language)

✅ **Issue Tracking**
- List issues with state and label filters
- View detailed issue information
- Create new issues
- Add comments to existing issues

✅ **Pull Request Management**
- List pull requests by state
- View PR details and merge status
- Check PR mergability and CI status

✅ **Commit History**
- Browse commit history
- View detailed commit information
- Track changes across branches

✅ **Smart Features**
- Automatic rate limit handling
- Response caching for performance
- Retry logic for failed requests
- Natural language command support

---

## Setup

### 1. Get GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name: "Alpha GitHub Integration"
4. Select scopes:
   - `repo` (full control of private repositories)
   - `read:org` (optional, for organization access)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### 2. Configure Environment Variable

Add your token to your environment:

```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN="your_token_here"

# Or set temporarily for current session
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### 3. Verify Setup

Start Alpha and verify the GitHub tool is available:

```bash
alpha> tools

Available tools:
- github: Interact with GitHub repositories, issues, PRs, and commits
- ...
```

---

## Usage

### Repository Operations

#### List Your Repositories

```bash
# List all your repositories
alpha> Show me my GitHub repositories

# List repositories for a specific user
alpha> List repositories for torvalds

# Using explicit tool call
alpha> github list_repos
```

#### Get Repository Information

```bash
# Natural language
alpha> Tell me about the repository torvalds/linux

# Explicit call
alpha> github get_repo owner=torvalds repo=linux
```

**Output includes:**
- Repository name and description
- Stars, forks, watchers count
- Primary language
- Open issues count
- Clone URLs (HTTPS and SSH)
- Creation and update timestamps

---

### Issue Management

#### List Issues

```bash
# List open issues
alpha> Show me open issues in facebook/react

# List all issues (open and closed)
alpha> List all issues for microsoft/vscode

# Filter by labels
alpha> github list_issues owner=facebook repo=react labels=bug,help-wanted state=open
```

#### View Issue Details

```bash
# Natural language
alpha> Show me issue #123 from facebook/react

# Explicit call
alpha> github get_issue owner=facebook repo=react number=123
```

**Output includes:**
- Issue title and body
- Author and assignees
- Labels and milestone
- Comment count
- Creation and update timestamps
- Current state (open/closed)

#### Create New Issue

```bash
# Using natural language
alpha> Create an issue in myuser/myrepo titled "Bug: Login fails" with description "Users cannot log in after update"

# Explicit call
alpha> github create_issue owner=myuser repo=myrepo title="Bug: Login fails" body="Users cannot log in after update" labels=bug,high-priority
```

#### Add Comment to Issue

```bash
# Natural language
alpha> Add comment to issue #5 in myuser/myrepo: "Working on a fix now"

# Explicit call
alpha> github add_comment owner=myuser repo=myrepo number=5 body="Working on a fix now"
```

---

### Pull Request Management

#### List Pull Requests

```bash
# List open PRs
alpha> Show me open pull requests for microsoft/vscode

# List all PRs
alpha> github list_prs owner=facebook repo=react state=all

# Sort by recently updated
alpha> github list_prs owner=django repo=django sort=updated direction=desc
```

#### View Pull Request Details

```bash
# Natural language
alpha> Tell me about PR #456 from facebook/react

# Explicit call
alpha> github get_pr owner=facebook repo=react number=456
```

**Output includes:**
- PR title, body, and author
- Source and target branches
- Merge status (mergeable, conflicts, checks)
- Draft/ready status
- Commits, additions, deletions
- Changed files count
- Labels and assignees

---

### Commit Operations

#### List Commits

```bash
# List recent commits
alpha> Show me recent commits for torvalds/linux

# List commits for specific branch
alpha> github list_commits owner=myuser repo=myrepo sha=develop

# Limit number of pages
alpha> github list_commits owner=facebook repo=react max_pages=2
```

#### View Commit Details

```bash
# Natural language
alpha> Show me commit abc123 from torvalds/linux

# Explicit call
alpha> github get_commit owner=torvalds repo=linux sha=abc123def456
```

**Output includes:**
- Full commit SHA
- Commit message
- Author and committer information
- Timestamp
- Parent commits
- GitHub URL

---

### Utility Operations

#### Check Rate Limit

```bash
alpha> github rate_limit
```

**Output:**
- API calls limit (usually 5000/hour)
- Remaining calls
- Reset time (Unix timestamp)
- Calls used

---

## Advanced Usage

### Automation Examples

#### Monitor Issue Activity

```bash
# Create a scheduled task to check new issues daily
alpha> Schedule a task to run daily at 9am: "List open issues in myuser/myrepo and notify me if there are more than 10"
```

#### Automated PR Review Reminders

```bash
# Get notified about PRs needing review
alpha> Check for open PRs in myuser/myrepo and remind me if any have been waiting more than 2 days
```

---

## API Rate Limits

GitHub API has rate limits:

- **Authenticated requests**: 5,000 requests/hour
- **Search API**: 30 requests/minute

Alpha automatically handles rate limiting:

- **Buffer reserve**: Keeps 100 API calls in reserve
- **Automatic retry**: Retries failed requests with backoff
- **Cache**: Caches responses for 5 minutes to reduce API calls
- **Rate limit errors**: Shows clear error message with reset time

**Check remaining quota:**
```bash
alpha> github rate_limit
```

---

## Troubleshooting

### "Authentication failed" Error

**Cause**: Invalid or missing GitHub token

**Solution**:
1. Verify `GITHUB_TOKEN` is set: `echo $GITHUB_TOKEN`
2. Check token has not expired
3. Generate new token if needed
4. Restart Alpha after setting token

### "Resource not found" Error

**Cause**: Repository, issue, or PR doesn't exist or you don't have access

**Solution**:
1. Check spelling of owner/repo names
2. Verify issue/PR number is correct
3. Ensure you have access to private repositories (token scope)

### "Rate limit exceeded" Error

**Cause**: Too many API requests in short time

**Solution**:
1. Wait for rate limit reset (shown in error message)
2. Use caching (default enabled)
3. Reduce frequency of requests
4. Check rate limit status: `alpha> github rate_limit`

### "Insufficient permissions" Error

**Cause**: Token doesn't have required scopes

**Solution**:
1. Go to token settings on GitHub
2. Add required scopes (`repo` for private repos)
3. Regenerate token
4. Update `GITHUB_TOKEN` environment variable

---

## Security Best Practices

✅ **Token Storage**
- Store token in environment variable, never in code
- Use `~/.bashrc` or `~/.zshrc` for persistent storage
- Never commit token to version control

✅ **Token Permissions**
- Grant minimum required scopes
- Use fine-grained tokens for better security
- Regularly rotate tokens

✅ **Access Control**
- Keep token private and secure
- Revoke tokens immediately if compromised
- Review token usage regularly on GitHub

---

## Examples & Use Cases

### Developer Workflow

```bash
# Morning routine: Check your repositories
alpha> List my repositories sorted by recently updated

# Check open issues
alpha> Show me open issues in myuser/myproject

# Review PRs needing attention
alpha> List open pull requests for myuser/myproject

# Create issue for bug found
alpha> Create issue in myuser/myproject: "Bug in login form" body="Email validation not working"
```

### Open Source Contribution

```bash
# Find interesting projects
alpha> Get repository info for facebook/react

# Check open issues to contribute
alpha> List issues for facebook/react labels=good-first-issue state=open

# View specific issue details
alpha> Show me issue #12345 from facebook/react
```

### Project Management

```bash
# Daily standup: Review team activity
alpha> List commits for myorg/project

# Check sprint progress
alpha> List issues for myorg/project milestone=v2.0 state=open

# Monitor PR review queue
alpha> List PRs for myorg/project state=open sort=created direction=asc
```

---

## Limitations

⚠️ **Current Limitations** (Phase 11.1):
- No PR creation or merging (view only)
- No issue editing (create and comment only)
- No branch operations
- No webhooks or real-time notifications
- No GitHub Actions integration

**Coming in Phase 11.2**:
- Full PR management (create, merge, review)
- Issue editing and closing
- Branch management
- Webhook support for real-time updates
- GitHub Actions integration

---

## FAQ

**Q: Do I need a paid GitHub account?**
A: No, the free GitHub account provides 5,000 API requests/hour, which is sufficient for most use cases.

**Q: Can I use this with GitHub Enterprise?**
A: Yes, set the `base_url` parameter when creating the client: `GitHubClient(base_url="https://github.company.com/api/v3")`

**Q: Is my data private?**
A: Yes, all GitHub operations use your personal token. Alpha doesn't store or share your GitHub data.

**Q: Can I automate issue creation from errors?**
A: Yes! Alpha's proactive intelligence can suggest creating issues when it detects errors or failures.

**Q: How do I access private repositories?**
A: Ensure your token has the `repo` scope, which grants access to private repositories.

---

## Related Documentation

- [Alpha Features Guide](../features.md)
- [Tool Usage Guide](../../TOOL_USAGE_GUIDE.md)
- [Task Scheduling](../daemon_mode.md)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

**Version**: 1.1 (Phase 11.1)
**Last Updated**: 2026-02-03
**Status**: Production Ready ✅
