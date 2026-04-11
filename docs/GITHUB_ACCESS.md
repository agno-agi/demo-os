# Giving Coda Access to GitHub

Coda needs a GitHub token to clone repos, read issues/PRs, push branches, and open PRs. Without this, most of Coda's capabilities won't work.

## Step 1: Create a Fine-Grained Personal Access Token

Go to [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens) and click **Generate new token**.

Do **not** use a Classic PAT -- those grant broad access to everything on your account. Use the newer Fine-grained token.

Fill in the basics:

| Field | Value |
|-------|-------|
| Token name | `coda` (or any name you'll recognize) |
| Expiration | 90 days (or longer) |
| Resource owner | Your personal account or your org |

## Step 2: Select Repositories

Under **Repository access**, choose **Only select repositories** and pick every repo you want Coda to work on.

Coda can only see and interact with repos you explicitly grant here. If you add a repo to `repos.yaml` but don't include it in the token, Coda won't be able to clone it, read its issues, or push code.

## Step 3: Set Permissions

Click **Repository permissions** and set these four:

| Permission | Access | What breaks without it |
|------------|--------|------------------------|
| **Contents** | Read and write | Can't clone repos or push `coda/*` branches |
| **Pull requests** | Read and write | Can't review PRs or create new ones |
| **Issues** | Read and write | Can't read issues for triage or post comments |
| **Metadata** | Read-only (required) | Can't list repos or make any API calls |

All four are required. If any are missing, Coda will fail silently or return permission errors when trying to use the affected feature.

## Step 4: Generate and Save

Click **Generate token**. GitHub only shows the token once -- copy it immediately.

Add it to your `.env` file:

```
GITHUB_TOKEN=github_pat_***
```

No quotes needed. Then restart the container:

```bash
docker compose up -d
```

> **Note:** AgentOS accepts either `GITHUB_TOKEN` or `GITHUB_ACCESS_TOKEN` as the environment variable name. Both work.

## Troubleshooting

**"Permission to repo.git denied" or 403 errors:**
- The token doesn't have **Contents: Read and write** for that repo
- Or the repo isn't in the token's "Only select repositories" list

**"Resource not accessible by personal access token":**
- The token is missing **Pull requests: Read and write** (for PR operations)
- Or missing **Issues: Read and write** (for issue operations)

**Coda can read but can't push or create PRs:**
- Permissions are set to Read-only instead of Read and write
- Check the token settings and update to Read and write

**Token expired:**
1. Generate a new one with the same settings
2. Update `.env` with the new value
3. Restart: `docker compose up -d`

## How It Works

Coda's `GithubTools` (from the Agno framework) use the token to authenticate GitHub API calls. The token is read from the environment at startup and never exposed to the agent's instructions or output.

- Coda uses `git clone https://github.com/...` (not SSH, not token-in-URL)
- All code work happens in isolated `coda/*` branches via git worktrees -- Coda never commits to main
- The token is injected at the application layer, not in agent instructions
